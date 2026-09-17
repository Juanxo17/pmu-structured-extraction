# Deuda técnica

Registro de puntos identificados en revisiones de PR que se aceptan conscientemente para este prototipo, en vez de bloquear el merge. Cada entrada indica de qué PR sale, por qué no se resuelve ahora y qué revisar cuando se retome.

## Regex de teléfono no anclado al inicio del patrón

- **Origen:** PR #37 (`feat: modulo de anonimizacion de datos personales`)
- **Dónde:** `backend/process/process/anonimizacion.py`, `_REGEX_TELEFONO`
- **Problema:** el patrón `(?:\+?57\s?)?(?:3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}|\d{7})\b` solo tiene `\b` al final, no al inicio. Puede matchear los últimos 7 dígitos de una secuencia numérica más larga que no es un teléfono (número de radicado, cédula, fecha compacta), enmascarando parcialmente un dato que no es PII.
- **Por qué se deja así:** no hay evidencia todavía de que aparezca en el corpus real; agregar el ancla y su test es de bajo esfuerzo pero no es urgente para el prototipo.
- **Qué revisar después:** agregar `\b` (o lookbehind de no-dígito) al inicio del patrón, con un test que cubra una secuencia numérica larga que no sea teléfono (ej. un número de radicado).

## `httpx` y `httpx2` mezclados en el mismo workspace

- **Origen:** PR #38 (`feat: orquestador del pipeline de dos etapas`)
- **Dónde:** `pyproject.toml` (raíz, dependencia de desarrollo `httpx2`) vs. `backend/process/process/orquestador.py` (usa `httpx` en producción)
- **Problema:** `httpx2` es el fork oficial que Pydantic Services Inc. mantiene de `httpx` desde 2026 (no es un paquete falso, se verificó). Se agregó solo como dependencia de desarrollo para eliminar un `DeprecationWarning` de `TestClient`. Resultado: el cliente HTTP que ejercitan las pruebas (`httpx2`, vía `TestClient`) es distinto del que corre en producción (`httpx`, en `orquestador.py`), lo que reduce la fidelidad de las pruebas frente a cualquier diferencia de comportamiento entre ambas librerías.
- **Por qué se deja así:** migrar todo el proyecto a `httpx2` es una decisión de equipo (afecta a los 5 servicios), no algo que decida un solo PR de Process.
- **Qué revisar después:** decidir en equipo si el proyecto migra completo a `httpx2` (dado que `httpx` original entra en mantenimiento reducido) o si se revierte `httpx2` y se acepta el warning de `TestClient` mientras tanto.

## Sin manejo de errores de servicios downstream en el orquestador

- **Origen:** PR #38 (`feat: orquestador del pipeline de dos etapas`)
- **Dónde:** `backend/process/process/orquestador.py` (`_llamar_compuerta`, `_llamar_geo`, `_persistir_reporte`)
- **Problema:** si Inference, Geo o CRUD fallan (caído, 5xx, timeout), la excepción de `httpx` se propaga sin capturar y `POST /procesar` responde 500 genérico a BFF. Si el fallo ocurre en Geo o CRUD, el mensaje ya incurrió el costo de las llamadas a Inference (compuerta + extracción) y se pierde sin registro ni reintento.
- **Por qué se deja así:** aceptable para este prototipo, donde los tres servicios corren en el mismo entorno de desarrollo y los fallos de red no son el caso común todavía.
- **Qué revisar después:** definir una estrategia de reintento/registro de fallos antes de cualquier despliegue con tráfico real (ej. persistir el mensaje descartado por fallo técnico en vez de perderlo silenciosamente).

## Condición de carrera en el chequeo de duplicado de `POST /mensajes`

- **Origen:** PR #39 (`feat: endpoints de BFF - POST /mensajes y proxy hacia CRUD`)
- **Dónde:** `backend/bff/bff/main.py`, `_existe_duplicado`
- **Problema:** `_existe_duplicado` consulta a CRUD antes de que el mensaje se persista (la persistencia ocurre después, dentro de Process, de forma asíncrona). Dos peticiones `POST /mensajes` con la misma `fuente`+`id_externo` llegando casi al mismo tiempo (ej. un reintento de Telegram) pueden pasar ambas el chequeo porque ninguna se ha persistido todavía, y ambas disparan Process — duplicado real, no solo teórico.
- **Por qué se deja así:** el caso de dos peticiones concurrentes con el mismo `id_externo` es poco frecuente en este prototipo (un solo consumidor de Telegram); no bloquea el merge.
- **Qué revisar después:** mover el chequeo de idempotencia a algo atómico (ej. constraint único en CRUD sobre `fuente`+`id_externo` que rechace el segundo insert) en vez de depender de un check-then-act desde BFF.

## Fallo silencioso del disparo fire-and-forget a Process

- **Origen:** PR #39 (`feat: endpoints de BFF - POST /mensajes y proxy hacia CRUD`)
- **Dónde:** `backend/bff/bff/main.py`, `_disparar_procesamiento`
- **Problema:** no tiene manejo de errores. Si la llamada a `POST /procesar` falla (Process se cae justo después del chequeo de salud, timeout, etc.), no hay log estructurado ni forma de saber que un mensaje se perdió — el cliente ya recibió su `202`.
- **Por qué se deja así:** aceptable para este prototipo; el patrón fire-and-forget es intencional para no bloquear la respuesta al cliente.
- **Qué revisar después:** agregar al menos un log explícito del fallo (con el `id_externo` del mensaje perdido) antes de cualquier despliegue con tráfico real.

## Proxies de BFF asumen que CRUD siempre devuelve JSON

- **Origen:** PR #39 (`feat: endpoints de BFF - POST /mensajes y proxy hacia CRUD`)
- **Dónde:** `backend/bff/bff/main.py`, `_reenviar_get` / `_reenviar_patch`
- **Problema:** si CRUD cae y devuelve un cuerpo no-JSON (error de servidor, HTML, vacío), `respuesta.json()` lanza sin capturar y BFF responde con un 500 genérico en vez de algo más informativo.
- **Por qué se deja así:** no bloquea el prototipo; es un caso de borde de infraestructura, no de lógica de negocio.
- **Qué revisar después:** capturar el error de parseo y responder un 502/503 explícito indicando que CRUD no está respondiendo correctamente.

## Desempate de barrios ambiguos no es realmente determinista

- **Origen:** PR #45 (`feat: servicio Geo - resolver determinista con gazetteer del IDESC y respaldo Nominatim`)
- **Dónde:** `backend/geo/geo/geocodificador.py`, `Geocodificador._elegir_barrio`
- **Problema:** `nombre = max(nombres, key=len)` opera sobre `nombres = {barrio.nombre for barrio in barrios}`, un `set` de strings. Cuando dos nombres de barrio *distintos* empatan en longitud y ambos aparecen en el mismo texto, cuál gana depende del orden de iteración del `set`, sujeto al hash aleatorizado por proceso de Python (`PYTHONHASHSEED` no fijado) — el mismo texto podría resolver a un barrio distinto entre un reinicio del servicio y otro. Contradice el objetivo de determinismo que el propio PR destaca como diseño central. Ningún test cubre un empate real de longitud.
- **Por qué se deja así:** tráfico bajo esperado para este prototipo; la probabilidad de que dos nombres de barrio de igual longitud aparezcan juntos en el mismo texto es baja.
- **Qué revisar después:** ordenar de forma determinista antes de elegir (ej. `sorted(nombres, key=lambda n: (-len(n), n))[0]`, o fijar `PYTHONHASHSEED` del proceso), con un test que fuerce un empate real de longitud.

## Inicialización no perezosa del gazetteer y el resolutor externo en Geo

- **Origen:** PR #45 (`feat: servicio Geo - resolver determinista con gazetteer del IDESC y respaldo Nominatim`)
- **Dónde:** `backend/geo/geo/main.py` (`_gazetteer_inicial`, `_externo_inicial` a nivel de módulo)
- **Problema:** `Gazetteer()` (que abre y parsea `gazetteer.json`, 57 KB) se instancia al importar `geo.main`, no en el primer uso — inconsistente con el patrón de inicialización perezosa que el mismo autor estableció en CRUD (PR #44) específicamente para no tocar el sistema de archivos al importar en Windows.
- **Por qué se deja así:** el archivo es de solo lectura (a diferencia de la base de datos de CRUD, que sí se bloquea al escribir), así que el riesgo práctico es menor.
- **Qué revisar después:** mover la construcción de `_gazetteer_inicial`/`_externo_inicial` a una función lazy, igual que `FabricaSesiones` en CRUD, si en algún momento da problemas al importar en algún entorno.

## `NominatimResolver` crea un cliente nuevo en cada llamada

- **Origen:** PR #45 (`feat: servicio Geo - resolver determinista con gazetteer del IDESC y respaldo Nominatim`)
- **Dónde:** `backend/geo/geo/nominatim.py`, `NominatimResolver._geocodificar_sin_limite`
- **Problema:** cada llamada construye un `Nominatim(user_agent=self._user_agent)` nuevo en vez de reutilizar un cliente — no es incorrecto, solo innecesariamente costoso.
- **Por qué se deja así:** el `RateLimiter` (mínimo 1s entre llamadas) y el cache en memoria ya limitan cuántas veces se ejecuta esto en la práctica; el costo extra de crear el cliente es marginal frente a la llamada de red.
- **Qué revisar después:** reutilizar una sola instancia de `Nominatim` como atributo de `NominatimResolver`, creada una vez en `__init__`.

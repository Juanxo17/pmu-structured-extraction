# Protocolo de anotación del corpus — SIRENA

Versión: **1.0** · Estado: propuesta para validación del equipo · Frente A (Datos y Evaluación)

Este documento define las reglas operativas para anotar los mensajes del corpus de SIRENA
y producir el *gold standard* v1. Complementa el contrato de datos de `docs/CONTRATOS_SISTEMA.md`
y el vocabulario de `config/ontologia.yaml`. Todo aporte a este documento se integra por
Pull Request y requiere validación explícita del equipo antes de anotar la primera partida.

---

## 1. Objeto de la anotación

Cada línea del corpus es un **mensaje ciudadano** en español coloquial, frecuentemente
regionales de Cali (jerga, tipeos, toponimia informal). El anotador traduce ese mensaje al
esquema de tres capas definido en `common/sirena-schema/sirena_schema/schema.py`:

1. **Compuerta** (`Compuerta`) — obligatoria en todo mensaje.
2. **Naturaleza** (`Naturaleza`) — solo si el mensaje es *accionable*; en caso contrario es `null`.
3. **Ubicación** (`Ubicacion`) — solo si el mensaje es *accionable*; puede quedar *indeterminada*
   si el mensaje no da pistas geográficas.

Regla de oro: **el anotador nunca inventa información.** Si el mensaje no permite defender un
valor, se usa el valor *menos preciso pero defensible* (compuerta `false` para lo no accionable,
`nivel_granularidad: "indeterminada"` y coordenadas nulas para lo irresoluble, etc.).

---

## 2. Formato del archivo

Formato **JSONL** (una línea por mensaje), codificación UTF-8. Cada línea tiene el siguiente
esquema (objetos del esquema Pydantic v2 ya validados):

```json
{
  "texto": "Hay un incendio en el cerro, cerca a la 26, está saliendo humo negro.",
  "compuerta": {
    "es_reporte_accionable": true,
    "temporalidad": "ocurriendo_ahora",
    "intencion": "reporta_terceros"
  },
  "naturaleza": {
    "tipo_evento": "incendio_cobertura_vegetal",
    "servicio_de_respuesta": ["B"]
  },
  "ubicacion": {
    "ubicacion_texto_literal": "el cerro, cerca a la 26",
    "barrio": null,
    "comuna": "2",
    "punto_referencia": null,
    "nivel_granularidad": "comuna",
    "lat": null,
    "lon": null
  }
}
```

Reglas de forma:

- `texto` se copia **literal**, sin corregir ortografía, abreviaturas ni mayúsculas.
- Para mensajes **no accionables** (`es_reporte_accionable: false`), `naturaleza` y `ubicacion`
  se omiten o van en `null`; solo se anotan `texto` y `compuerta`.
- El anotador entrega además un archivo `.tsv` de hoja de ruta por cada partida (ver §7) para
  la revisión cruzada y el cálculo de concordancia.

---

## 3. Capa 1 — Compuerta

### 3.1 `es_reporte_accionable` (bool)

`true` si el mensaje describe un hecho que **requiere o requerirá la intervención de un servicio
de respuesta** de la ERE, o una ayuda de la comunidad, en un horizonte operativo (ahora o en el
futuro previsible). `false` si es ruido, noticia pasada sin acción, pregunta administrativa
general, reclamo sin petición concreta, o contenido sin relación con emergencias.

Modos típicos de `false`:

- Noticia de un hecho ya atendido/resuelto narrada como anécdota (`referencia_noticia`).
- Pregunta general ("¿a qué hora funcionan los Bomberos?").
- Publicidad, memes, chismes, temas políticos sin vínculo con un evento.
- "Estuvieron haciendo control" → sin necesidad actual.

### 3.2 `temporalidad`

| Valor | Definición operativa | Ejemplo |
|---|---|---|
| `ocurriendo_ahora` | El hecho está sucediendo o acaba de iniciar; el lenguaje indica presente/inmediatez (presente, gerundio, "ahora", "acaba de"). | "están quemando llantas en la vía Panamericana" |
| `ya_ocurrio` | El hecho ocurrió y las consecuencias persisten o se reporta el hecho pasado con necesidad de atención. | "anoche se inundó mi casa y aún está el agua" |
| `riesgo_previsto` | Hay peligro o amenaza inminente y *previ-sible*, con lenguaje de futuro o condición. | "el tanque se puede caer, no está asegurado y hay niños" |
| `referencia_noticia` | Mención de un hecho sin necesidad operativa actual; se narra como suceso conocido. | "pues que ayer cayó un árbol en el norte, no sé, así dijeron" |

Desempate: si hay presente + consecuencias pasadas, manda **`ocurriendo_ahora`** (lo que el
ciudadano reporta como vigente). El futuro/condición marca `riesgo_previsto` solo si hay amenaza,
no mera especulación sin peligro concreto (esa pasa a `false` en accionabilidad).

### 3.3 `intencion`

| Valor | Definición operativa |
|---|---|
| `solicita_ayuda` | El autor pide intervención directa para sí o para la comunidad en primera persona ("ayúdeme", "necesito que vengan", "manden a alguien"). |
| `reporta_terceros` | El autor informa un hecho que afecta a otros; no pide en primera persona pero el hecho es accionable. |
| `ofrece_ayuda` | El autor ofrece recursos/ayuda (voluntariado, logística, un lugar). |
| `solicita_informacion` | El autor pide datos o estado (¿dónde queda, cómo está el servicio?). |

Desempate: `solicita_ayuda` y `reporta_terceros` son los dos modos *accionables* habituales;
`ofrece_ayuda` normalmente es accionable solo si el mensaje permite conectar la oferta con un
evento vigente (si no, `false`). `solicita_informacion` suele ser **no accionable** salvo que la
información pedida sea operativa para un evento en curso.

---

## 4. Capa 2 — Naturaleza (solo accionables)

### 4.1 `tipo_evento`

Debe ser **exactamente** uno de los valores de `config/ontologia.yaml` (sección `tipo_evento`).
Los valores vigentes se leen del archivo; este protocolo no los repite para no desincronizarse.

Reglas:

- El valor se elige por lo que **el mensaje describe**, no por el servicio que se imagina.
- Si el mensaje describe más de un tipo (multi-intención, ver §6), se anota el **primario**:
  el evento más urgente o el primero explícito.
- Si es accionable pero ningún valor encaja con claridad, se elige el **más defendible** y se
  marca el ejemplo en la hoja de ruta como caso borde para revisión.

### 4.2 `servicio_de_respuesta` (lista)

Subconjunto de los **códigos** A–R de la Tabla 8 de la ERE (ver `config/ontologia.yaml`),
excluidos **P** y **Q** (funciones institucionales, no reportables). Puede ser una lista de
varios códigos si el evento convoca varios servicios (ej. un incendio estructural con rescate
→ `["B", "A"]`). Se anotan sin duplicados.

---

## 5. Capa 3 — Ubicación (solo accionables)

### 5.1 Campos

| Campo | Regla |
|---|---|
| `ubicacion_texto_literal` | Transcripción literal del fragmento del mensaje que da ubicación (no la oración completa si no aporta). Ej.: "el cerro, cerca a la 26". |
| `barrio` | Nombre normalizado de barrio de Cali (CNPV 2018) **solo si el mensaje lo permite**; `null` si no. |
| `comuna` | Número de comuna (cadena, ej. `"2"`, `"17"`) **solo si se puede defender**; `null` si no. |
| `punto_referencia` | Monumento, hospital, parque, centro comercial, etc. nombrado literalmente; `null` si no. |
| `nivel_granularidad` | Véase §5.2. |
| `lat` / `lon` | Coordenadas decimales **solo si el gazetteer permite resolver a un punto**; en otro caso `null`. Nunca aproximadas a ojo. |

### 5.2 `nivel_granularidad` y qué se puede afirmar

| Nivel | Se anota cuando... | Coordenadas |
|---|---|---|
| `exacta` | El gazetteer resuelve coordenadas para la referencia (dirección, esquina, lugar puntual). | Sí, las del gazetteer |
| `barrio` | Solo se puede afirmar el barrio (se nombra el barrio, o un punto de referencia ubicado determinísticamente dentro de un barrio). | Sí si el gazetteer tiene punto para el barrio; si no, `null` |
| `comuna` | Solo se puede afirmar la comuna (se nombra la comuna o un barrio no catalogado pero asignable a comuna). | `null` |
| `ciudad` | Solo "Cali", "la ciudad", "el norte/sur de Cali". | `null` |
| `indeterminada` | No hay pista geográfica o es irresoluble. | `null` |

Regla de ambigüedad: **nunca se sube de granularidad por suposición**. Ante una referencia
ambigua se conserva el nivel más específico *defendible*; rutas populares ("cerca a la 26")
se anotan al nivel que el texto respalda (si "26" es una calle reconocida → `exacta` si el
gazetteer la tiene; si no, `barrio`/`comuna`/`indeterminada` según corresponda).

---

## 6. Multi-intención y ruido

- **Multi-intención**: un mensaje puede contener varias necesidades (ej. "se inundó mi casa y
  también hay un árbol caído en la cuadra"). Regla: el tipo de evento anotado es el **primario**
  (más urgente o primero explícito); `servicio_de_respuesta` puede recoger los servicios de
  todos los eventos mencionados.
- **Ruido no accionable**: mensajes de la categoría `false` se anotan completos en compuerta
  (temporalidad e intención aplican igual) y con resto `null`.
- **Saludos/varios temas**: se anota el contenido relevante a emergencias; si no hay ninguno,
  `false` + `referencia_noticia` o el valor que mejor describa la intención.

---

## 7. Proceso y revisión cruzada

1. **Partidas**: el corpus se divide en 4 partidas (~igual tamaño). Cada integrante anota la
   suya usando este protocolo y genera su JSONL en `eval-prompt/annotation/<autor>_partida.jsonl`.
2. **Submuestra del 20%**: se extrae una submuestra aleatoria fija (seed documentada) y cada
   mensaje de ella lo anota una **segunda persona** (revisión cruzada) en
   `eval-prompt/annotation/<revisor>_crosscheck.tsv`.
3. **Desempate**: para cada discrepancia en la submuestra, el responsable de Frente A resuelve
   con criterio de este protocolo, se documenta la resolución en
   `eval-prompt/annotation/resoluciones.md` y se actualiza el gold.
4. **Concordancia**: se calcula el porcentaje de acuerdo y el coeficiente Kappa de Cohen por
   campo sobre la submuestra y se reporta junto al gold congelado (T-09).
5. **Congelación**: la versión consolidada se guarda como v1:
   - `eval-prompt/corpus/gold/v1/dev.jsonl` (partición de desarrollo, 60 mensajes)
   - `eval-prompt/corpus/gold/v1/eval.jsonl` (partición de evaluación, 340 mensajes)

Cambios posteriores al freeze se gestionan como **v2**, nunca editando v1 en sitio.

---

## 8. Privacidad (Ley 1581 de 2012)

- La anotación se realiza sobre el texto **ya anonimizado** por el pipeline. El corpus sintético
  no contiene PII; si al anotar un mensaje se detectaran nombres, teléfonos, direcciones
  personales u otros datos personales, se registra en la hoja de ruta y **no se transcribe
  el dato**, se sustituye por `[PII]`.
- Ningún archivo de anotación incluye datos personales reales de ciudadanos ni del equipo.

---

## 9. Casos borde frecuentes (guía rápida de consulta)

| Caso | Resolución |
|---|---|
| "¿Alguien sabe si sigue la vía cerrada?" | `solicita_informacion`; si no hay evento vigente → `false`; si hay evento vigente accionable → `true`, temporalidad del evento. |
| "Regalé unos zapatos que quedaron de la inundación" | `ofrece_ayuda`; sin nexo con evento vigente → `false`. |
| "Ya pasó, gracias a Dios" sin pedir nada | `false` + `referencia_noticia`. |
| "Hay un hueco en la ciclovía" | Depende de si afecta seguridad: hueco grande con riesgo → accionable (riesgo_previsto); menor → `false`. Anotar lo que el texto permita defender. |
| Mensaje solo con "alguien que colabore" sin evento | `false` + `reporta_terceros` (o `solicita_informacion` si pide dato). |
| Ubicación "en el callejón de la Y / gaseosas Lux" | `punto_referencia` = "Y" o "gaseosas Lux"; granularidad según gazetteer (`exacta` si resuelve, si no `barrio`). |

---

## 10. Validación del protocolo (AC 2 de T-04)

Para que el protocolo quede **validado por el equipo** se solicita a cada integrante revisar
este documento y aprobar (con reply en la PR) o proponer cambios. Con ≥2 aprobaciones y la
firma del responsable de Frente A, el protocolo queda vigente y da inicio a la anotación (T-08).
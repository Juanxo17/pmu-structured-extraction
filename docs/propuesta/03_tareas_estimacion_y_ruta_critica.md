# 3. Desglose de Tareas, Estimación y Ruta Crítica

> **Proyecto:** SIRENA — *Sistema de Interpretación de Reportes de Emergencia y Necesidades Automatizado*
> **Documento:** Insumo para el capítulo 3 de la Propuesta (Cronograma y Ruta Crítica)
> **Universidad Autónoma de Occidente**

> **Alcance de este documento.** Contiene el desglose de trabajo (WBS), la estimación de esfuerzo, las dependencias entre tareas, los frentes paralelizables y el análisis de ruta crítica. **No contiene calendario ni diagrama de Gantt**: la asignación de fechas es una decisión del equipo y se construye a partir de las dependencias aquí declaradas.

---

## 3.1 Convenciones de estimación

Se aplica la regla establecida para el curso:

- **Escala:** serie de Fibonacci — 1, 2, 3, 5, 8, 13.
- **Equivalencia:** **1 Story Point = 1 día de trabajo de una persona** (día-persona).
- Ninguna tarea supera los 5 SP: toda estimación mayor se subdividió, conforme a la regla de que una tarea por encima de 13 debe partirse.

### Distinción crítica: esfuerzo ≠ duración

Un Story Point mide **esfuerzo** (día-persona), no **tiempo transcurrido**. Para una tarea paralelizable entre *n* personas:

```
duración ≈ esfuerzo / n
```

Pero esta división **no aplica a todas las tareas**. Se distinguen dos tipos:

| Tipo | Comportamiento | Ejemplo en el proyecto |
|---|---|---|
| **Divisible** | Añadir personas reduce la duración proporcionalmente | Anotación del corpus (T-08): 400 mensajes se reparten entre 4 |
| **Indivisible** | Añadir personas no reduce la duración; puede aumentarla por costo de coordinación | Diseño del esquema (T-02), iteración del prompt (T-15) |

Las tareas indivisibles se marcan con **⛔ND** (no divisible) y son las que determinan la duración mínima del proyecto, independientemente del tamaño del equipo.

---

## 3.2 Desglose de trabajo (WBS)

**31 tareas · 64 Story Points totales**

### Fase 0 — Fundación *(habilita todo lo demás)*

| ID | Tarea | SP | Depende de | Módulo | OE |
|---|---|---|---|---|---|
| **T-01** | Inicializar repositorio: estructura de carpetas, gestor de dependencias, `.gitignore`, plantilla de tickets, convención de ramas | 1 | — | Plataforma | Transversal |
| **T-02** ⛔ND | **Definir el esquema de salida de 3 capas y 10 campos** como modelos Pydantic v2 / JSON Schema: compuerta (accionable, temporalidad, intención), naturaleza (tipo de evento, servicio de respuesta multietiqueta) y ubicación descompuesta | 3 | — | M2 | Transversal |
| **T-03** | Codificar la ontología de dominio de emergencias en archivo de configuración YAML cargable: **servicios de respuesta de la ERE de Cali** (Decreto 1002 de 2023) y **tipos de evento** (escenarios de riesgo con protocolo especifico) como categorías operativas, con tabla de correspondencia hacia las clases HumAID para comparabilidad con la literatura | 1 | T-02 | M2 | OE1, OE2 |
| **T-04** | Redactar el protocolo de anotación: definiciones operativas de cada campo, casos límite, reglas de desempate | 1 | T-02 | Datos | OE5 |
| **T-05** | Crear cuentas y credenciales de proveedores (Groq, Bluesky/Telegram); prueba de conectividad y verificación de cuotas | 1 | — | Plataforma | Transversal |
| **T-06** | Obtener o construir el *gazetteer* de Cali: barrios, comunas, puntos de referencia; normalización de nombres | 2 | — | M3 | OE3 |

> **T-02 es la tarea más bloqueante del proyecto.** De ella dependen la anotación, el prompt, el validador, la persistencia y el tablero. Un cambio de esquema después de iniciada la anotación invalida trabajo ya realizado. Debe cerrarse con acuerdo de los cuatro integrantes antes de avanzar.

### Fase 1 — Datos

| ID | Tarea | SP | Depende de | Módulo | OE |
|---|---|---|---|---|---|
| **T-07** | Generar el corpus sintético crudo (~400 mensajes) en español coloquial caleño: variación de registro, errores de tipeo, toponimia informal, multi-intención, ruido no accionable | 2 | T-03, T-04 | Datos | OE2, OE5 |
| **T-08** | **Anotar manualmente el corpus** conforme al protocolo — tarea colectiva, repartida entre los 4 integrantes | 5 | T-07 | Datos | OE5 |
| **T-09** | Consolidar anotaciones, resolver discrepancias por revisión cruzada, congelar la versión 1 del *gold standard* | 1 | T-08 | Datos | OE5 |
| **T-10** | Implementar el módulo de anonimización de datos personales (nombres, teléfonos, direcciones) | 1 | T-02 | M1 | OE5 |

> **Sobre T-08:** cada integrante anota ~100 mensajes. Adicionalmente, una submuestra del 20 % se anota por duplicado para permitir la revisión cruzada de T-09. Es la tarea con mayor riesgo de subestimación: anotar bien es lento, y la calidad del corpus condiciona toda la evaluación posterior.

### Fase 2 — Núcleo de extracción

| ID | Tarea | SP | Depende de | Módulo | OE |
|---|---|---|---|---|---|
| **T-11** | Cliente de inferencia abstracto e independiente del proveedor: manejo de errores, reintentos con retroceso exponencial, control de límites de tasa | 2 | T-05 | M2 | Transversal |
| **T-12** | Construir los **dos prompts** versión 1 —compuerta y extracción—: instrucciones, esquema embebido y ejemplos *few-shot* en español coloquial | 2 | T-02, T-03 | M2 | OE1, OE2 |
| **T-13** | Validador de salidas y capa de reparación: reintento guiado ante JSON no conforme, registro de rechazos | 2 | T-02 | M2 | OE5 |
| **T-14** | Orquestador del pipeline **en dos etapas**: mensaje → anonimización → compuerta → (si accionable) extracción → validación → registro con su mensaje original | 2 | T-10, T-11, T-12, T-13 | M2 | OE1, OE2 |
| **T-15** ⛔ND | **Iteración de los prompts** sobre partición de desarrollo: ajuste de instrucciones y ejemplos en ambas etapas, análisis de fallos, control de versiones | 5 | T-09, T-14 | M2 | OE1, OE2 |
| **T-16** ⛔ND | **Normalización geográfica determinista**: resolución de toponimia informal contra el *gazetteer*, niveles de granularidad, desambiguación, geocodificación | 5 | T-06, T-14 | M3 | OE3 |
| **T-17** | Detección básica de reportes duplicados | 1 | T-16 | M3 | OE1 |

### Fase 3 — Ingesta

| ID | Tarea | SP | Depende de | Módulo | OE |
|---|---|---|---|---|---|
| **T-18** | Interfaz `FuenteDeMensajes` e implementación `CSVReplaySource` (reproductor del corpus con marcas de tiempo) | 1 | T-02 | M1 | OE4 |
| **T-19** | Implementación de fuente en vivo: `BlueskySource` o `TelegramSource` | 2 | T-18 | M1 | OE4 |

### Fase 4 — Persistencia, servicio e interfaz

| ID | Tarea | SP | Depende de | Módulo | OE |
|---|---|---|---|---|---|
| **T-20** | Capa de persistencia: modelo de datos SQLite/SQLAlchemy derivado del esquema | 1 | T-02 | M4 | OE4 |
| **T-21** | API REST en FastAPI: endpoints de ingesta, procesamiento y consulta de reportes | 2 | T-20 | M4 | OE4 |
| **T-22** | Tablero Streamlit — vista principal: bandeja de reportes con **ordenamiento y filtros configurables por el operador** (por servicio de respuesta, tipo de evento, comuna, temporalidad e intención) | 3 | T-21 | M5 | OE4 |
| **T-23** | Tablero Streamlit — vista de detalle: mapa y **mensaje original completo junto al registro estructurado**, para contraste inmediato | 2 | T-22, T-16 | M5 | OE4 |

> **T-23 materializa la delimitación ética.** Mostrar el mensaje original junto al registro no es un adorno de interfaz: es el mecanismo por el cual el operador verifica cada campo contra su fuente antes de actuar.

### Fase 5 — Evaluación

| ID | Tarea | SP | Depende de | Módulo | OE |
|---|---|---|---|---|---|
| **T-24** | Marco de evaluación: comparación automatizada contra el *gold standard*, desempeño por campo, matrices de confusión, medición de latencia | 2 | T-09, T-14 | Evaluación | OE5 |
| **T-25** | Corrida de evaluación con `Llama-3.1-8B-Instruct` y **análisis cualitativo de modos de error** | 2 | T-15, T-16, T-24 | Evaluación | OE5 |
| **T-26** | Corrida comparativa con `Llama-3.3-70B-Instruct` bajo idéntico prompt y corpus | 1 | T-25 | Evaluación | OE5 |
| **T-27** | Prueba de transferibilidad: construir ontología de dominio alterno (Seguridad y Convivencia), corpus reducido y corrida sin modificar código | 2 | T-25 | Evaluación | OE5 |

### Fase 6 — Empaquetado y cierre

| ID | Tarea | SP | Depende de | Módulo | OE |
|---|---|---|---|---|---|
| **T-28** | Contenedorización: `Dockerfile`, `docker-compose.yml`, verificación de despliegue en máquina limpia | 2 | T-21, T-22 | Plataforma | OE4 |
| **T-29** | Suite de pruebas con `pytest` sobre extracción, validación y normalización; integración continua en GitHub Actions | 2 | T-14, T-16 | Plataforma | Transversal |
| **T-30** | Documentación: `README`, Model Card del sistema, documentación de la API, manual de despliegue | 2 | T-28 | Documentación | OE4 |
| **T-31** | Informe de evaluación: resultados por campo, modos de error, comparación entre escalas, transferibilidad, límites y conclusiones | 3 | T-26, T-27 | Documentación | OE5 |

---

## 3.3 Análisis de la ruta crítica

### 3.3.1 Cadena crítica identificada

La secuencia más larga de tareas dependientes —aquella cuyo retraso desplaza el fin del proyecto— es:

```
T-02  →  T-07  →  T-08  →  T-09  →  T-15  →  T-25  →  T-26  →  T-31
 (3)     (2)      (5)      (1)      (5)      (2)      (1)      (3)
esquema  corpus  anotación  gold   iteración  eval    comp.   informe
                            v1     de prompt  8B      70B
```

**Esfuerzo acumulado en la cadena: 22 SP.**

Descontando el paralelismo de T-08 (5 SP repartidos entre 4 personas ≈ 1,25 días) y de T-15 (parcialmente divisible entre 2 personas trabajando sobre campos distintos del esquema, ≈ 3 días), la **duración mínima teórica de la cadena crítica ronda los 15–16 días transcurridos**.

> ⚠️ **Hallazgo relevante para el cronograma: la ruta crítica consume prácticamente todo el plazo del módulo.** No existe holgura significativa en esta cadena. Cualquier retraso en el cierre del esquema (T-02) o en la anotación (T-08) se traslada íntegro a la fecha de entrega.

### 3.3.2 Tareas críticas — no admiten retraso

| ID | Tarea | Por qué es crítica | Mitigación |
|---|---|---|---|
| **T-02** | Esquema de salida | Bloquea 9 tareas de forma directa. Un cambio tardío invalida anotación ya hecha | Cerrarlo el primer día con acuerdo formal de los 4; versionarlo y prohibir cambios tras el inicio de T-08 |
| **T-08** | Anotación del corpus | Bloquea toda la evaluación. Es intensiva en trabajo humano y difícil de acelerar | Iniciar apenas exista corpus crudo; fijar cuota diaria por persona; anotar en dos tandas para detectar problemas del protocolo temprano |
| **T-15** | Iteración del prompt | Es investigación empírica: su duración no es plenamente predecible | Fijar un número máximo de iteraciones y congelar el prompt en una fecha límite, aunque no se haya agotado la mejora |
| **T-16** | Normalización geográfica | Alta incertidumbre técnica: la toponimia informal es el problema más difícil del proyecto | Definir un alcance mínimo aceptable (resolución a nivel de comuna) y tratar la resolución a barrio como incremento |
| **T-25** | Evaluación y análisis de errores | Alimenta el informe final, que no puede empezar sin ella | Construir T-24 (marco de evaluación) anticipadamente para que la corrida sea inmediata |

### 3.3.3 Tareas con holgura

Las siguientes tareas **no están en la ruta crítica** y pueden absorber retrasos sin afectar la entrega. Son las candidatas naturales a ceder recursos cuando la ruta crítica se tensione:

`T-17` (duplicados) · `T-19` (fuente en vivo) · `T-23` (vista de detalle) · `T-27` (transferibilidad) · `T-30` (documentación)

---

## 3.4 Paralelización: cuatro frentes de trabajo

Tras completar la Fase 0, el trabajo se divide en cuatro frentes con interfaces definidas, ejecutables en paralelo.

| Frente | Alcance | Tareas | SP |
|---|---|---|---|
| **A — Datos y Evaluación** | Corpus, protocolo de anotación, marco de evaluación, experimentos, informe | T-04, T-07, T-08\*, T-09, T-24, T-25, T-26, T-27, T-31 | 19 |
| **B — Núcleo de extracción** | Esquema, ontología, prompt, cliente de inferencia, validador, pipeline | T-02, T-03, T-11, T-12, T-13, T-14, T-15 | 17 |
| **C — Geo e Ingesta** | *Gazetteer*, normalización geográfica, duplicados, fuentes de mensajes, anonimización | T-06, T-10, T-16, T-17, T-18, T-19 | 12 |
| **D — Plataforma e Interfaz** | Repositorio, credenciales, persistencia, API, tablero, Docker, pruebas, documentación | T-01, T-05, T-20, T-21, T-22, T-23, T-28, T-29, T-30 | 16 |

\* *T-08 (5 SP) es colectiva: se reparte entre los cuatro integrantes (~1,25 SP cada uno), aunque se contabiliza en el frente A.*

### Carga efectiva por integrante

| Frente | SP propios | + parte de T-08 | **Carga total** |
|---|---|---|---|
| A | 14 | 1,25 | **15,25** |
| B | 17 | 1,25 | **18,25** |
| C | 12 | 1,25 | **13,25** |
| D | 16 | 1,25 | **17,25** |

**Total: 64 SP.** El frente B está sobrecargado y el C es el más liviano; se recomienda trasladar T-11 (cliente de inferencia, 2 SP) de B a C, dejando B en 16,25 y C en 15,25. El equipo debe balancear según afinidades reales.

### Puntos de sincronización obligatorios

Momentos en que los frentes deben converger antes de continuar:

| Sincronización | Participantes | Condición de salida |
|---|---|---|
| **S1 — Cierre del esquema** | Los 4 | T-02 aprobado por consenso. Nadie avanza en anotación, prompt, persistencia ni tablero antes de esto |
| **S2 — Jornada de anotación** | Los 4 | T-08 completada; discrepancias identificadas |
| **S3 — Integración del pipeline** | B + C | T-14 y T-16 conectados: la salida del modelo pasa por normalización geográfica |
| **S4 — Integración de interfaz** | C + D | T-21 consume registros reales del pipeline, no datos simulados |
| **S5 — Congelación de código** | Los 4 | Fin del desarrollo funcional; solo correcciones. Habilita T-28 y T-31 |

---

## 3.5 Capacidad y sobrecompromiso

### El análisis que el equipo debe resolver antes de fijar fechas

| Concepto | Valor |
|---|---|
| Integrantes | 4 |
| Duración del módulo | 15 días |
| **Capacidad teórica máxima** | **60 SP** (4 × 15) |
| **Esfuerzo estimado del plan** | **64 SP** |
| **Sobrecompromiso** | **+7 %** |

La capacidad teórica supone dedicación completa de los cuatro integrantes durante los quince días, lo cual **no es realista** en un contexto académico con otras asignaturas en curso. Escenarios:

| Escenario | Dedicación efectiva | Capacidad real | Veredicto sobre 64 SP |
|---|---|---|---|
| Optimista | 100 % | 60 SP | Inviable por 4 SP |
| **Realista** | **70 %** | **42 SP** | **Requiere recortar ~22 SP** |
| Conservador | 50 % | 30 SP | Requiere recortar ~34 SP |

### Recorte recomendado

Para llevar el plan a un rango ejecutable sin comprometer los objetivos específicos, en este orden:

| Orden | Tarea | SP liberados | Impacto |
|---|---|---|---|
| 1 | **T-19** — fuente en vivo | 2 | El reproductor CSV (T-18) basta para demostrar el sistema. La fuente en vivo pasa a *nice to have* |
| 2 | **T-17** — detección de duplicados | 1 | Ya está declarada como deseable, no comprometida |
| 3 | **T-23** — reducir alcance de la vista de detalle | 1 | Conservar la visualización del mensaje original; el mapa pasa a opcional |
| 4 | **T-29** — limitar pruebas a módulos críticos, sin CI | 1 | Se conserva la suite; se pospone la integración continua |
| 5 | **T-27** — transferibilidad con corpus mínimo | 1 | Reducir a ~30 mensajes del dominio alterno |
| | **Total liberado** | **6 SP → plan de 58 SP** | |

Si el escenario resulta ser el conservador, el recorte debe continuar sobre T-26 (comparación 70B) y sobre el alcance del tablero — **nunca sobre T-02, T-08, T-09, T-15 ni T-25**, que son la ruta crítica y sostienen los objetivos.

> **Recomendación.** Estimar el proyecto en **~59 SP con recorte aplicado** y declarar explícitamente en el cronograma qué tareas son de alcance flexible. Un plan que reconoce su propio margen es más creíble que uno que asume dedicación perfecta.

---

## 3.6 Hitos lógicos

Puntos de control definidos por dependencias, no por fechas. El equipo les asignará fecha al construir el diagrama de Gantt.

| Hito | Se alcanza cuando | Habilita |
|---|---|---|
| **H1 — Contrato definido** | T-02, T-03, T-04 completadas | Todo el trabajo paralelo |
| **H2 — Corpus disponible** | T-09 completada | Iteración de prompt y evaluación |
| **H3 — Extracción funcional** | T-14 completada | Iteración, evaluación e integración |
| **H4 — Pipeline integrado** | T-15, T-16 completadas | Evaluación definitiva y tablero con datos reales |
| **H5 — Sistema navegable** | T-22, T-23 completadas | Demostración funcional |
| **H6 — Resultados obtenidos** | T-25, T-26, T-27 completadas | Redacción del informe |
| **H7 — Entregable listo** | T-28, T-30, T-31 completadas | Sustentación |

---

## 3.7 Riesgos que amenazan el plan

| # | Riesgo | Probabilidad | Impacto | Respuesta |
|---|---|---|---|---|
| R1 | El esquema (T-02) se modifica después de iniciada la anotación | Media | **Alto** — invalida trabajo de anotación | Congelar el esquema en S1; los cambios posteriores solo por decisión unánime y con reanotación presupuestada |
| R2 | La anotación (T-08) toma más de lo estimado | **Alta** | Alto — desplaza toda la ruta crítica | Reducir el corpus a 300 mensajes antes que extender el plazo. Un corpus más pequeño y bien anotado es preferible a uno grande y ruidoso |
| R3 | La iteración del prompt (T-15) no converge | Media | Medio | Fijar tope de iteraciones y fecha de congelación; documentar el estado alcanzado como resultado |
| R4 | La normalización geográfica (T-16) resulta más difícil de lo previsto | **Alta** | Medio | Alcance mínimo a nivel de comuna; la resolución a barrio se declara incremento opcional |
| R5 | Cambian las cuotas gratuitas del proveedor de inferencia | Baja | Alto | Supuesto S1 del capítulo 2: migración a proveedor alterno mediante configuración |
| R6 | Indisponibilidad de un integrante | Media | Alto | Interfaces definidas entre frentes; ningún frente depende de conocimiento no documentado |
| R7 | Sobrecompromiso no reconocido (64 SP sobre capacidad de 42) | **Alta** | **Alto** | Aplicar el recorte de §3.5 **antes** de iniciar, no a mitad de camino |

---

## 3.8 Definición de Terminado (*Definition of Done*)

Criterio uniforme para cerrar cualquier ticket:

1. El código está en la rama principal, revisado por al menos otro integrante.
2. Los criterios de aceptación del ticket se cumplen y son verificables.
3. Existen pruebas cuando la tarea produce lógica ejecutable.
4. La documentación afectada quedó actualizada.
5. La tarea no rompe el despliegue ni la suite de pruebas existente.

---

## 3.9 Insumos para construir el Gantt

Para el diagrama del capítulo 3, este documento aporta:

- **31 tareas** con identificador estable (`T-01`…`T-31`) para nombrar barras y tickets.
- **Estimación en SP** convertible a duración mediante la regla 1 SP = 1 día-persona.
- **Dependencias explícitas** en la columna *Depende de* — son las flechas del diagrama.
- **Ruta crítica** de 8 tareas para resaltar en color diferenciado.
- **Cuatro frentes** para las calles o carriles del diagrama.
- **Siete hitos** para marcar como rombos.
- **Cinco puntos de sincronización** que actúan como restricciones de convergencia.

**Sugerencia de agrupación por fases del enunciado del módulo:**

| Fase del enunciado | Tareas |
|---|---|
| **Preparación** (literatura y requisitos) | T-01 a T-06 |
| **Desarrollo** (datos y modelo) | T-07 a T-19 |
| **Implementación** (Docker y pruebas) | T-20 a T-31 |

---

## 3.10 Anexo — Ejemplo de ticket derivado

Formato aplicable a las 31 tareas al poblar el tablero Kanban del capítulo 5.

> ### Ticket T-16: Normalización geográfica determinista
> **5 SP** · Etiquetas: `ML` `Backend` `Ruta-Crítica` · Frente: C · Objetivo: **OE3 — Situar territorialmente los reportes**
>
> **Depende de:** T-06 (*gazetteer*), T-14 (pipeline de extracción)
>
> **Descripción:** Implementar el módulo `geocoder.py` que reciba el bloque de ubicación extraído por el modelo (`ubicacion_texto_literal`, `barrio`, `punto_referencia`) y lo resuelva contra el *gazetteer* de Cali, devolviendo la entidad territorial normalizada con su nivel de granularidad. El módulo es determinista: no invoca al modelo de lenguaje.
>
> **Criterios de aceptación:**
> - La función recibe el bloque de ubicación y retorna barrio, comuna, nivel de granularidad y coordenadas cuando la resolución lo permita.
> - Ante referencia ambigua, retorna el nivel de granularidad más específico que sea defendible, nunca una suposición de mayor precisión.
> - Ante referencia irresoluble, retorna `nivel_granularidad = "indeterminada"` y coordenadas nulas — **nunca un valor inventado**.
> - Existen pruebas con casos de toponimia informal, ambigüedad y ausencia de ubicación.
> - Se documenta la comparación del comportamiento del sistema con y sin el módulo.

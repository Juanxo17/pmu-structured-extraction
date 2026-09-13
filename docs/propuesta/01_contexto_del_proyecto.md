# 1. Contexto del Proyecto

> **Proyecto:** SIRENA — *Sistema de Interpretación de Reportes de Emergencia y Necesidades Automatizado*
> **Eje temático:** 4 — Educación, Cultura, Comunicación y Cohesión Social
> **Modelo base:** `meta-llama/Llama-3.1-8B-Instruct` (Hugging Face Hub)
> **Documento:** Propuesta de Proyecto de Curso — Módulo 2, Entregable 2
> **Universidad Autónoma de Occidente**

*Nombre del proyecto sujeto a validación del equipo.*

---

## 1.1 Encuadre temático: por qué esto es un problema de comunicación y cohesión social

Este proyecto se inscribe en el Eje 4 porque su objeto de estudio **no es el fenómeno natural, sino el canal comunicativo entre la ciudadanía y sus instituciones**.

Cuando ocurre una emergencia de gran escala, la población produce de forma espontánea un volumen masivo de información situacional: dónde se cayó un muro, quién quedó atrapado, qué barrio se quedó sin agua, quién tiene una camioneta disponible para transportar heridos. Esa información es, en términos técnicos, la mejor fuente de datos en tiempo real que existe sobre el territorio afectado — y es producida gratuitamente por los propios ciudadanos.

El problema es que se produce en un formato que las instituciones **no pueden consumir**: lenguaje natural, coloquial, fragmentado, con jerga local, con referencias geográficas informales y mezclado con un volumen mucho mayor de ruido, opinión y rumor.

Cuando ese canal se satura y la institución no logra escuchar, ocurren dos daños. El primero es operativo: se pierden reportes válidos y la respuesta llega tarde. El segundo es social y más duradero: **el ciudadano aprende que reportar no sirve**. Deja de hacerlo. La confianza en el canal oficial se erosiona, y con ella la disposición a colaborar en la siguiente emergencia. Ese deterioro de la relación entre comunidad e institución es precisamente un problema de cohesión social.

SIRENA se plantea, entonces, como un **traductor entre el lenguaje ciudadano y el lenguaje institucional**: un sistema que convierte la comunicación desestructurada de la comunidad en información estructurada, verificable y accionable para un Puesto de Mando Unificado (PMU).

---

## 1.2 El detonante: terremoto del 10 de agosto de 2026

El 10 de agosto de 2026, a las 7:34 a.m., un sismo de **magnitud 7,4** con epicentro en San José del Palmar (Chocó) y profundidad de 96 km sacudió el occidente colombiano. Fue percibido en Bogotá, Medellín, Cali, Pereira y Manizales, y constituye **el sismo más fuerte sentido en Colombia en la última década** según el Servicio Geológico Colombiano (SGC), que registró cinco réplicas superiores a magnitud 3,0.

En Santiago de Cali, el balance inicial reportado por la Alcaldía el mismo 10 de agosto fue de **28 personas fallecidas, 380 lesionadas atendidas en centros médicos y 26 edificaciones colapsadas** en zona urbana. Ese balance subió considerablemente en las semanas siguientes: según el **Repositorio Oficial de Información del Terremoto de Cali** de la Alcaldía de Santiago de Cali, con corte al **28 de agosto de 2026, 5:00 p.m.**, la cifra en Cali es de **154 fallecidos, 1.657 lesionados, 88 personas rescatadas, 17 reportes de desaparecidos y 24 edificaciones con colapso total**. Esta página se actualiza de forma continua, por lo que el equipo debe volver a consultarla inmediatamente antes de la entrega del 3 de septiembre de 2026 y citar la cifra vigente con su fecha y hora de corte — no usar el balance inicial del día 10 como cifra definitiva. Fuente: Alcaldía de Santiago de Cali, *Repositorio Oficial de Información* — https://www.cali.gov.co/gobierno/publicaciones/193607/terremoto-de-cali-repositorio-oficial-de-informacion/ (consultado el 30 de agosto de 2026).

El Gobierno instaló Puestos de Mando Unificado el mismo día. En Cali, el PMU consolidó los informes de afectación y coordinó las operaciones con **dos reportes diarios (8:00 a.m. y 5:00 p.m.)**, articulando:

| Entidad | Recurso desplegado |
|---|---|
| Cuerpo de Bomberos | 260 voluntarios |
| Defensa Civil | 115 operativos |
| Cruz Roja | 101 socorristas |
| Rescatistas nacionales | 92 especialistas |
| Secretaría de Salud Pública Distrital | — |
| Ejército Nacional | — |

El 15 de agosto, el director de operaciones de emergencias de la Cruz Roja Valle advirtió durante el PMU que la recuperación **"nos va a durar entre dos y cuatro años"**. La Alcaldía instaló posteriormente un nuevo PMU dedicado a la fase de reconstrucción.

Este evento no es un ejemplo hipotético: es un caso local, reciente y oficialmente documentado, ocurrido en la ciudad donde se desarrolla este proyecto, y su fase de recuperación sigue activa al momento de esta propuesta.

---

## 1.3 Caracterización del problema

### 1.3.1 El problema está declarado por la propia autoridad

El hallazgo central de nuestra investigación de antecedentes es que **no es necesario argumentar que el problema existe: la autoridad competente lo declaró por escrito durante la emergencia**.

En su boletín oficial sobre las emergencias y medidas por el terremoto, la Alcaldía de Santiago de Cali emitió dos instrucciones simultáneas a la ciudadanía:

1. **Limitar las llamadas telefónicas**, "para evitar el colapso de las antenas repetidoras", y reservar las llamadas de emergencia exclusivamente para situaciones de peligro real o rescate, con el fin de **evitar la saturación de los canales de socorro** y garantizar una respuesta rápida a las personas afectadas.
2. **Abstenerse de difundir material audiovisual o mensajes de texto no verificados.**

Y, de forma coherente con lo anterior, habilitó canales de reporte que incluyen explícitamente uno de texto:

| Canal | Número | Naturaleza |
|---|---|---|
| Emergencias | 123 | Voz |
| Bomberos | 119 | Voz |
| Cruz Roja | 132 | Voz |
| Salud mental | 106 | Voz |
| **WhatsApp — reportes urbanos** | **310 229 97 08** | **Texto / multimedia** |

De estas tres decisiones institucionales se desprenden directamente los tres pilares del problema:

- **El canal de voz colapsa** bajo demanda extrema. Está reconocido oficialmente.
- **La institución empuja el reporte hacia canales de texto** — y un canal de texto abierto a toda la ciudadanía genera un volumen que ningún operador humano puede estructurar manualmente en tiempo real.
- **Por esos canales circula desinformación**, al punto de requerir una advertencia pública explícita.

A esto se suma un cuarto factor que agrava la consecuencia de cada reporte perdido: la **saturación hospitalaria alcanzó el 100 % de la capacidad**. Cuando el recurso disponible es menor que la demanda, la calidad de la información con que se decide determina resultados en vidas.

### 1.3.2 Situación actual (*as-is*): modelo del flujo de información

> **Nota sobre el estatus de esta subsección.** El flujo que se describe a continuación es un **modelo reconstruido**, no un procedimiento transcrito de un manual operativo. Se construye a partir de tres fuentes de distinto peso probatorio, que se declaran separadamente para que el lector pueda evaluar qué está documentado y qué constituye una hipótesis de trabajo del equipo. Su validación empírica es una tarea explícita del proyecto (ver 1.3.3).

**(a) Lo documentado oficialmente.** El PMU es la instancia de coordinación interinstitucional desde la cual se toman las decisiones tácticas y operativas en terreno, y en la que convergen los representantes de las entidades con competencia para actuar en la emergencia. La Sala de Crisis Nacional de la UNGRD **consolida los reportes de daños, necesidades e impactos** de las entidades del Estado para dirigir los recursos y la ayuda a los lugares que más los necesitan, organizándose por servicios de respuesta con el fin de garantizar un adecuado flujo de información. En el caso de Cali, la Alcaldía reportó que el PMU consolidó los informes de afectación con dos reportes diarios (8:00 a.m. y 5:00 p.m.) y habilitó un canal de texto para reportes urbanos.

**(b) Lo documentado en la literatura, de forma general.** La investigación en gestión de emergencias identifica la **sobrecarga informativa sobre los respondientes** como una barrera central para el aprovechamiento de las redes sociales en organizaciones de respuesta. El volumen y la velocidad de los mensajes durante una crisis son extremadamente altos, lo que dificulta su procesamiento oportuno, y el análisis manual de tales volúmenes **no es viable durante la gestión de la emergencia**, por lo que se requieren sistemas automatizados de monitoreo en tiempo real.

De manera más específica, los estudios sobre gestores de emergencias y primeros respondientes identifican **tres barreras organizacionales** para la adopción de redes sociales:

1. **Falta de personal disponible** para monitorear redes sociales.
2. **Falta de herramientas de procesamiento** que eviten la sobrecarga informativa.
3. **Falta de confianza** en la información publicada por los usuarios.

Estas tres barreras se corresponden, respectivamente, con el cuello de botella de capacidad, la ausencia de estructuración automatizada y el problema de la desinformación declarado por la Alcaldía de Cali.

**(c) La hipótesis de trabajo del equipo.** Sobre las dos bases anteriores, modelamos la cadena de valor de la información ciudadana en una activación de PMU de la siguiente manera:

```
Ciudadano  →  Canal (WhatsApp / redes / línea)  →  Recepción y estructuración  →  Coordinación  →  Equipo en terreno
                                                              ▲
                                                  CUELLO DE BOTELLA HIPOTETIZADO
```

La hipótesis es que la **estructuración del mensaje ciudadano —leerlo, decidir si es relevante, identificar qué ocurrió y a qué servicio compete, inferir la ubicación y registrarlo en un formato consolidable— carece de soporte automatizado**, y que por tanto su capacidad está acotada por el personal disponible. De ser correcta, se derivan cuatro fallas:

| Falla hipotetizada | Descripción | Consecuencia esperada | Sustento |
|---|---|---|---|
| **Latencia** | La estructuración sin soporte automatizado toma tiempo por mensaje | Reportes que llegan cuando ya no son accionables | Literatura: procesamiento oportuno inviable a alto volumen |
| **Subregistro** | En picos de volumen la capacidad de recepción se satura | Reportes válidos que nunca se procesan | Literatura: barrera de personal disponible |
| **Duplicación** | Un mismo incidente reportado por múltiples ciudadanos | Despacho redundante de recursos escasos | Inferencia del equipo — pendiente de validación |
| **Registro heterogéneo** | Sin un formato común, cada operador consigna la información con criterios distintos | Reportes no comparables ni agregables entre sí | Inferencia del equipo — pendiente de validación |

**Lo que este modelo NO afirma.** No se afirma que exista un procedimiento manual formalizado de transcripción en el PMU de Cali, ni se dispone de mediciones de latencia, tasa de subregistro o volumen de duplicados para esa institución. No se localizó documentación pública que describa un protocolo específico de monitoreo de redes sociales en el PMU de Cali. La ausencia de documentación pública no equivale a la ausencia del procedimiento, y tampoco a su existencia.

### 1.3.3 Validación pendiente del diagnóstico

Dado el carácter académico y el plazo del proyecto, la validación del modelo *as-is* se limita a **revisión documental de fuentes públicas**, sin trabajo de campo ni requerimientos formales de información a la institución:

1. **Revisión del Plan Municipal de Gestión del Riesgo de Desastres** y de la Estrategia Municipal de Respuesta a Emergencias de Cali, en busca del procedimiento formalizado de recepción y consolidación de reportes ciudadanos.
2. **Consulta de la doctrina institucional de conformación de PMU** publicada por la UNGRD y la Policía Nacional.

Se declara explícitamente como **limitación del estudio** que el diagnóstico del estado actual no fue contrastado con fuentes primarias de la institución.

Si la validación refutara la hipótesis —por ejemplo, si el PMU ya contara con una herramienta de estructuración automatizada—, el proyecto conserva su pertinencia como propuesta de mejora sobre el componente de extracción, y el hallazgo se reportaría como resultado. **El diagnóstico se declara falsable de forma deliberada.**

### 1.3.4 Naturaleza técnica del texto a procesar

El mensaje ciudadano real presenta características que descartan las soluciones convencionales:

- **Multi-intención:** un solo mensaje puede contener varias necesidades distintas ("se cayó el muro de la casa de mi vecina, hay una señora mayor adentro y no tenemos agua desde anoche").
- **Toponimia informal:** las referencias geográficas no existen en ningún catálogo oficial ("por el puente, cerca de la panadería", "subiendo por la loma después del colegio").
- **Registro coloquial y errores de tipeo** propios de la escritura bajo estrés.
- **Ambigüedad temporal:** conviven reportes de hechos en curso con recuerdos, reenvíos y citas de noticias de días anteriores.
- **Ruido dominante:** la mayor parte del tráfico en un canal abierto no constituye un reporte accionable.

---

## 1.4 Formulación del problema

### Enunciado

> Durante eventos de alta demanda informativa en Santiago de Cali, el Puesto de Mando Unificado carece de un mecanismo automatizado que convierta el flujo desestructurado de mensajes ciudadanos en registros estructurados y verificables. Esta ausencia produce latencia en la respuesta institucional, subregistro de reportes válidos, duplicación de despachos sobre recursos escasos y registro heterogéneo entre operadores; efectos que, acumulados, deterioran la confianza ciudadana en los canales oficiales de reporte y debilitan la cohesión entre comunidad e institución.

### Pregunta de investigación

> ¿En qué medida un agente de orquestación basado en un modelo de lenguaje de pesos abiertos y escala accesible (Llama 3.1 8B), operando mediante *prompting* estructurado con salida en JSON validado, puede discriminar el reporte accionable del ruido y extraer de forma confiable el tipo de evento, el servicio de respuesta competente y la ubicación a partir de mensajes ciudadanos escritos en español coloquial colombiano, con calidad suficiente para apoyar la toma de decisiones en un Puesto de Mando Unificado?

### Hipótesis

> Un modelo de pesos abiertos y escala accesible (8 000 millones de parámetros), operado mediante *prompting* estructurado, validación de esquema y una capa determinista de normalización geográfica, es capaz de extraer los campos núcleo de un reporte ciudadano con una confiabilidad y una latencia suficientes para sostener un **triage asistido** —donde un operador humano valida cada registro antes del despacho—, sobre infraestructura de inferencia de costo cero o marginal.
>
> Se anticipa que la degradación del desempeño no será uniforme entre campos, sino que se concentrará en la **resolución de toponimia informal** y en la **asignación del servicio de respuesta competente cuando un mensaje expresa varias necesidades**, por tratarse respectivamente de conocimiento territorial ausente en los datos de entrenamiento y de una discriminación multietiqueta sobre un vocabulario institucional de dieciséis categorías.

La hipótesis es **falsable**: quedaría refutada si el sistema no alcanzara una confiabilidad que justifique su uso como apoyo —esto es, si la carga de corrección impuesta al operador resultara comparable o superior a la de estructurar los mensajes sin asistencia—, o si los errores se distribuyeran de forma impredecible entre campos, impidiendo delimitar en qué puede confiarse y en qué no. La caracterización de esos límites es el propósito de la evaluación (OE5, §2.2).

### Delimitación ética fundamental

**SIRENA es un copiloto, no un decisor.** El sistema produce sugerencias estructuradas que un operador humano valida antes de que se despache cualquier recurso. Esta delimitación es una decisión de diseño, no una limitación técnica: en un dominio donde un error de extracción puede enviar una ambulancia a la dirección equivocada, la responsabilidad de la decisión debe permanecer en una persona. El mecanismo que hace operativa esta delimitación es la presentación de cada registro estructurado junto al mensaje original que lo produjo (§1.5.2).

---

## 1.5 Qué vamos a resolver

SIRENA recibe un flujo de mensajes ciudadanos y produce, por cada uno, un registro estructurado auditable que alimenta un **dashboard de operador PMU** con bandeja de reportes, ordenamiento y filtros configurables, y mapa.

### 1.5.1 Arquitectura del esquema de salida

El esquema tiene **tres capas y diez campos**. Se resuelve en **dos etapas de inferencia**: la compuerta primero, sobre todo el flujo entrante; la extracción completa después, solo sobre los mensajes que la compuerta declaró accionables. Como la mayor parte del tráfico de un canal abierto no es un reporte, esta separación reduce el consumo, evita que el modelo gaste atención estructurando mensajes que debió descartar, y permite medir cada capacidad por separado.

**Capa 1 — Compuerta** *(primera etapa)*. Antes de extraer cualquier dato, el sistema decide si el mensaje merece procesarse:

| Campo | Función |
|---|---|
| `es_reporte_accionable` | Filtra opinión, meme y reenvío. Sin esta compuerta, el sistema se ahoga en ruido |
| `temporalidad` | `ocurriendo_ahora` / `ya_ocurrio` / `riesgo_previsto` / `referencia_noticia`. Evita tratar la cita de una noticia como un incidente activo |
| `intencion` | `solicita_ayuda` / `reporta_terceros` / **`ofrece_ayuda`** / `solicita_informacion` |

El valor `ofrece_ayuda` merece énfasis: durante una emergencia la ciudadanía no solo pide, también ofrece — vehículos, alojamiento, alimentos, mano de obra. Un PMU capaz de **conectar la oferta ciudadana con la demanda ciudadana** convierte el sistema en un instrumento de cohesión social, no solo de gestión de emergencias. Esta categoría está respaldada empíricamente por la taxonomía HumAID, que incluye la clase *"Rescue, volunteering, or donation effort"*.

**Capa 2 — Naturaleza del reporte** *(segunda etapa)*. Qué ocurrió y a qué servicio institucional compete:

| Campo | Valores | Origen del vocabulario |
|---|---|---|
| `tipo_evento` | Sismos · movimientos en masa · inundación súbita · inundación lenta · incendios de cobertura vegetal · incendios estructurales · aglomeración de público · salud ambiental | **ERE de Cali**, escenarios de riesgo con protocolo específico |
| `servicio_de_respuesta[]` | 16 servicios reportables por la ciudadanía — **multietiqueta**, porque un mensaje puede expresar varias necesidades | **ERE de Cali**, servicios de respuesta |

Asignar un servicio de respuesta equivale a identificar la entidad competente: la ERE asigna a cada servicio un responsable principal y sus apoyos.

**Capa 3 — Ubicación descompuesta** *(segunda etapa)*. Nunca una cadena de texto única, y **el modelo no emite coordenadas bajo ninguna circunstancia**:

`ubicacion_texto_literal` · `barrio` · `comuna` · `punto_referencia` · `nivel_granularidad` (exacta / barrio / comuna / ciudad / indeterminada)

La conversión a coordenadas es un paso posterior determinista, mediante geocodificador y *gazetteer* de Cali.

### 1.5.2 Verificabilidad: el mensaje original viaja con el registro

**Cada registro estructurado se almacena y se presenta junto al mensaje original completo que lo produjo.** El operador ve ambos, uno al lado del otro, y valida antes de actuar.

La evidencia así es **completa** —no un fragmento recortado— y **no puede alucinarse**, porque el mensaje es un dato de entrada y no una salida del modelo. Este es el mecanismo concreto que sostiene la definición del sistema como copiloto y no como decisor (§1.4).

El sistema estructura **hechos**: qué se reporta, a qué servicio institucional compete y dónde ocurre. La valoración de esos hechos —su gravedad, su prioridad, el orden de atención— es un juicio experto en gestión del riesgo y permanece en el operador y en las instancias que la normativa faculta para ello.

### 1.5.3 Transferibilidad por diseño

El esquema se organiza como **núcleo invariante + taxonomía enchufable**. Los campos estructurales —la compuerta y el bloque de ubicación— no cambian nunca. Solo dos campos, `tipo_evento` y `servicio_de_respuesta`, cargan su vocabulario desde un archivo de configuración por dominio.

Migrar el sistema de "emergencias por desastre natural" a "seguridad y convivencia ciudadana" o "reporte de fallas en servicios públicos" implica sustituir una ontología y un bloque de ejemplos del *prompt*, no reescribir el sistema. Esta propiedad se evaluará experimentalmente midiendo la degradación de desempeño sobre un dominio no visto.

---

## 1.6 Antecedentes: tres generaciones y un vacío

### Generación 1 — Crowdsourcing manual (2010)

**Ushahidi**, tras el terremoto de Haití, recibió **3 584 reportes ciudadanos** que fueron visualizados cerca de 500 000 veces sobre un mapa, permitiendo a la población reportar su ubicación y sus necesidades. Demostró que la ciudadanía sí produce información situacional valiosa en crisis. Su límite: la estructuración de cada reporte era **enteramente manual**, a cargo de voluntarios digitales. No escala ni sostiene latencia baja.

### Generación 2 — Clasificación supervisada (2013–2020)

**AIDR** (*Artificial Intelligence for Disaster Response*), del Qatar Computing Research Institute, introdujo la clasificación automática de microblogs de crisis en categorías definidas por el usuario, con un esquema colaborativo humano-máquina. Su limitación es la que define nuestro espacio de trabajo: **requiere etiquetado humano de miles de mensajes para cada evento nuevo**. Ante un desastre inédito, el modelo arranca en frío y el costo del re-etiquetado recae sobre el personal de emergencia justo cuando está más saturado. Además, AIDR *clasifica* —asigna una etiqueta— pero no *extrae* los campos estructurados que un PMU necesita para despachar recursos.

### Generación 3 — Modelos de lenguaje de gran escala (2024–2026)

Línea de investigación activa. El consenso de la literatura reciente es que los LLM **superan a los modelos NER tradicionales** en extracción de ubicaciones desde datos sociales de desastre, y lo hacen **sin requerir reentrenamiento específico por evento** — eliminando exactamente la barrera de la Generación 2. Trabajos de referencia: *Harnessing Large Language Models for Disaster Management: A Survey*; *CrisisSense-LLM*, que valida la clasificación multi-etiqueta de un mismo mensaje; y *LLMs for Causal Relations Extraction in Social Media*, que aporta un marco de validación para sistemas de apoyo a la decisión en desastres.

El trabajo más directamente aplicable es **Cafferata, Demarco, Kalimeri, Mejova y Beiró (2025)**, sobre extracción de geolocalización en respuesta humanitaria. Evaluaron GPT-5, GPT-4o, DeepSeek y Claude Sonnet/Haiku 4.5 contra baselines de SpaCy y RoBERTa, con tres resultados que estructuran nuestro diseño:

1. **GPT-4o con salida JSON alcanzó precisión exacta 0,87 y F1 0,84**; GPT-5 en Markdown llegó a F1 parcial 0,92. Este es el rango de referencia del estado del arte **con modelos propietarios de frontera**.
2. **El agente de geocodificación posterior elevó la precisión exacta de 0,69 a 0,88** frente a un baseline basado en reglas. La arquitectura *"el LLM extrae, un componente determinista geocodifica"* está validada empíricamente y aporta cerca de 19 puntos porcentuales.
3. **El formato de salida es una variable experimental**, no un detalle de implementación: el desempeño cambia según se use JSON o Markdown.

Los autores señalan como limitaciones los sesgos residuales heredados de GeoNames y la dificultad con topónimos no estándar o ambiguos, y nombran explícitamente como trabajo futuro pendiente la **extensión a textos multilingües y contextos de bajos recursos**.

### El vacío que ocupa este proyecto

> La literatura de LLM aplicados a desastres está dominada por el **inglés** y por **modelos propietarios de frontera**. El mayor dataset del área, **HumAID** (77 196 tuits anotados de 19 desastres entre 2016 y 2019), es **exclusivamente en inglés**. No se localizó trabajo que evalúe **modelos de pesos abiertos y escala accesible (8B) sobre reportes ciudadanos en español coloquial colombiano, con toponimia urbana informal, bajo restricciones de despliegue de costo cero y con una taxonomía transferible entre dominios.**

Este vacío es específico, verificable y abordable dentro del alcance del curso.

---

## 1.7 Descripción del modelo base

| Atributo | Valor |
|---|---|
| **Nombre** | Meta Llama 3.1 8B Instruct |
| **Identificador** | `meta-llama/Llama-3.1-8B-Instruct` |
| **Enlace oficial** | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct |
| **Plataforma MaaS** | Hugging Face Hub |
| **Creador** | Meta AI |
| **Fecha de lanzamiento** | 23 de julio de 2024 |
| **Función** | NLP — generación condicionada, seguimiento de instrucciones, extracción de información estructurada y *function calling* |
| **Arquitectura** | Modelo de lenguaje autorregresivo sobre arquitectura *transformer* optimizada, con ajuste supervisado (SFT) y aprendizaje por refuerzo con retroalimentación humana (RLHF) |
| **Parámetros** | 8 000 millones |
| **Longitud de contexto** | 128 000 tokens |
| **Licencia** | Llama 3.1 Community License (licencia comercial personalizada) |

**Modelo de comparación:** `meta-llama/Llama-3.3-70B-Instruct` (Meta AI, 6 de diciembre de 2024, 70 000 millones de parámetros, 128 K de contexto, Llama 3.3 Community License) se empleará como cota superior de referencia para cuantificar la brecha de desempeño atribuible a la escala del modelo, no como modelo de despliegue. Enlace oficial: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct

---

## 1.8 Model Card

### 1.8.1 Datos de entrenamiento

Aproximadamente **15 billones de tokens** provenientes de fuentes públicamente disponibles, con **corte de conocimiento en diciembre de 2023**. El corte es relevante para nuestro caso de uso: el modelo **no tiene conocimiento del terremoto de agosto de 2026** ni de la toponimia actualizada de Cali. Toda la información situacional debe provenir del texto de entrada, lo que refuerza la prohibición de que el modelo emita coordenadas o infiera datos no presentes en el mensaje.

### 1.8.2 Métricas de rendimiento declaradas

| Benchmark | Llama 3.1 8B Instruct | Llama 3.3 70B Instruct |
|---|---|---|
| MMLU (CoT) | 73,0 %¹ | 86,0 % |
| **IFEval** (seguimiento de instrucciones) | **80,4 %** | **92,1 %** |
| GSM-8K | 84,5 % | — |
| HumanEval | 72,6 % | 88,4 % |
| MATH | — | 77,0 % |
| GPQA Diamond | — | 50,5 % |
| BFCL v2 (*function calling*) | — | 77,3 % |
| MGSM (multilingüe) | 68,9 % | — |

**IFEval es la métrica más relevante para este proyecto.** Mide la capacidad del modelo de adherirse a instrucciones de formato explícitas —exactamente lo que se le exige a SIRENA al obligarlo a devolver un JSON conforme a un esquema fijo. Un 80,4 % en el modelo de 8B es un punto de partida razonable, y la brecha frente al 92,1 % del 70B es una de las hipótesis que el experimento comparativo pondrá a prueba.

*Las cifras corresponden a los Model Cards oficiales de Meta publicados en Hugging Face Hub; las condiciones de evaluación (número de ejemplos, uso de cadena de pensamiento) deben citarse textualmente del Model Card en la versión final del documento.*

¹ *Verificado directamente en el Model Card oficial de `meta-llama/Llama-3.1-8B-Instruct` en Hugging Face (consultado el 30 de agosto de 2026): MMLU 73,0 % con evaluación de cadena de pensamiento (CoT). La cifra previa de 69,4 % en este documento no correspondía a la metodología CoT y fue corregida.*

### 1.8.3 Idiomas soportados oficialmente

Inglés, alemán, francés, italiano, portugués, hindi, **español** y tailandés (ocho idiomas en Llama 3.1; siete más inglés en Llama 3.3).

El español está oficialmente soportado, lo que habilita el proyecto. Sin embargo, el soporte declarado corresponde al español estándar; **el español coloquial colombiano, con jerga caleña, elisiones y toponimia barrial, constituye un caso fuera de la distribución de entrenamiento.** Medir el desempeño en ese registro es parte del aporte del proyecto.

### 1.8.4 Sesgos, limitaciones y consideraciones éticas

**Declarados por Meta:**

- El modelo "puede, en algunos casos, producir respuestas inexactas, sesgadas u objetables". Meta traslada explícitamente al desarrollador la responsabilidad de realizar pruebas de seguridad adaptadas a la aplicación específica.
- Los idiomas no soportados requieren ajuste fino y controles de sistema antes de su despliegue.
- La Política de Uso Aceptable prohíbe actividades ilegales, explotación infantil, discriminación, creación de *malware* y engaño.

**Identificados para este caso de uso concreto:**

| Riesgo | Descripción | Mitigación en el diseño |
|---|---|---|
| **Alucinación de ubicación** | El modelo puede inventar una ubicación plausible no presente en el mensaje | El registro se presenta junto al mensaje original, permitiendo contraste inmediato. Prohibición de emitir coordenadas: la resolución territorial es determinista. Ante referencia irresoluble, `nivel_granularidad = indeterminada` |
| **Sesgo lingüístico** | Entrenamiento mayoritariamente anglófono; el registro coloquial caleño está fuera de distribución | Evaluación explícita sobre corpus en español local; documentación de la degradación observada |
| **Sesgo geográfico heredado** | La literatura documenta sesgos residuales provenientes de GeoNames en la etapa de geocodificación | Uso de *gazetteer* local de Cali como fuente primaria de normalización |
| **Sesgo de cobertura socioeconómica** | Quien carece de conectividad no reporta; el sistema puede invisibilizar comunas vulnerables | Se documenta como **hallazgo del proyecto**, no como defecto oculto. Es un resultado relevante para el Eje 4 |
| **Datos personales** | Los mensajes contienen nombres, teléfonos y direcciones | Anonimización en el preprocesamiento, antes de que el mensaje llegue al modelo. Exigido por la Ley 1581 de 2012 |
| **Confianza excesiva del operador** | Riesgo de que el humano valide sin revisar (*automation bias*) | Campos de confianza visibles y marca `requiere_revision_humana` en el dashboard |

---

## 1.9 Restricciones técnicas

### 1.9.1 Software

| Componente | Selección |
|---|---|
| Lenguaje | Python 3.11+ |
| Validación de esquema | Pydantic v2 / JSON Schema |
| API de servicio | FastAPI |
| Dashboard | Streamlit |
| Datos | Pandas, SQLite |
| Geocodificación | Nominatim / *gazetteer* local de Cali |
| Contenedor | Docker |
| Cliente de inferencia | SDK OpenAI-compatible (Groq) / `huggingface_hub` |

### 1.9.2 Hardware

El proyecto **no requiere GPU**. Esta es una decisión deliberada y una restricción real del equipo: no se dispone de máquina con capacidad de inferencia local.

Como referencia de la restricción evitada: Llama 3.3 70B en precisión FP16 exige del orden de 140 GB de VRAM, y aun cuantizado a 4 bits ronda los 40 GB — inviable en hardware de estudiante. Por ello la ejecución se realiza mediante **API de inferencia**, y el requisito de hardware se reduce a un equipo de desarrollo estándar con conexión a internet.

### 1.9.3 Infraestructura de inferencia y cuotas

| Proveedor | Modelo | Cuota gratuita | Rol en el proyecto |
|---|---|---|---|
| **Groq** | `llama-3.1-8b-instant` | 14 400 req/día · 500 K tokens/día · 6 K TPM | **Motor de producción** |
| **Groq** | `llama-3.3-70b-versatile` | 1 000 req/día · 30 RPM · 12 K TPM · 100 K TPD | **Benchmark comparativo** |
| Hugging Face | Inference Providers (gratuito) | USD 0,10/mes en créditos | Insuficiente para ejecución; se usa como **fuente del Model Card y de los datasets** |
| Hugging Face PRO | Inference Providers | 2 M créditos/mes por USD 9 | Alternativa de contingencia |

**Restricción operativa:** las cuotas de Groq aplican a nivel de organización, no de clave de API; múltiples claves no multiplican el límite. Con un equipo de cuatro integrantes, cada uno usará su propia organización para desarrollo, reservando una cuenta única para las corridas oficiales de evaluación.

Las cuotas gratuitas son suficientes con holgura: la evaluación completa del *gold standard* (300–400 mensajes) consume menos de la mitad del límite diario del modelo de 70B.

### 1.9.4 Fuentes de datos y sus restricciones

| Fuente | Condición de acceso (agosto 2026) | Rol |
|---|---|---|
| **Bluesky (AT Protocol)** | Gratuito, sin tier pago ni proceso de aprobación. Límite por puntos (5 000/hora) | **Fuente principal en vivo** |
| **X / Twitter** | Sin tier gratuito. Modelo *pay-per-use*: **USD 0,005 por lectura** (el plan Basic de USD 200/mes fue retirado el 1 de junio de 2026) | Opcional, con presupuesto acotado (~USD 10 por 2 000 mensajes) |
| **Telegram** | Gratuito mediante bot en canal propio | Simulación del canal WhatsApp institucional |
| Reddit | Gratuito con OAuth | Complementaria |
| Reproductor CSV | — | Demostración reproducible en sustentación |

**Restricción reconocida:** WhatsApp Business API requiere verificación empresarial, incompatible con el plazo del proyecto. Telegram se adopta como sustituto metodológico del canal 310 229 97 08 habilitado por el Distrito, y así se declara.

La arquitectura define una interfaz `FuenteDeMensajes` con implementaciones intercambiables, de modo que la elección de plataforma sea configuración y no dependencia estructural.

### 1.9.5 Licencias y marco normativo

| Norma / licencia | Implicación |
|---|---|
| **Llama 3.1 Community License** | Licencia comercial personalizada de Meta, **no OSI** (no es MIT ni Apache 2.0). Compatible con uso académico. Exige atribución *"Built with Llama"* y requiere licencia comercial adicional para productos con más de 700 millones de usuarios activos mensuales — umbral irrelevante para este proyecto pero de citación obligatoria |
| **Política de Uso Aceptable de Meta** | Restringe usos ilegales, discriminatorios y engañosos |
| **Ley 1523 de 2012** | Adopta la Política Nacional de Gestión del Riesgo de Desastres y establece el SNGRD. Es la norma que da existencia jurídica al PMU |
| **Ley 1581 de 2012** | Protección de datos personales. Obliga el tratamiento y anonimización de la información personal contenida en los mensajes ciudadanos |
| **Licencias de datasets** | HumAID y CrisisBench (QCRI) se emplean bajo sus términos de uso académico |

---

## 1.10 Justificación

### ¿Por qué este problema?

Porque está documentado oficialmente, es local y es actual. La Alcaldía de Santiago de Cali declaró por escrito, durante la emergencia del 10 de agosto de 2026, que los canales de socorro se saturan, que empujó el reporte hacia canales de texto y que por esos canales circula material no verificado. El PMU de reconstrucción sigue activo y la propia Cruz Roja estima entre dos y cuatro años de recuperación. **El proyecto no atiende un escenario hipotético sino una necesidad institucional vigente en la ciudad donde se desarrolla.**

### ¿Por qué un modelo de lenguaje y no un clasificador convencional?

Porque la Generación 2 de esta línea tecnológica ya demostró su techo. Un clasificador supervisado exige miles de ejemplos etiquetados por cada evento nuevo, y ese costo recae sobre el personal de emergencia en el peor momento posible. Un LLM ajustado a instrucciones resuelve extracción, normalización y clasificación en un solo paso, sin dataset propio de gran escala, y su desempeño en extracción de ubicaciones **supera a los modelos NER tradicionales** según la literatura reciente. Adicionalmente, el texto real es multi-intención: un solo mensaje contiene varias necesidades simultáneas, un caso que la clasificación de etiqueta única no representa.

### ¿Por qué Llama 3.1 8B específicamente?

**Por cuatro razones convergentes:**

1. **Capacidad adecuada a la tarea.** El requisito central no es conocimiento del mundo sino adherencia estricta a un formato de salida. Su IFEval de 80,4 % mide exactamente esa capacidad, y el modelo está optimizado para *function calling* y estructuración en JSON.
2. **Viabilidad económica real.** 14 400 solicitudes diarias gratuitas en Groq permiten iterar sin presupuesto. Un modelo propietario de frontera haría inviable la experimentación repetida que exige el ajuste de *prompts*.
3. **Pesos abiertos y soberanía del dato.** Aunque este proyecto ejecuta vía API por restricción de hardware, un modelo de pesos abiertos **admite despliegue local en la institución**. Esto es determinante en producción: los mensajes ciudadanos contienen datos personales que, bajo la Ley 1581 de 2012, no deberían salir de la infraestructura institucional. Un modelo cerrado cierra esa puerta de forma permanente; Llama la deja abierta.
4. **Escala accesible como pregunta de investigación.** El estado del arte reporta F1 de 0,84 a 0,92 con GPT-5 y Claude. Determinar cuánto de ese desempeño conserva un modelo de 8B —ejecutable gratuitamente y desplegable en una alcaldía— **es en sí mismo el aporte del proyecto**, no una concesión por falta de recursos.

### ¿Cómo se integra en producción?

SIRENA se inserta en el nodo *operador* de la cadena de valor, sin reemplazarlo. El operador deja de transcribir y pasa a validar: recibe registros ya estructurados junto al mensaje original que los produjo, y los ordena y filtra según el criterio que la situación exija. La ganancia no es sustituir el juicio humano sino **liberarlo del trabajo mecánico para concentrarlo en la decisión**.

El sistema se entrega contenedorizado en Docker, con una API FastAPI y un dashboard Streamlit, de modo que su despliegue en la infraestructura de un PMU no dependa del entorno de desarrollo del equipo.

### ¿Por qué importa más allá de la emergencia?

Porque un canal de reporte que responde es un canal que la ciudadanía sigue usando. Cada reporte procesado y atendido refuerza la percepción de que participar sirve; cada reporte perdido la erosiona. Al hacer que la institución **escuche efectivamente** lo que la comunidad ya está diciendo —y al conectar además la oferta espontánea de ayuda con la demanda real—, el sistema interviene sobre la relación entre comunidad e institución. Ese es el sentido en que este proyecto pertenece al eje de Comunicación y Cohesión Social.

---

## Referencias del capítulo

**Caso de estudio**

- Alcaldía de Santiago de Cali. *Emergencias y medidas por terremoto en Cali*. https://www.cali.gov.co/boletines/publicaciones/193598/emergencias-y-medidas-por-terremoto-en-cali/
- Alcaldía de Santiago de Cali. *Terremoto de Cali — Repositorio Oficial de Información*. https://www.cali.gov.co/gobierno/publicaciones/193607/terremoto-de-cali-repositorio-oficial-de-informacion/
- Infobae (10/08/2026). *El sismo de 7,4 se sintió en varias ciudades del país*.
- Infobae (11/08/2026). *Más de 130 muertos, 570 heridos: las cifras que deja el terremoto en Colombia*.
- Infobae (15/08/2026). *Director de operaciones de emergencias de la Cruz Roja Valle en el PMU de Cali*.
- El Heraldo (10/08/2026). *Gobierno instala puestos de mando unificados para atender la emergencia*.
- Semana (08/2026). *Cali comienza la reconstrucción: alcalde Eder instala nuevo Puesto de Mando Unificado*.

**Estado del arte**

- Cafferata, Demarco, Kalimeri, Mejova y Beiró (2025). *Large Language Models for Geolocation Extraction in Humanitarian Crisis Response*. arXiv:2602.08872.
- *Extracting Disaster Impacts and Impact Related Locations in Social Media Posts Using Large Language Models*. arXiv:2511.21753.
- *Large Language Models for Causal Relations Extraction in Social Media: A Validation Framework for Disaster Intelligence*. arXiv:2605.11348.
- *Harnessing Large Language Models for Disaster Management: A Survey*.
- Imran, Castillo, Lucas, Meier y Vieweg. *AIDR: Artificial Intelligence for Disaster Response*. ACM. https://dl.acm.org/doi/10.1145/2567948.2577034
- *Crowdsourcing Crisis Information in Disaster-Affected Haiti* (Ushahidi).

**Sobrecarga informativa y flujo de trabajo en centros de operaciones de emergencia**

- Imran, Castillo, Diaz y Vieweg. *Processing Social Media Messages in Mass Emergency: A Survey*. ACM Computing Surveys, 47(4). https://dl.acm.org/doi/10.1145/2771588 — arXiv:1407.7071
- *Ranking of Social Media Alerts with Workload Bounds in Emergency Operation Centers*. arXiv:1809.08489
- *Supporting the Use of Social Media by Emergency Managers: Software Tools to Overcome Information Overload*.
- *Overcoming barriers to social media use through multisensor integration in emergency management systems*. International Journal of Disaster Risk Reduction (ScienceDirect).
- *Socializing in emergencies — A review of the use of social media in emergency situations*. International Journal of Information Management (ScienceDirect).
- NIST. *A Review of Social Media Use During Disaster Response and Recovery*. NIST Technical Note 2086. https://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.2086.pdf

**Doctrina institucional del PMU**

- UNGRD. *Puesto de Mando Unificado de seguimiento y monitoreo* — Portal de Gestión del Riesgo. https://portal.gestiondelriesgo.gov.co/
- Policía Nacional de Colombia. *Puesto de Mando Unificado (PMU) – PMI*. https://www.policia.gov.co/sites/default/files/descargables/18._pmu_-_pmi.pdf
- Ministerio de Salud del Ecuador. *Guía de Conformación de Puesto de Mando Unificado – PMU*, MMT2-GUIA-001 (2020) — referencia comparada de doctrina regional.
- UNGRD. *Plan Nacional de Respuesta* — organización de la Sala de Crisis por servicios de respuesta.

**Modelos y datasets**

- Meta AI. *Llama 3.1 8B Instruct Model Card*. https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
- Meta AI. *Llama 3.3 70B Instruct Model Card*. https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct
- QCRI. *HumAID: Human-Annotated Disaster Incidents Data from Twitter*. https://huggingface.co/datasets/QCRI/HumAID-all
- QCRI. *CrisisBench*. https://huggingface.co/datasets/QCRI/CrisisBench-all-lang

**Estándares y normativa**

- OASIS. *Common Alerting Protocol (CAP)*, estándar desde 2004.
- OASIS. *Emergency Data Exchange Language (EDXL)*.
- UNGRD. *Manual de Estandarización de Ayuda Humanitaria de Colombia*.
- Congreso de Colombia. *Ley 1523 de 2012* — Política Nacional de Gestión del Riesgo de Desastres.
- Congreso de Colombia. *Ley 1581 de 2012* — Protección de Datos Personales.

*El detalle completo de fuentes, con enlaces verificados y notas de investigación, se encuentra en el documento anexo `investigacion_antecedentes.md`.*

# 2. Objetivos y Alcance

> **Proyecto:** SIRENA — *Sistema de Interpretación de Reportes de Emergencia y Necesidades Automatizado*
> **Documento:** Propuesta de Proyecto de Curso — Módulo 2, Entregable 2
> **Universidad Autónoma de Occidente**

---

## 2.1 Objetivo General

> **Fortalecer la capacidad de escucha institucional frente a la comunicación ciudadana durante emergencias en Santiago de Cali, mediante un sistema de inteligencia artificial que traduzca los mensajes de la comunidad —escritos en lenguaje natural, coloquial y desestructurado— en información estructurada y verificable, de modo que el Puesto de Mando Unificado pueda incorporar el reporte ciudadano a su proceso de decisión sin depender de su procesamiento manual.**

### Sentido del objetivo

El objetivo general expresa la **finalidad** del sistema, no su implementación. Responde al problema formulado en §1.4: el canal de comunicación entre la ciudadanía y sus instituciones se satura precisamente cuando más se necesita, y esa incapacidad de escucha produce un daño operativo —reportes perdidos, respuesta tardía— y un daño social más duradero: la erosión de la confianza en el canal oficial de reporte.

En consecuencia, el propósito último del proyecto no es técnico sino comunicativo: **que lo que la comunidad ya está diciendo llegue efectivamente a quien puede actuar**. La preservación de esa confianza es lo que inscribe el proyecto en el Eje 4 de Educación, Cultura, Comunicación y Cohesión Social.

### Descomposición del enunciado

| Componente | Qué compromete |
|---|---|
| *Fortalecer la capacidad de escucha institucional* | La finalidad: intervenir sobre el canal, no sobre el fenómeno que lo satura |
| *Comunicación ciudadana durante emergencias en Cali* | El ámbito de aplicación, delimitado geográfica y situacionalmente |
| *Traducir mensajes en lenguaje natural, coloquial y desestructurado* | La naturaleza del insumo: texto real, no formularios |
| *Información estructurada y verificable* | Las dos propiedades exigidas a la salida — *verificable* implica que cada registro se presenta junto al mensaje original que lo produjo |
| *Incorporar el reporte ciudadano al proceso de decisión* | El sistema alimenta la decisión; no la sustituye |
| *Sin depender de su procesamiento manual* | El cuello de botella que se busca aliviar (§1.3.2) |

**Delimitación ética.** El objetivo dice *incorporar al proceso de decisión*, no *decidir*. SIRENA es un copiloto: produce sugerencias estructuradas que un operador humano valida antes de que se despache cualquier recurso (§1.4).

---

## 2.2 Objetivos Específicos

Los objetivos específicos descomponen el objetivo general en **capacidades funcionales**: aquello que el sistema debe ser capaz de hacer para que la escucha institucional efectivamente mejore. Están formulados en términos de la función que cumplen ante el problema, no de la tecnología que los realiza.

La implementación técnica —esquemas, modelos, módulos, contenedores— corresponde a las **tareas del capítulo 3**, que apuntan a estos objetivos. Cada objetivo declara qué tareas lo materializan, de modo que la trazabilidad *objetivo → tarea* sea explícita y verificable.

> **Criterio de formulación:** un objetivo específico debe sobrevivir a un cambio de tecnología. Si el equipo sustituyera el modelo de lenguaje, la base de datos o el marco de la interfaz, los cinco objetivos siguientes permanecerían válidos; solo cambiarían las tareas que los realizan.

---

### OE1 — Discriminar el reporte accionable del ruido comunicacional

> **Dotar al sistema de la capacidad de distinguir, dentro del flujo de mensajes ciudadanos, aquellos que constituyen un reporte útil para la respuesta institucional, separándolos de la opinión, el reenvío, la referencia a noticias y el contenido no accionable.**

| Aspecto | Definición |
|---|---|
| **Necesidad que atiende** | En un canal abierto, la mayor parte del tráfico no es un reporte. Sin discriminación previa, el volumen ahoga al receptor y reproduce el problema que se busca resolver (§1.3) |
| **Capacidad funcional** | Determinar si un mensaje es accionable, en qué momento sitúa los hechos —en curso, ya ocurridos, riesgo previsto o cita de noticia— y con qué intención se emite: solicitud de ayuda, reporte sobre terceros, **ofrecimiento de ayuda** o solicitud de información |
| **Resultado observable** | Ante un flujo mixto de mensajes, el sistema entrega al operador únicamente los accionables, clasificados por intención y momento |
| **Se materializa en** | T-02, T-03, T-12, T-14, T-15, T-17 |

*Relevancia particular:* la categoría **ofrecimiento de ayuda** convierte al sistema en un instrumento de articulación comunitaria. Durante una emergencia la ciudadanía no solo demanda: también ofrece vehículos, alojamiento y trabajo voluntario. Reconocer esa oferta es parte de la escucha.

---

### OE2 — Estructurar el contenido del reporte en información institucionalmente utilizable

> **Dotar al sistema de la capacidad de identificar, dentro de un mensaje escrito en lenguaje coloquial, qué ocurrió y qué se necesita, expresándolo en los *servicios de respuesta* con que la Estrategia de Respuesta a Emergencias de Santiago de Cali organiza la atención y asigna responsables.**

| Aspecto | Definición |
|---|---|
| **Necesidad que atiende** | El mensaje ciudadano y el registro institucional hablan lenguajes distintos. La traducción entre ambos es hoy trabajo humano y constituye el cuello de botella del proceso |
| **Capacidad funcional** | Reconocer el **tipo de evento** conforme a los escenarios de riesgo con protocolo específico, y asociar la necesidad expresada al **servicio de respuesta competente**. La asignación es **multietiqueta**: un mismo mensaje puede expresar varias necesidades y el sistema debe reconocerlas todas |
| **Resultado observable** | Cada reporte accionable llega al operador asociado al tipo de evento y al servicio o servicios de respuesta que le corresponden, sin transcripción manual |
| **Se materializa en** | T-02, T-03, T-07, T-12, T-14, T-15 |

#### Fundamento de la taxonomía

La categorización **no es una invención del equipo ni un esquema tomado de la literatura académica**. Se adopta la estructura de **servicios de respuesta** definida por la **Estrategia de Respuesta a Emergencias (ERE) de Santiago de Cali**, adoptada mediante **Decreto 4112.010.20.1002 del 29 de diciembre de 2023**, que define dieciocho servicios, cada uno con su protocolo, entidad responsable principal y entidades de apoyo.

La ERE los define como *"las acciones individuales o de orden interinstitucional que se desarrollan para permitir la atención de la comunidad afectada, el restablecimiento de servicios públicos esenciales y demás actividades que se generan como parte de la atención de la emergencia, la reconstrucción y rehabilitación"*.

De los dieciocho servicios, dieciséis corresponden a necesidades que la ciudadanía puede reportar; dos —los relativos a Evaluación de Daños y Análisis de Necesidades— son funciones institucionales. La ontología del sistema opera sobre el **subconjunto reportable**:

| Servicio de respuesta (ERE Cali) | Ejemplo de reporte ciudadano asociado |
|---|---|
| Búsqueda y Rescate | *"hay una señora atrapada en la casa que se cayó"* |
| Extinción de Incendios | *"hay fuego en el edificio de la esquina"* |
| Telecomunicaciones para la comunidad | *"no hay señal en toda la comuna"* |
| Manejo de Materiales peligrosos | *"se está derramando algo de un camión cisterna"* |
| Seguridad y Convivencia | *"están saqueando el local de la esquina"* |
| Accesibilidad y Transporte | *"la vía está bloqueada por escombros"* |
| Salud | *"mi papá se golpeó la cabeza y está sangrando"* |
| Agua potable | *"llevamos dos días sin agua en el barrio"* |
| Asistencia humanitaria | *"no tenemos nada para comer desde ayer"* |
| Alojamientos temporales | *"nos sacaron de la casa y no tenemos dónde dormir"* |
| Energía y gas | *"se cayó un poste y hay cables en la calle"* |
| Saneamiento básico | *"las aguas negras se salieron a la calle"* |
| Reencuentro familiar | *"no sé nada de mi hermana desde el temblor"* |
| Seres sintientes — Fauna doméstica | *"quedaron perros encerrados en la casa"* |
| Seres sintientes — Fauna silvestre | *"hay animales heridos en la quebrada"* |
| Manejo de Residuos sólidos en emergencias | *"hay basura acumulada hace días"* |

Cuatro consecuencias de esta decisión:

1. **La salida del sistema es directamente accionable.** Asociar un reporte a un servicio de respuesta equivale a identificar qué entidad del PMU debe atenderlo, porque la ERE asigna a cada servicio una entidad responsable principal, apoyos técnicos y entidades de apoyo.
2. **El sistema se inserta en una función institucional existente.** El servicio **E.D.A.N. — Evaluación de Daños y Análisis de Necesidades** es precisamente la función que este proyecto apoya. SIRENA no propone una capacidad nueva para el Distrito: **alimenta un servicio de respuesta que la ERE ya define, con protocolo y responsable asignados**.
3. **Valida una decisión de diseño previa.** *Seguridad y Convivencia* confirma que el dominio alterno elegido para la prueba de transferibilidad (OE5) es un servicio institucional real de Cali y no un ejemplo hipotético.
4. **La taxonomía académica pasa a rol secundario.** La clasificación HumAID —esquema de anotación de investigación en *crisis informatics*— se conserva únicamente como **capa de comparabilidad con la literatura internacional** en la evaluación (OE5), no como categorización operativa.

---

### OE3 — Situar territorialmente los reportes a partir de referencias geográficas informales

> **Dotar al sistema de la capacidad de determinar el lugar al que se refiere un reporte cuando la ubicación se expresa en el lenguaje cotidiano de los habitantes —barrios, puntos de referencia, indicaciones relativas— y no mediante direcciones formales.**

| Aspecto | Definición |
|---|---|
| **Necesidad que atiende** | Sin ubicación no hay despacho posible. La ciudadanía no reporta direcciones catastrales: reporta lugares tal como los nombra en su vida diaria |
| **Capacidad funcional** | Traducir la referencia informal a la entidad territorial correspondiente, **declarando siempre el nivel de precisión alcanzado** —exacta, barrio, comuna, ciudad o indeterminada— y absteniéndose de afirmar una precisión que el texto no sustenta |
| **Resultado observable** | Los reportes se representan sobre el territorio con su nivel de certeza explícito; los irresolubles se marcan como tales en lugar de recibir una ubicación supuesta |
| **Se materializa en** | T-06, T-16 |

*Delimitación crítica:* **el sistema nunca infiere una ubicación no sustentada en el texto.** Una ubicación inventada con apariencia de precisión es más peligrosa que una ubicación ausente, porque puede desviar recursos escasos. La resolución territorial se realiza por medios deterministas y verificables, no generativos (§1.6).

---

### OE4 — Entregar la información al operador de forma verificable y desplegable

> **Poner la información estructurada a disposición de quien decide, de manera que cada dato pueda contrastarse contra el mensaje original antes de actuar, y garantizar que el sistema pueda instalarse y operarse en la institución de forma reproducible.**

| Aspecto | Definición |
|---|---|
| **Necesidad que atiende** | Un sistema de apoyo a decisiones críticas que no permite verificar lo que afirma no puede usarse con responsabilidad. La verificabilidad es la condición que hace posible el uso del sistema como apoyo a la decisión (§1.4) |
| **Capacidad funcional** | Presentar cada registro estructurado **junto al mensaje original completo que lo produjo**, permitir al operador **ordenar y filtrar los reportes según los criterios que él determine**, y proteger los datos personales contenidos en los mensajes conforme a la Ley 1581 de 2012 |
| **Resultado observable** | El operador puede validar o rechazar cada registro contrastándolo contra su texto de origen, sin abandonar la interfaz. El sistema completo se instala y ejecuta en un entorno distinto al de desarrollo |
| **Se materializa en** | T-10, T-13, T-17, T-18, T-19, T-20, T-21, T-22, T-23, T-28, T-30 |

*Delimitación ética:* este objetivo es el que hace operativa la definición del sistema como **copiloto y no como decisor**. El mecanismo es deliberadamente simple: el mensaje original viaja con el registro, de modo que la evidencia es completa y no puede alucinarse, por tratarse de un dato de entrada y no de una salida del modelo (§1.5.2).

---

### OE5 — Determinar la confiabilidad del sistema, sus límites y su transferibilidad

> **Establecer en qué medida el sistema cumple las capacidades anteriores, en qué condiciones falla, y hasta qué punto la solución es aplicable a otros contextos de reporte ciudadano distintos de la emergencia por desastre.**

| Aspecto | Definición |
|---|---|
| **Necesidad que atiende** | Un sistema destinado a apoyar decisiones críticas debe poder declarar qué sabe hacer y qué no. Sin esa caracterización, el operador no tiene base para decidir cuánto confiar |
| **Capacidad funcional** | Contrastar el comportamiento del sistema contra una referencia construida y validada por el equipo; caracterizar sus modos de error; contrastar el modelo de escala accesible frente a uno de mayor escala; y verificar que el sistema opera en un dominio distinto —convivencia y seguridad ciudadana— **sustituyendo la configuración del dominio y no el sistema** |
| **Resultado observable** | Un informe que declara, por cada capacidad, dónde el sistema es confiable y dónde no; y una demostración de que el cambio de contexto de aplicación no exige reconstruir la solución |
| **Se materializa en** | T-04, T-07, T-08, T-09, T-24, T-25, T-26, T-27, T-31 |

*Alcance de la evaluación:* el propósito es **caracterizar y documentar**, no superar un umbral predefinido. Los modos de error —ubicación inferida sin sustento, servicio de respuesta mal asignado, necesidades no detectadas en mensajes multietiqueta, falsos positivos en la compuerta— tienen tanto valor documental como el desempeño agregado, porque son los que determinan qué puede delegarse al sistema y qué debe permanecer en manos del operador.

---

### 2.2.1 Tabla resumen

| # | Capacidad funcional | Pregunta que responde ante el problema | Tareas que lo materializan |
|---|---|---|---|
| **OE1** | Discriminar lo accionable del ruido | *¿Qué merece la atención del operador?* | T-02, T-03, T-12, T-14, T-15, T-17 |
| **OE2** | Estructurar el contenido del reporte | *¿Qué ocurrió, qué se necesita y a quiénes afecta?* | T-02, T-03, T-07, T-12, T-14, T-15 |
| **OE3** | Situar territorialmente el reporte | *¿Dónde hay que ir?* | T-06, T-16 |
| **OE4** | Entregar de forma verificable y desplegable | *¿Puedo confiar en este dato y actuar sobre él?* | T-10, T-13, T-17 a T-23, T-28, T-30 |
| **OE5** | Determinar confiabilidad, límites y transferibilidad | *¿Hasta dónde funciona esto, y sirve en otro contexto?* | T-04, T-07, T-08, T-09, T-24 a T-27, T-31 |

**Cómo se articulan con el objetivo general.** Escuchar no es un acto único, sino una secuencia de operaciones: *oír entre el ruido* (OE1), *comprender lo dicho* (OE2), *saber dónde ocurre* (OE3), *poder responder por lo que se afirma* (OE4) y *conocer los propios límites* (OE5). Los cinco objetivos descomponen la capacidad de escucha institucional en sus operaciones constitutivas.

> **Hechos, no juicios.** El sistema estructura lo que el mensaje dice —qué se reporta, a qué servicio institucional compete y dónde ocurre— y lo entrega junto al texto que lo sustenta. La valoración de esos hechos, su prioridad y el orden de atención son juicio experto en gestión del riesgo y competencia de las instancias que la normativa faculta para ello.

---

## 2.3 Alcance funcional del sistema

El sistema se descompone en cinco módulos, que corresponden a los frentes de trabajo paralelos del equipo de cuatro integrantes.

| Módulo | Responsabilidad | Objetivos que sirve |
|---|---|---|
| **M1 — Ingesta** | Recepción de mensajes desde fuentes intercambiables; normalización y protección de datos personales | OE4 |
| **M2 — Interpretación** | Discriminación de lo accionable y estructuración del contenido del reporte | OE1, OE2 |
| **M3 — Ubicación** | Resolución territorial de referencias geográficas informales; detección de reportes duplicados | OE1, OE3 |
| **M4 — Persistencia y servicio** | Almacenamiento de los registros y exposición para consulta | OE4 |
| **M5 — Presentación** | Interfaz de operador: bandeja de reportes con ordenamiento y filtros configurables, territorio, y mensaje original junto a cada registro | OE4 |

Transversalmente: **evaluación** (referencia, experimentos, informe) y **empaquetado** (despliegue, pruebas, documentación).

---

## 2.4 Matriz de Alcance

### 🟢 Included — Compromiso del proyecto

Elementos cuya ausencia implica que el proyecto **no está completo**.

| Categoría | Elemento |
|---|---|
| **Modelo** | Integración de `Llama-3.1-8B-Instruct` vía API de inferencia |
| **Modelo** | Prompt de extracción estructurada con salida JSON forzada y ejemplos *few-shot* en español coloquial |
| **Modelo** | Capa de validación, reintento y reparación de salidas no conformes |
| **Datos** | Corpus *gold standard* de mensajes sintéticos anotado manualmente por el equipo |
| **Datos** | Ontología de dominio para emergencias, basada en los **servicios de respuesta y los escenarios de riesgo de la ERE de Cali** (Decreto 1002 de 2023) |
| **Datos** | Anonimización de datos personales en preprocesamiento (Ley 1581 de 2012) |
| **Ingesta** | Interfaz de fuentes intercambiables con al menos dos implementaciones: reproductor del corpus y una fuente en vivo (Bluesky o Telegram) |
| **Procesamiento** | Módulo determinista de normalización geográfica con *gazetteer* de Cali |
| **Interfaz** | Tablero con bandeja de reportes, ordenamiento y filtros configurables por el operador, mapa, y visualización del mensaje original junto a cada registro estructurado |
| **Servicio** | API REST para ingesta y consulta |
| **Despliegue** | Contenedorización con Docker — despliegue en un solo comando |
| **Calidad** | Suite de pruebas sobre interpretación, validación y ubicación |
| **Evaluación** | Informe con desempeño por capacidad, análisis de modos de error, comparación entre escalas de modelo y prueba de transferibilidad |
| **Documentación** | `README`, Model Card del sistema, documentación de la API y manual de despliegue |
| **Gestión** | Repositorio GitHub público y tablero Kanban con la totalidad de los tickets |

### 🟡 Nice to have — Deseable, no comprometido

Elementos que se abordarán **solo si el avance frente a la ruta crítica lo permite**. Su ausencia no afecta la completitud del proyecto.

| Elemento | Objetivo que reforzaría | Condición para abordarlo |
|---|---|---|
| Integración con la API de X (Twitter) bajo modelo *pay-per-use* | OE4 | Disponibilidad de presupuesto (~USD 10) y holgura en cronograma |
| Agrupamiento de reportes duplicados por similitud semántica | OE1 | Detección de duplicados básica ya funcionando |
| Marca de sospecha de desinformación sobre contenido no verificable | OE1 | Corpus con suficientes ejemplos etiquetados de rumor |
| Emparejamiento entre ofrecimientos y solicitudes de ayuda | OE1 | Interpretación estable y tablero funcional |
| Transcripción de notas de voz para el canal de audio | OE2 | Canal de texto completamente resuelto |
| Optimización de costo por reutilización de contexto | — | Comportamiento base ya caracterizado |
| Comparación con un modelo alternativo de escala similar (Qwen, Mistral) | OE5 | Comparación 8B/70B concluida |
| Exportación conforme a los estándares CAP o HXL | OE4 | Esquema interno estabilizado |
| Autenticación y gestión de roles en el tablero | OE4 | Funcionalidad principal completa |

### 🔴 Not included — Exclusiones explícitas

Elementos **fuera del alcance**, con su justificación. Se declaran para prevenir expectativas no acordadas.

| Exclusión | Justificación |
|---|---|
| **Entrenamiento o *fine-tuning* del modelo base** | El proyecto evalúa la capacidad *zero/few-shot* de un modelo preentrenado. El ajuste fino exige volumen de datos y cómputo fuera del alcance, y contradice el argumento central del proyecto: eliminar el costo de reentrenamiento por evento (§1.6) |
| **Recolección manual de datos reales en tiempo real durante una emergencia** | Inviable y éticamente inadecuado: implicaría depender de la ocurrencia de un desastre durante el plazo del proyecto |
| **Integración con sistemas institucionales en producción** (línea 123, sistemas del PMU) | Requiere convenios y credenciales institucionales fuera del ámbito académico |
| **Integración con WhatsApp Business API** | Exige verificación empresarial, incompatible con el plazo. Telegram actúa como sustituto metodológico (§1.9.4) |
| **Despliegue local del modelo (*self-hosting*)** | El equipo no dispone de hardware con GPU. Llama 3.3 70B exige del orden de 140 GB de VRAM en FP16 (§1.9.2) |
| **Hardware dedicado o infraestructura en la nube de pago** | Restricción presupuestal declarada; el proyecto se ejecuta sobre cuotas gratuitas |
| **Despacho automático de recursos o toma autónoma de decisiones** | **Exclusión ética deliberada**, no una limitación técnica. El sistema es copiloto, no decisor (§1.4, OE4) |
| **Valoración de gravedad, prioridad u orden de atención** | Son juicio experto en gestión del riesgo y dependen además de la capacidad de respuesta disponible, cuya valoración compete al Consejo Municipal de Gestión del Riesgo. El sistema estructura hechos; la valoración es del operador |
| **Validación de campo con operadores reales del PMU** | Fuera del alcance académico y del plazo; declarada como limitación del estudio (§1.3.3) |
| **Procesamiento de imágenes o video adjuntos a los reportes** | El proyecto es de procesamiento de lenguaje natural; el análisis multimodal constituye una línea de trabajo futuro |
| **Soporte de idiomas distintos del español** | El aporte del proyecto es precisamente el trabajo sobre español coloquial colombiano |
| **Aplicación móvil nativa** | El tablero web responde al usuario destinatario, que opera desde una sala de mando |
| **Verificación factual de los reportes contra fuentes externas** | El sistema estructura lo que el mensaje dice y lo entrega junto a su texto de origen, pero no verifica si lo dicho es cierto: excedería el alcance y requeriría fuentes de verdad en tiempo real |

---

## 2.5 Criterios de aceptación del proyecto

El proyecto se considera **terminado** cuando se cumplen simultáneamente:

1. Las cinco capacidades funcionales están implementadas y son demostrables sobre un flujo de reportes.
2. El sistema completo se despliega con un solo comando en una máquina limpia.
3. La suite de pruebas ejecuta en verde.
4. El tablero procesa un flujo de extremo a extremo y presenta cada registro estructurado junto al mensaje original que lo produjo.
5. El repositorio y el tablero Kanban están públicos, con la totalidad de los tickets cerrados o justificados.
6. El informe de evaluación documenta el comportamiento del sistema, sus modos de error y sus límites.

> **Sobre el resultado de la evaluación.** El proyecto no condiciona su éxito a que el sistema alcance un nivel de desempeño determinado. Su compromiso es **construir el sistema, medir su comportamiento con un método explícito y documentar honestamente lo que se observe**. Un desempeño inferior al esperado, correctamente caracterizado y explicado, constituye un hallazgo válido sobre los límites de los modelos de pesos abiertos y escala accesible aplicados al español coloquial —precisamente el vacío identificado en §1.6—. Lo que sí constituiría un incumplimiento es no poder medirlo ni explicarlo.

---

## 2.6 Supuestos

El alcance declarado es válido bajo los siguientes supuestos. Su incumplimiento obliga a replantearlo.

| # | Supuesto | Riesgo si falla | Plan de contingencia |
|---|---|---|---|
| S1 | Las cuotas gratuitas de LLM se mantienen vigentes durante el plazo del proyecto | Bloqueo de la capacidad de interpretación | Migrar a Hugging Face Inference Providers (PRO, USD 9) u otro proveedor compatible con la API de OpenAI |
| S2 | `Llama-3.1-8B-Instruct` continúan disponibles en el proveedor | Cambio forzado de modelo base | La capa de interpretación se abstrae del proveedor; el modelo es sustituible por configuración |
| S3 | El corpus sintético refleja suficientemente el registro del mensaje ciudadano real | Conclusiones no generalizables | Contraste cualitativo con el flujo en vivo; se declara como limitación del estudio |
| S4 | Los cuatro integrantes mantienen disponibilidad durante el plazo del módulo | Retraso en la ruta crítica | Los módulos M1–M5 tienen interfaces definidas y son reasignables |
| S5 | Existe una fuente de datos geográficos de barrios y comunas de Cali de acceso abierto | Degradación del alcance de OE3 | Construcción manual de un *gazetteer* reducido a las comunas de mayor afectación |

---

## 2.7 Trazabilidad: problema, objetivos y realización

| Problema identificado (§1.3) | Objetivo que lo atiende | Módulos | Evidencia de cumplimiento |
|---|---|---|---|
| El ruido domina el canal y satura al receptor | **OE1** | M2 | Flujo mixto filtrado, clasificado por intención y momento |
| La traducción del lenguaje ciudadano al institucional es trabajo manual | **OE2** | M2 | Reportes categorizados conforme a taxonomía reconocida |
| Las referencias geográficas informales no son resolubles automáticamente | **OE3** | M3 | Reportes situados con nivel de precisión declarado |
| El operador no puede verificar lo que el sistema afirma | **OE4** | M1, M4, M5 | Cada registro se presenta junto al mensaje original que lo produjo |
| Se desconoce hasta dónde es confiable y extensible la solución | **OE5** | Transversal | Informe de límites y prueba de cambio de dominio |

---

*Las capacidades aquí declaradas se realizan mediante las 32 tareas del capítulo 3, estimadas en Story Points y organizadas por dependencias, y se gestionan como tickets con criterios de aceptación en el capítulo 5.*

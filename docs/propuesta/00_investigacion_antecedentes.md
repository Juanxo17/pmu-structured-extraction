# Investigación de Antecedentes — Agente de Orquestación PMU

**Proyecto:** Sistema de extracción estructurada de reportes ciudadanos para Puestos de Mando Unificado
**Eje temático:** 4 — Educación, Cultura, Comunicación y Cohesión Social
**Curso:** Diseño y Desarrollo de Proyectos de IA (DDPIA) — Módulo 2
**Universidad Autónoma de Occidente**
**Fecha de la investigación:** 30 de agosto de 2026
**Equipo:** 4 integrantes (perfil: desarrollo)

> Documento de trabajo. Todas las cifras y precios fueron verificados vía búsqueda web en la fecha indicada;
> los tiers comerciales cambian con frecuencia y **deben re-verificarse antes de la entrega final**.

---

## 1. Caso motivador: terremoto del 10 de agosto de 2026

### 1.1 El evento

| Dato | Valor |
|---|---|
| Fecha y hora | Lunes 10 de agosto de 2026, 7:34 a.m. |
| Magnitud | 7.4 |
| Epicentro | San José del Palmar, Chocó |
| Profundidad | 96 km |
| Fuente oficial | Servicio Geológico Colombiano (SGC) |
| Alcance de percepción | Bogotá, Medellín, Cali, Pereira, Manizales |
| Réplicas | 5 réplicas por encima de magnitud 3.0 |
| Calificación | Sismo más fuerte percibido en Colombia en la última década |

**Impacto en Cali (cifras iniciales del boletín distrital):** 28 fallecidos, 380 lesionados atendidos en centros médicos, 26 edificaciones colapsadas en zona urbana.

**Impacto nacional (a 11 de agosto):** más de 130 muertos, 570 heridos, viviendas y vías dañadas, aeropuertos cerrados.

> ⚠️ Las cifras evolucionaron durante los días siguientes. Para el documento formal usar el **repositorio oficial de información del Terremoto de Cali** publicado por la Alcaldía y citar la fecha de corte.

### 1.2 Respuesta institucional y activación del PMU

El Gobierno instaló Puestos de Mando Unificado el mismo 10 de agosto. En Cali el PMU consolidó los informes de afectación y coordinó operaciones, con **dos reportes diarios (8:00 a.m. y 5:00 p.m.)**. Entidades participantes registradas:

- Cuerpo de Bomberos — 260 voluntarios
- Defensa Civil — 115 operativos
- Cruz Roja — 101 socorristas
- Rescatistas nacionales — 92 especialistas
- Secretaría de Salud Pública Distrital
- Ejército Nacional

El 15 de agosto, el director de operaciones de emergencias de la Cruz Roja Valle advirtió en el PMU que la recuperación "nos va a durar entre dos y cuatro años". El alcalde instaló posteriormente un **nuevo PMU dedicado a la fase de reconstrucción**.

### 1.3 Canales de reporte ciudadano habilitados

| Canal | Número | Naturaleza |
|---|---|---|
| Emergencias | 123 | Voz |
| Bomberos | 119 | Voz |
| Cruz Roja | 132 | Voz |
| Salud mental | 106 | Voz |
| **WhatsApp — reportes urbanos** | **310 229 97 08** | **Texto / multimedia** |

### 1.4 🎯 Evidencia directa del problema

Este es el hallazgo más importante de la investigación. Las autoridades distritales, en su propio boletín, emitieron dos instrucciones a la ciudadanía:

1. **Limitar las llamadas telefónicas** "para evitar el colapso de las antenas repetidoras", y reservar las llamadas de emergencia exclusivamente para situaciones de peligro real o rescate, **con el fin de evitar la saturación de los canales de socorro**.
2. **Abstenerse de difundir material audiovisual o mensajes de texto no verificados.**

**Lectura para el proyecto:** la institución reconoce oficialmente que (a) el canal de voz se satura y por eso *empuja el reporte hacia canales de texto* — habilitando un WhatsApp para reportes urbanos —, y (b) circula desinformación en esos mismos canales. Es decir: **el problema que nuestro sistema aborda no es hipotético ni inferido; está declarado por la autoridad competente en un documento público durante la emergencia.**

Adicionalmente, la saturación hospitalaria llegó al 100 % de capacidad: cuando el recurso disponible es menor que la demanda, la calidad de la información con que se decide determina resultados en vidas, y cada reporte perdido pesa más.

Esto ancla el proyecto en el Eje 4: el objeto de estudio es **el canal comunicativo entre ciudadanía e institución**, su saturación, su ruido y su confiabilidad — no el fenómeno geológico.

---

## 2. Antecedentes académicos y estado del arte

### 2.1 Generación 1 — Crowdsourcing manual (2010)

**Ushahidi / Haití 2010.** Plataforma de crisis mapping usada tras el terremoto de Haití. Recibió **3.584 reportes ciudadanos**, visualizados ~500.000 veces, permitiendo a la población reportar su ubicación y sus necesidades sobre un mapa.

- *Aporte:* demostró que la ciudadanía **sí** produce información situacional valiosa en crisis.
- *Limitación:* la estructuración de cada reporte era **100% manual**, realizada por voluntarios digitales distribuidos. No escala ni sostiene latencia baja.

### 2.2 Generación 2 — Clasificación supervisada (2013–2020)

**AIDR (Artificial Intelligence for Disaster Response), QCRI.** Plataforma de clasificación automática de microblogs de crisis en categorías definidas por el usuario ("necesidades", "daños", etc.), con un esquema humano-máquina: humanos etiquetan una muestra en vivo y el modelo generaliza.

- *Aporte:* introdujo el aprendizaje automático al triage de crisis.
- **Limitación crítica — este es nuestro gap:** requiere **etiquetado humano de miles de mensajes por cada evento nuevo**. Ante un desastre inédito el modelo arranca en frío y el costo de re-entrenamiento recae sobre el personal de emergencia, justo cuando está más saturado. Además clasifica (asigna una etiqueta) pero **no extrae** los campos estructurados que un PMU necesita para despachar.

### 2.3 Generación 3 — LLMs para gestión de desastres (2024–2026)

Línea de investigación activa y reciente. Trabajos relevantes localizados:

| Trabajo | Contribución | Uso para nosotros |
|---|---|---|
| **Harnessing Large Language Models for Disaster Management: A Survey** | Revisión integral del uso de LLMs en respuesta, preparación, recuperación y mitigación | Marco general de la sección de antecedentes |
| **LLMs for Geolocation Extraction in Humanitarian Crisis Response** (Cafferata, Demarco, Kalimeri, Mejova, Beiró, arXiv 2602.08872) | Extracción de topónimos + geocodificación con agente LLM | **Referencia metodológica directa** — ver 2.4 |
| **Extracting Disaster Impacts and Impact Related Locations in Social Media Posts Using LLMs** (arXiv 2511.21753) | Extracción conjunta de impacto y ubicación desde posts sociales | Precedente de nuestro esquema multi-campo |
| **CrisisSense-LLM** | Instruction fine-tuning para clasificación **multi-etiqueta** de posts | Sustenta que un solo mensaje contiene varias necesidades simultáneas |
| **LLMs for Causal Relations Extraction in Social Media: A Validation Framework for Disaster Intelligence** (arXiv 2605.11348) | Extracción de relaciones causales (víctimas, daño físico, disrupción de infraestructura, impactos en cascada) + framework de validación | Modelo de **framework de validación**, aplicable a nuestra capa de auditoría |
| **Enhanced earthquake impact analysis based on social media texts via LLM** (ScienceDirect) | Análisis de impacto sísmico vía LLM sobre texto social | Antecedente específico para sismos |
| **LLM-guided Semi-Supervised Approaches for Social Media Crisis Data Classification** (arXiv 2605.08448) | LLM como generador de supervisión débil | Justifica nuestra estrategia de dataset sintético |

**Consenso de la literatura:** los LLMs **superan a los modelos NER tradicionales** en extracción de ubicaciones desde datos sociales de desastre, y lo hacen **sin requerir reentrenamiento específico por evento**.

### 2.4 Hallazgos cuantitativos citables (Cafferata et al., 2025)

Estudio de extracción de topónimos en documentos humanitarios, con geocodificación posterior:

- Modelos evaluados: GPT-5, GPT-4o, GPT-4o mini, DeepSeek (reasoning y chat), Claude Sonnet 4.5, Claude Haiku 4.5. Baselines: SpaCy, RoBERTa y modelos fine-tuned.
- **GPT-4o con salida JSON: precisión exacta 0.87 · F1 0.84**
- **GPT-5 con salida Markdown: recall parcial 0.99 · F1 parcial 0.92**
- El **agente de geocodificación** elevó la precisión exacta a **0.88 frente a 0.69** de un baseline basado en reglas.
- Equidad: paridad casi total entre continentes y niveles de ingreso, mejorando sistemas previos sesgados hacia regiones occidentales — aunque persisten sesgos residuales heredados de **GeoNames** y alta tasa de falsos descubrimientos en Europa.
- Limitaciones reportadas: topónimos no estándar o ambiguos; **el desempeño depende del formato de salida elegido (JSON vs. Markdown)**.
- Trabajo futuro señalado por los autores: **optimización supervisada de prompts, extensión a textos multilingües y contextos de bajos recursos**, y auditoría algorítmica continua.

**Implicaciones directas para nuestro diseño:**

1. La arquitectura **extracción por LLM → geocodificación determinista posterior** no es una decisión nuestra improvisada: es el patrón validado por la literatura, y el paso de geocodificación aporta +19 puntos de precisión. Confirma la regla de que **el LLM no debe emitir coordenadas**.
2. F1 ≈ 0.84–0.92 es el **rango de referencia del estado del arte** con modelos frontier. Nuestra hipótesis de F1 ≥ 0.80 con Llama-3.1-8B queda calibrada de forma realista y defendible.
3. El formato de salida es una **variable experimental**, no un detalle. Podemos incluir un objetivo específico que compare JSON estricto vs. otros formatos.
4. Los autores nombran explícitamente "extensión a contextos multilingües y de bajos recursos" como gap abierto. **Español coloquial caleño con toponimia informal es exactamente ese gap.** Es el argumento de originalidad del proyecto.

### 2.5 🕳️ Formulación del gap

> La literatura de LLMs para desastres está dominada por **inglés** y por **modelos propietarios frontier** (GPT-4o/GPT-5, Claude). Los datasets de referencia del área (HumAID) son **exclusivamente en inglés**. No se localizó trabajo que evalúe **modelos open-weights de escala accesible (Llama 3.x, 8B) sobre reportes ciudadanos en español coloquial colombiano, con toponimia informal urbana (barrios, comunas, puntos de referencia no catalogados), bajo restricciones de despliegue de bajo costo y con una taxonomía transferible entre dominios.**

Ese es el vacío que el proyecto ocupa. Es específico, es verificable y es alcanzable en el alcance del curso.

---

## 3. Datasets de referencia

### 3.1 Disponibles en Hugging Face (QCRI — Qatar Computing Research Institute)

| Dataset | Contenido | Idioma | Enlace |
|---|---|---|---|
| `QCRI/HumAID-all` | 77.196 tweets anotados manualmente, 19 desastres (2016–2019): terremotos, huracanes, incendios, inundaciones. 11 clases | **Solo inglés** | huggingface.co/datasets/QCRI/HumAID-all |
| `QCRI/HumAID-event-type` | Variante segmentada por tipo de evento | Inglés | huggingface.co/datasets/QCRI/HumAID-event-type |
| `QCRI/CrisisBench-all-lang` | Consolidado de CrisisLex26, CrisisLex6, CrisisNLP, SWDM2013, ISCRAM13, DRD, DSM, CrisisMMD y AIDR | **Multilingüe** | huggingface.co/datasets/QCRI/CrisisBench-all-lang |

HumAID es el mayor dataset de crisis informatics existente.

### 3.2 Taxonomía operativa: los servicios de respuesta del SNGRD

> **Hallazgo posterior a la investigación inicial.** Existe una taxonomía **institucional colombiana** para clasificar necesidades en emergencia, y es preferible a cualquier esquema académico como categorización operativa del sistema.

**Fuente aplicable al proyecto: la Estrategia de Respuesta a Emergencias (ERE) de Santiago de Cali**, adoptada por **Decreto 4112.010.20.1002 del 29 de diciembre de 2023** ("Por el cual se adopta la actualización de la Estrategia de Respuesta a Emergencias en el Distrito Especial Deportivo, Cultural, Turístico, Empresarial y de Servicios de Santiago de Cali"), publicada el 08/11/2024. Documento de 185 páginas. ✅ **Listado extraído del documento oficial.**

### Definiciones textuales (ERE Cali, p. 43)

> **SERVICIOS DE RESPUESTA:** "se definen las acciones individuales o de orden interinstitucional que se desarrollan para permitir la atención de la comunidad afectada, el restablecimiento de servicios públicos esenciales y demás actividades que se generan como parte de la atención de la emergencia, la reconstrucción y rehabilitación."

> **FUNCIONES DE SOPORTE:** "corresponden a actividades políticas, administrativas, técnicas de logística que permiten articular, armonizar y desarrollar los servicios de respuesta."

Roles definidos por entidad: **Responsable (R)** — ejecuta el servicio y solicita apoyo; **Apoyos Técnicos (AA)** — entidades no operativas que asesoran la toma de decisiones; **Apoyos (A)** — entran en escena cuando el responsable lo solicita.

### Los 18 servicios de respuesta de Cali (Tabla 8, p. 44)

| Letra | Servicio de respuesta | ¿Reportable por la ciudadanía? |
|---|---|---|
| A | Búsqueda y Rescate | ✅ |
| B | Extinción de Incendios | ✅ |
| C | Telecomunicaciones para la comunidad | ✅ |
| D | Manejo de Materiales peligrosos | ✅ |
| E | Seguridad y Convivencia | ✅ |
| F | Accesibilidad y Transporte | ✅ |
| G | Salud | ✅ |
| H | Agua potable | ✅ |
| I | Asistencia humanitaria | ✅ |
| J | Alojamientos temporales | ✅ |
| K | Energía y gas | ✅ |
| L | Saneamiento básico | ✅ |
| M | Reencuentro familiar | ✅ |
| N | Seres sintientes — Fauna doméstica | ✅ |
| O | Seres sintientes — Fauna silvestre | ✅ |
| P | **E.D.A.N.** (Evaluación de Daños y Análisis de Necesidades) | ⚠️ Función institucional |
| Q | E.D.A.N. de Cambio Climático desde la órbita de la G.R.D. | ⚠️ Función institucional |
| R | Manejo de Residuos sólidos en emergencias | ✅ |

La ERE adjunta **dieciocho (18) protocolos de servicio de respuesta**, representados por letras (Tablas 24 a 41, pp. 95–113), cada uno con objetivo, alcance, entidades participantes, áreas de servicio y entidad responsable principal.

### Las 6 funciones de soporte (mismas tablas)

| Letra | Función de soporte |
|---|---|
| S | Información pública |
| T | Gestión de la información |
| U | Planeación |
| V | Logística de soporte operacional |
| W | Aspectos Jurídicos |
| X | Aspectos financieros |

### Niveles de emergencia (§7.1 y Tabla 7, pp. 41–42)

Santiago de Cali define **3 niveles de emergencia**, clasificados cruzando tres criterios: **características del evento**, **afectación** y **capacidad de respuesta**.

| Nivel | Características del evento | Afectación | Capacidad de respuesta |
|---|---|---|---|
| **1** | **Baja** — evento inminente o que se materializa con poca velocidad, intensidad o expansión; posibilidad de transformación baja y riesgos conexos bajos | **Baja** — sin afectaciones o daños bajos frente a las condiciones normales; afectación en un **punto específico** del Distrito | **Suficiente** — la Administración Distrital puede manejar la emergencia, prestar los servicios de respuesta y desempeñar las funciones de soporte; no requiere apoyo de nivel superior |
| **2** | **Moderada** — velocidad, intensidad, expansión y capacidad de transformación moderadas; riesgos conexos identificables y controlables | **Moderada** — daños y pérdidas significativos; afectación **extendida en el ámbito territorial sin sobrepasarlo** | **Insuficiente** — capacidad insuficiente de la Administración Distrital; **se declara calamidad pública** |
| **3** | **Alta** | **Alta** — daños que afectan completamente la normalidad del territorio, **comprometiendo la gobernabilidad local**; afectación en todo el Distrito o parte sustancial | **Insuficiente** — capacidad muy limitada; **se requiere el apoyo de la Gobernación del Valle del Cauca** |

La §7.2 vincula el nivel con la activación: *"Basados en el nivel de la emergencia, las características del evento, la afectación y las capacidades de respuesta se deben activar los actores competentes, los servicios de respuesta y las funciones de soporte"*.

### Cómo se determina si la capacidad es suficiente o insuficiente

La ERE **no define un umbral medible**: es un juicio institucional, construido con tres piezas.

1. **Oferta — inventarios de capacidades.** La ERE (p. 43) indica que hay que considerar *"cuáles son los recursos, cuál será la forma de administrarlos y cómo se usarán las instalaciones, equipos y servicios"*, y concluye que *"es necesario que cada organismo y entidad mantenga actualizado un inventario de sus capacidades"*.
2. **Demanda — el servicio E.D.A.N.** Evaluación de Daños y **Análisis de Necesidades** produce la medida de lo que se requiere.
3. **Juicio — el CMGRD.** La ERE (p. 55) señala que la información *"es necesaria para la toma de decisiones, la solicitud de apoyo y el manejo de la situación; así mismo, apoya el desarrollo de acciones como la elaboración de reportes de situación, comunicados de prensa y **la declaratoria o no de calamidad pública**"*. La declaratoria es un acto administrativo, no el cruce de un umbral.

**Consecuencia para el proyecto — y es el argumento de pertinencia más fuerte disponible:** de las dos entradas del juicio, la de **capacidades** está razonablemente resuelta (inventarios institucionales, actualizables en frío). La de **necesidades** no lo está: depende de consolidar en tiempo real lo que ocurre en el territorio, que es justamente la información que llega desestructurada por los canales ciudadanos. El cuello de botella del proyecto coincide con el de la decisión institucional más importante de una emergencia.

**Consecuencia sobre el alcance:** el sistema **no calcula un orden de atención**. Hacerlo exigiría conocer la capacidad disponible en cada momento, dato que no reside en los mensajes ciudadanos y cuya valoración compete al CMGRD. El sistema extrae y entrega los indicadores de severidad —gravedad, urgencia, riesgo vital, separados conforme a **CAP**— y el operador ordena y filtra según su criterio.

**Otros aportes de la ERE al diseño:**

- **Vocabulario institucional.** *Afectación* y *capacidad de respuesta* son los términos con que el Distrito razona sobre emergencias; usarlos alinea el sistema con el lenguaje del PMU.
- **Agregación territorial.** La gradación de la afectación (punto específico → extendida sin sobrepasar → todo el Distrito) sirve para la vista agregada del tablero: concentración de reportes por comuna.
- **Las redes sociales ya son canal institucional.** En los protocolos por escenario, los canales de alarma incluyen *"medios de comunicación y redes sociales oficiales"* junto a radiocomunicaciones, llamada telefónica y **mensajería instantánea**.
- **El reporte comunitario está tipificado.** Entre las acciones esperadas de la comunidad figuran la *"primera respuesta comunitaria"* y el *"reporte inicial al CMGRD"*, con una **cadena de llamado comunitaria** paralela a la institucional. El ciudadano que reporta no es un actor informal para la ERE.

### 🎯 Hallazgo de mayor valor: SIRENA es un apoyo al servicio E.D.A.N.

El servicio **P — Evaluación de Daños y Análisis de Necesidades** es, literalmente, la función institucional que este proyecto automatiza parcialmente. El sistema no inventa una función nueva: **alimenta un servicio de respuesta que la ERE de Cali ya define, con entidad responsable y protocolo asignados**. Esto ancla el proyecto en la estructura institucional real y debe declararse explícitamente en el documento.

**Nota de diseño:** los servicios P y Q son funciones institucionales, no necesidades que un ciudadano reporte. La ontología del sistema debe distinguir el **subconjunto reportable por la ciudadanía** (16 servicios) del conjunto completo, para no forzar al modelo a clasificar en categorías que nunca aparecerán en un mensaje.

**Otras validaciones de diseño:** los servicios N y O (*seres sintientes*) respaldan incluir animales en la población afectada; **E — Seguridad y Convivencia** confirma que el dominio alterno de la prueba de transferibilidad es un servicio institucional real de Cali, no un ejemplo inventado; **M — Reencuentro familiar** corresponde a la clase *"Missing or found people"* de HumAID.

**Enlaces:**
- [Reglamentación de políticas de gestión del riesgo — Alcaldía de Cali (descarga del Decreto 1002 y de la ERE)](https://www.cali.gov.co/gestiondelriesgo/publicaciones/146871/reglamentacion-de-las-politicas-de-gestion-del-riesgo/)
- [Estrategia de respuesta a emergencias de Santiago de Cali — repositorio UNGRD](http://repositorio.gestiondelriesgo.gov.co/handle/20.500.11762/38766)
- [ENRE nacional — Portal de Gestión del Riesgo](https://portal.gestiondelriesgo.gov.co/Paginas/Estrategia-Nacional-para-la-Respuesta-a-Emergencias-ENRE.aspx)
- [Manual de Estandarización de Ayuda Humanitaria, Resolución UNGRD 1808 de 2013 (PDF)](https://portal.gestiondelriesgo.gov.co/Documents/Manuales/Manual_de_Estandarizacion_AHE_de_Colombia.pdf)

*Marco normativo de respaldo: Ley 1523 de 2012 (arts. 2, 5, 6, 14, 15, 19, 28, 29, 35, 37), citada en los considerandos del Decreto 1002 de 2023.*

### 3.3 Taxonomía académica de HumAID (10+1 categorías) — capa de comparabilidad

**Rol en el proyecto:** no es la categorización operativa, sino la **capa de comparabilidad con la literatura internacional**. Mantener una tabla de correspondencia entre servicios de respuesta y clases HumAID permite situar los resultados frente al estado del arte:

1. Caution and advice — *Precaución y recomendaciones*
2. Sympathy and support — *Solidaridad y apoyo*
3. Requests or urgent needs — *Solicitudes o necesidades urgentes*
4. Displaced people and evacuations — *Personas desplazadas y evacuaciones*
5. Injured or dead people — *Personas heridas o fallecidas*
6. Missing or found people — *Personas desaparecidas o encontradas*
7. Infrastructure and utility damage — *Daños en infraestructura y servicios*
8. Rescue, volunteering, or donation effort — *Rescate, voluntariado o donaciones*
9. Other relevant information — *Otra información relevante*
10. Not humanitarian — *No humanitario* (→ alimenta nuestra compuerta `es_reporte_accionable`)

> Nota de diseño: la categoría 8 (voluntariado/donaciones) valida el campo `intencion = ofrece_ayuda` propuesto. La categoría 10 valida la compuerta de filtrado. La taxonomía de HumAID **respalda empíricamente el esquema que diseñamos**.

### 3.4 Estrategia de datos del proyecto (híbrida, 3 capas)

| Capa | Fuente | Propósito | Tamaño objetivo |
|---|---|---|---|
| **A. Gold standard sintético** | Generación con LLM + **etiquetado manual por los 4 integrantes** con acuerdo inter-anotador | Métricas cuantitativas (precision / recall / F1 por campo) | 300–400 mensajes |
| **B. Anclaje en literatura** | Muestra traducida/adaptada de `CrisisBench-all-lang` o HumAID | Comparabilidad con el estado del arte; validación de la taxonomía | 100–150 mensajes |
| **C. Robustez en vivo** | Stream real (ver §4.2) | Evaluación cualitativa: ¿aguanta texto no escrito para el sistema? | Streaming |

Justificación metodológica de la capa A: la propia literatura (arXiv 2605.08448) valida el uso de LLMs como generadores de supervisión. Documentar el protocolo de anotación y el acuerdo inter-anotador (Cohen's κ o Krippendorff's α) convierte una limitación en una decisión metodológica defendible.

---

## 4. Infraestructura: proveedores verificados

### 4.1 Inferencia del modelo — dónde corre Llama

**Hugging Face Inference Providers** funciona como *router* hacia 15+ proveedores externos (Groq entre ellos), con **pricing pass-through sin margen**: se paga la tarifa del proveedor subyacente.

| Opción | Free tier | Veredicto |
|---|---|---|
| **HF — cuenta gratuita** | **USD 0.10/mes** en créditos de Inference Providers | ❌ Insuficiente. Alcanza para pruebas triviales |
| HF PRO (USD 9/mes) | 2M créditos mensuales de inferencia | 🟡 Viable si se requiere; costo real bajo |
| HF Serverless (legacy) | ~1.000 req/día, modelos <10B parámetros | 🟡 Sirve para 8B, no para 70B |
| **Groq — free tier, directo** | **`llama-3.1-8b-instant`: 14.400 req/día**, 500K tokens/día, 6K TPM | ✅ **Opción principal.** Sin tarjeta de crédito |
| Groq — free tier, directo | `llama-3.3-70b-versatile`: **1.000 req/día**, 30 RPM, 12K TPM, 100K TPD | ✅ **Suficiente para el benchmark comparativo** |

**Los límites de Groq aplican a nivel de organización** — varias API keys no multiplican la cuota. Con 4 integrantes, conviene que **cada uno cree su propia organización** para el desarrollo paralelo, y usar una cuenta única para las corridas de evaluación oficiales.

**Decisión recomendada:**

- **Ejecución:** Groq API directo (`llama-3.1-8b-instant` como modelo de producción).
- **Benchmark:** `llama-3.3-70b-versatile` en Groq — 1.000 req/día alcanzan de sobra para evaluar un gold standard de 400 mensajes.
- **Hugging Face:** se usa como **fuente del Model Card y de los datasets** (que es lo que exige el enunciado del módulo), y se menciona Inference Providers como ruta alternativa de despliegue. El enunciado pide *seleccionar el modelo en una plataforma MaaS*, no necesariamente *ejecutarlo allí*: `meta-llama/Llama-3.1-8B-Instruct` en HF Hub cumple el requisito.

> **Ojo con el requisito del curso:** el Model Card de Meta debe transcribirse con licencia (**Llama 3.1 Community License**, no Apache/MIT), restricciones de uso (AUP de Meta), datos de entrenamiento, métricas y sesgos conocidos. La licencia Llama tiene cláusulas específicas (umbral de 700M usuarios activos, requisito de atribución "Built with Llama") que **hay que citar explícitamente** en la sección de Restricciones Técnicas.

### 4.2 Fuente de datos en vivo — de dónde salen los mensajes

Sobre la pregunta de **X (Twitter)**: sí es viable, y el panorama cambió a favor de proyectos pequeños.

| Plataforma | Modelo de costo (agosto 2026) | Veredicto |
|---|---|---|
| **X / Twitter** | **Ya no hay free tier real.** Nuevos desarrolladores entran en **pay-per-use: USD 0.005 por lectura de post** (tope 2M lecturas/mes); publicar cuesta USD 0.015. El plan Basic de USD 200/mes **fue retirado** y sus suscriptores migrados a pay-per-use tras el 1 de junio de 2026 | 🟡 **Viable y barato para nuestra escala.** 2.000 lecturas ≈ **USD 10**. Referencia: un proyecto pequeño con 1.000 lecturas/mes cuesta ~USD 6.50 |
| **Bluesky (AT Protocol)** | **Sin tier pago, sin tarifa por llamada, sin portal de aplicación ni cola de revisión.** Se crea una cuenta y se llama la API. Límite por puntos: 5.000 puntos/hora (un post cuesta 3). Lecturas libres | ✅ **Opción gratuita principal** |
| Reddit | Gratis con OAuth | ✅ Complementaria |
| Telegram | Gratis (bot en canal propio) | ✅ **La más realista para el contexto colombiano** |
| CSV replay | Gratis | ✅ Demo reproducible en sustentación |

**Qué es Bluesky:** red social descentralizada construida sobre el **AT Protocol**, protocolo abierto. A diferencia de X o Meta, no hay gatekeeping: cualquiera puede leer el *firehose* público. Es la alternativa de facto para investigación académica en redes sociales desde el cierre del acceso gratuito de X. Para el proyecto es atractiva porque el acceso es inmediato y sin fricción administrativa.

**Recomendación de arquitectura:** definir una interfaz `FuenteDeMensajes` con implementaciones intercambiables (`BlueskySource`, `XSource`, `TelegramSource`, `CSVReplaySource`). Esto convierte la elección de plataforma en configuración, no en arquitectura, y protege el cronograma:

- **Entregable demostrable:** Bluesky en vivo + CSV replay del gold standard.
- **Opcional documentado:** X con presupuesto acotado (~USD 10) para una muestra real de mensajes en español.
- **Realismo contextual:** Telegram simula el canal WhatsApp que el Distrito habilitó realmente (310 229 97 08). WhatsApp Business API requiere verificación de empresa — **no es viable en el plazo del curso**; Telegram es su sustituto metodológico legítimo y así debe justificarse.

---

## 5. Estándares de interoperabilidad

Alinear el esquema JSON de salida con vocabularios existentes en lugar de inventar uno propio.

| Estándar | Organismo | Qué es | Uso en el proyecto |
|---|---|---|---|
| **CAP** (Common Alerting Protocol) | OASIS, estándar desde **2004** | Protocolo XML para intercambio de alertas y avisos | Referencia para los campos de severidad, urgencia y certeza. **CAP separa `severity`, `urgency` y `certainty` como dimensiones independientes** — respalda directamente nuestra decisión de desacoplar gravedad / urgencia / confianza |
| **EDXL** (Emergency Data Exchange Language) | OASIS, libre de regalías | Suite de estándares XML para compartir información de emergencia entre entidades gubernamentales y organizaciones de respuesta; diseñado para compartir información sobre recursos que salvan vidas entre niveles local, estatal, nacional y ONGs | Referencia para el módulo de necesidades/recursos (EDXL-RM) |
| **HXL** (Humanitarian eXchange Language) | **OCHA** (ONU) | "Un estándar simple para datos desordenados": sistema de hashtags de columnas para datos humanitarios | Etiquetado de las columnas del dashboard y de los exports CSV |
| **Estandarización de Ayuda Humanitaria de Colombia** | **UNGRD** | Manual desarrollado conforme a la **Ley 1523 de 2012** | **Fuente normativa nacional para la taxonomía de tipos de necesidad.** Prioritaria sobre cualquier taxonomía extranjera |

> ⚠️ **HXL está en proceso de retiro de servicios** ("Retiring HXL Services", hxlstandard.org). Citarlo como antecedente conceptual, no como dependencia técnica.

**Marco normativo colombiano a citar:**

- **Ley 1523 de 2012** — adopta la Política Nacional de Gestión del Riesgo de Desastres y establece el SNGRD. Es la norma que da existencia legal al PMU.
- **Ley 1581 de 2012** — protección de datos personales. Obliga el tratamiento de PII en los mensajes ciudadanos (nombres, teléfonos, direcciones). Sustenta el campo `pii_removida` y el paso de anonimización en preprocesamiento.

---

## 6. Síntesis: cómo esta investigación blinda el proyecto

| Elemento del documento | Qué aporta esta investigación |
|---|---|
| **Contexto** | Caso real, local, reciente y documentado oficialmente (10 ago 2026) |
| **Problema** | **Declarado por la propia autoridad**: saturación de canales de socorro + circulación de material no verificado + habilitación de canal de texto (WhatsApp) |
| **Justificación del LLM** | Gen. 1 no escala (Ushahidi), Gen. 2 exige re-etiquetado por evento (AIDR), Gen. 3 lo elimina |
| **Originalidad** | Gap explícito: español coloquial + open-weights 8B + toponimia urbana informal + bajo costo |
| **Hipótesis calibrada** | F1 ≥ 0.80 frente al 0.84–0.92 del estado del arte con modelos frontier |
| **Decisión de arquitectura** | LLM extrae → geocodificador determinista resuelve (+19 pts de precisión, validado) |
| **Taxonomía** | HumAID (10+1 clases) + manual UNGRD, no invención propia |
| **Restricciones técnicas** | Costos y límites de cuota verificados con cifras concretas |
| **Ética y legal** | Ley 1581 (PII), sesgos de GeoNames documentados, sesgo lingüístico de Llama, desinformación como variable de estudio |

---

## 7. Pendientes de verificación antes de la entrega

- [ ] Cifras finales de víctimas y daños en Cali (usar repositorio oficial de la Alcaldía, indicando fecha de corte)
- [ ] Confirmar límites vigentes del free tier de Groq (cambian con frecuencia)
- [ ] Confirmar pricing pay-per-use de X si se decide usarlo
- [ ] Descargar y revisar el Model Card completo de `meta-llama/Llama-3.1-8B-Instruct` en HF Hub
- [ ] Verificar texto exacto de la Llama 3.1 Community License y su compatibilidad con uso académico
- [ ] Localizar el DOI y la cita formal completa de cada paper de la §2.3
- [ ] Revisar si el manual de estandarización de ayuda humanitaria de la UNGRD tiene versión vigente actualizada
- [ ] Confirmar la existencia de un protocolo formal de monitoreo de redes sociales en el PMU de Cali (para caracterizar el "as-is" con precisión)

---

## 8. Referencias

**Caso motivador**

- [Emergencias y medidas por terremoto en Cali — Alcaldía de Santiago de Cali](https://www.cali.gov.co/boletines/publicaciones/193598/emergencias-y-medidas-por-terremoto-en-cali/)
- [Terremoto de Cali — Repositorio Oficial de Información](https://www.cali.gov.co/gobierno/publicaciones/193607/terremoto-de-cali-repositorio-oficial-de-informacion/)
- [Alcaldía y Concejo de Cali empiezan articulación para la fase de recuperación](https://www.cali.gov.co/boletines/publicaciones/193766/alcaldia-y-concejo-de-cali-empiezan-articulacion-para-la-fase-de-recuperacion-tras-el-terremoto/)
- [Infobae — El sismo de 7,4 se sintió en varias ciudades del país](https://www.infobae.com/colombia/2026/08/10/temblor-en-colombia-el-sismo-de-67-se-sintio-en-varias-ciudades-del-pais-incluyendo-bogota-medellin-y-cali/)
- [Infobae — Más de 130 muertos, 570 heridos: cifras del terremoto](https://www.infobae.com/colombia/2026/08/11/mas-de-130-muertos-570-heridos-viviendas-y-vias-danadas-y-aeropuertos-cerrados-las-dramaticas-cifras-que-deja-hasta-ahora-el-terremoto-en-colombia/)
- [Infobae — Cruz Roja Valle en el PMU: "Nos va a durar entre dos y cuatro años"](https://www.infobae.com/colombia/2026/08/15/director-de-operaciones-de-emergencias-de-la-cruz-roja-valle-dio-advertencia-en-medio-del-pmu-en-cali-nos-va-a-durar-entre-dos-y-cuatro-anos/)
- [El Heraldo — Gobierno instala puestos de mando unificados para atender la emergencia](https://www.elheraldo.co/colombia/2026/08/10/gobierno-instala-puestos-de-mando-unificados-para-atender-la-emergencia/)
- [Semana — Cali comienza la reconstrucción: alcalde Eder instala nuevo PMU](https://www.semana.com/nacion/cali/articulo/cali-comienza-la-reconstruccion-tras-el-terremoto-alcalde-eder-instala-nuevo-puesto-de-mando-unificado/202608/)
- [El País — Terremoto en Cali, EN VIVO](https://www.elpais.com.co/cali/terremoto-en-cali-en-vivo-autoridades-suspenden-el-pico-y-placa-debido-a-la-emergencia-1007.html)
- [Wikipedia — Terremoto de Colombia de 2026](https://es.wikipedia.org/wiki/Terremoto_de_Colombia_de_2026)

**Estado del arte — LLMs y gestión de desastres**

- [Cafferata et al. (2025). Large Language Models for Geolocation Extraction in Humanitarian Crisis Response. arXiv:2602.08872](https://arxiv.org/html/2602.08872v1)
- [Extracting Disaster Impacts and Impact Related Locations in Social Media Posts Using LLMs. arXiv:2511.21753](https://arxiv.org/html/2511.21753)
- [LLMs for Causal Relations Extraction in Social Media: A Validation Framework for Disaster Intelligence. arXiv:2605.11348](https://arxiv.org/html/2605.11348v1)
- [LLM-guided Semi-Supervised Approaches for Social Media Crisis Data Classification. arXiv:2605.08448](https://arxiv.org/pdf/2605.08448)
- [Harnessing Large Language Models for Disaster Management: A Survey](https://www.themoonlight.io/en/review/harnessing-large-language-models-for-disaster-management-a-survey)
- [Enhanced earthquake impact analysis based on social media texts via large language model — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S2212420924003364)

**Antecedentes fundacionales — crisis informatics**

- [AIDR: Artificial Intelligence for Disaster Response — QCRI](https://aidr.qcri.org/)
- [AIDR: artificial intelligence for disaster response — ACM DL](https://dl.acm.org/doi/10.1145/2567948.2577034)
- [Crowdsourcing Crisis Information in Disaster-Affected Haiti](https://preparecenter.org/sites/default/files/crowdsourcing_crisis_information_in_disaster-affected_haiti.pdf)
- [Crisis Analytics: Big Data Driven Crisis Response. arXiv:1602.07813](https://arxiv.org/pdf/1602.07813)

**Datasets**

- [QCRI/HumAID-all — Hugging Face Datasets](https://huggingface.co/datasets/QCRI/HumAID-all)
- [QCRI/HumAID-event-type — Hugging Face Datasets](https://huggingface.co/datasets/QCRI/HumAID-event-type)
- [QCRI/CrisisBench-all-lang — Hugging Face Datasets](https://huggingface.co/datasets/QCRI/CrisisBench-all-lang)
- [CrisisNLP — QCRI](https://crisisnlp.qcri.org/)

**Estándares y marco normativo**

- [EDXL — Emergency Data Exchange Language (Wikipedia)](https://en.wikipedia.org/wiki/EDXL)
- [OASIS Advances CAP and EDXL Specifications — Cover Pages](https://xml.coverpages.org/ni2005-09-08-a.html)
- [Humanitarian eXchange Language (HXL)](https://hxlstandard.org/)
- [HXL Standard — GitHub](https://github.com/HXLStandard)
- [Estandarización de Ayuda Humanitaria de Colombia — UNGRD](https://www.humanitarianresponse.info/en/operations/colombia/document/estandarizaci%C3%B3n-de-ayuda-humanitaria-de-colombia-ungrd)

**Infraestructura y costos**

- [Hugging Face Inference API Free Tier Limits & Pricing 2026 — Klymentiev](https://klymentiev.com/blog/huggingface-inference-api)
- [Hugging Face pricing explained: what you actually pay in 2026 — eesel AI](https://www.eesel.ai/blog/hugging-face-pricing)
- [Groq API Free Tier Limits in 2026 — Grizzly Peak Software](https://www.grizzlypeaksoftware.com/articles/p/groq-api-free-tier-limits-in-2026-what-you-actually-get-uwysd6mb)
- [Groq pricing in 2026: every model, free tier, and hidden discounts — eesel AI](https://www.eesel.ai/blog/groq-pricing)
- [X (Twitter) API Pricing: Complete Guide for 2026 — Blotato](https://www.blotato.com/blog/twitter-api-pricing)
- [X (Twitter) API Pricing in 2026: All Tiers — Postproxy](https://postproxy.dev/blog/x-api-pricing-2026/)
- [Bluesky API Pricing: Full Breakdown for 2026 — Blotato](https://www.blotato.com/blog/bluesky-api-pricing)
- [The Complete Guide to Bluesky AT Protocol — DEV Community](https://dev.to/0012303/the-complete-guide-to-bluesky-at-protocol-4-free-tools-for-developers-1edb)

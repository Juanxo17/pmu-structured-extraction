# Trabajo futuro

Inventario de lo que queda pendiente para cerrar el componente de **registro de experimentos (MLflow) y métricas de evaluación**, según lo que exigen `AGENTS.md` (§MLflow), `docs/propuesta/03_tareas_estimacion_y_ruta_critica.md` (T-24 a T-27 y T-31), `docs/propuesta/02_objetivos_y_alcance.md` (OE5) y `docs/CONFIG_PROVEEDORES.md`.

Se escribe a partir de una revisión del repositorio del 2026-09-17. El objetivo no es justificar la omisión, sino dejar el inventario exacto de lo que falta y en qué orden ejecutarlo.

## Estado actual

- El **marco de evaluación** (T-15) ya existe en `backend/inference/inference/evaluacion.py`: calcula exactitud y F1 por campo del esquema (`MetricaCampo`), latencia media y p95, y errores de validación (`Metricas`), y redacta un informe en Markdown (`generar_informe`). Tiene pruebas en `tests/inference/test_evaluacion.py`.
- **MLflow no está implementado**: no hay dependencia declarada, no hay código que registre corridas, no hay `MLFLOW_TRACKING_URI` cableada al servicio de inferencia y no existe ninguna corrida registrada.
- El **contenedor** de MLflow sí está definido en `docker-compose.yml` (servicio `mlflow`, puerto `5000`, backend SQLite, volumen `mlflow_data`), pero es solo infraestructura: todavía nada lo usa.
- La carpeta `eval-prompt/report/` solo contiene `distribucion_corpus.md`; **nunca se ha ejecutado una corrida de evaluación** con salida persistida.

## Brechas por cerrar

### 1. Registro de corridas en MLflow (T-24)

- **Origen:** `AGENTS.md` §MLflow.
- **Dónde:** `backend/inference/inference/evaluacion.py` (`main`, `generar_informe`).
- **Qué falta:** el punto de entrada de la evaluación no abre una corrida (`mlflow.start_run`), no registra parámetros, no registra métricas, no sube artefactos y no etiqueta la corrida. `AGENTS.md` pide que **cada** evaluación o sesión de inferencia quede registrada como una corrida de experimento (no de entrenamiento).
- **Qué revisar después:** decidir si el registro vive solo en el harness de evaluación o también en el servicio de inferencia en ejecución (`backend/inference/inference/servicio.py`, `main.py`). La redacción de `AGENTS.md` ("evaluación o sesión de inferencia") admite ambas lecturas.

### 2. Dependencia `mlflow` y configuración de entorno

- **Dónde:** `backend/inference/pyproject.toml`, `docker-compose.yml` (servicio `inference`), `.env.example`.
- **Qué falta:**
  - Declarar la dependencia `mlflow` en el paquete de inferencia.
  - Pasar `MLFLOW_TRACKING_URI` al contenedor de `inference` y declarar `depends_on: mlflow` (`docker-compose.yml` hoy solo le entrega `GROQ_API_KEY`).
  - Documentar la variable en `.env.example` y en `docs/CONFIG_PROVEEDORES.md`.
- **Requisito de diseño:** si `MLFLOW_TRACKING_URI` no está definida, la corrida debe **ejecutarse igual, sin registrar** (así lo describe `docs/CONFIG_PROVEEDORES.md`). El registro no puede volverse una dependencia dura para correr la evaluación.

### 3. Parámetros que exige la documentación y el código no captura

| Parámetro (`AGENTS.md`) | Estado | Comentario |
| --- | --- | --- |
| Repositorio + revisión del modelo en Groq/HF Hub | Falta | El proveedor solo guarda el nombre del modelo; no hay revisión ni commit. |
| Versión del corpus | Falta | `gold_v1` existe como carpeta y en `README_gold_v1.md`, pero no hay una constante ni un campo que lo registre. |
| Umbral de la compuerta (etapa 1) | **No existe** | `config/` solo contiene `ontologia.yaml` y no define umbral. Además `docs/propuesta/02_objetivos_y_alcance.md` afirma que el proyecto **no** condiciona su éxito a un umbral. Ver "Contradicciones por resolver". |
| Configuración de prompts | Parcial | Existe `VERSION_PROMPTS` en `servicio.py`, pero no se expone ni se registra. |

### 4. Matrices de confusión (T-24)

- **Origen:** `docs/propuesta/03_tareas_estimacion_y_ruta_critica.md` (T-24): "comparación automatizada contra el gold standard, desempeño por campo, **matrices de confusión**, medición de latencia".
- **Dónde:** `backend/inference/inference/evaluacion.py`.
- **Qué falta:** el harness calcula exactitud y F1 por campo, pero no construye matrices de confusión. Falta definir el formato (tabla Markdown/CSV por campo categórico, o imagen) y decidir si se incorpora una dependencia de graficación o se mantiene sin dependencias nuevas.

### 5. Artefacto "ejemplos de predicción"

- **Origen:** `AGENTS.md` §MLflow ("Artefactos: informe de evaluación, **ejemplos de predicción**").
- **Dónde:** `backend/inference/inference/evaluacion.py`.
- **Qué falta:** el informe actual solo lista los ejemplos con error de validación. No se persiste un volcado de predicciones por ejemplo (por ejemplo, un JSONL con texto de entrada, predicción y gold) que pueda subirse como artefacto.

### 6. Tags de la corrida

- **Origen:** `AGENTS.md` §MLflow ("licencia Llama 3.1 Community License, equipo/autor, ambiente (dev/prod), PR asociado").
- **Qué falta:** no se define ningún tag. Ojo: el tag de licencia está atado al modelo realmente usado, que hoy es `openai/gpt-oss-20b` (no Llama). Ver "Contradicciones por resolver".

### 7. Corridas de evaluación (T-25, T-26, T-27)

- **T-25:** corrida con `Llama-3.1-8B-Instruct` y análisis cualitativo de modos de error. Pendiente.
- **T-26:** corrida comparativa con `Llama-3.3-70B-Instruct`, mismo prompt y mismo corpus. Pendiente.
- **T-27:** prueba de transferibilidad con una ontología alterna y corpus reducido. Pendiente.
- **Dónde:** `eval-prompt/`. Requiere `GROQ_API_KEY` y aproximadamente 340 llamadas por corrida (tamaño de `eval.jsonl`).

### 8. Informe de evaluación final (T-31)

- **Origen:** `docs/propuesta/03_tareas_estimacion_y_ruta_critica.md` (T-31) y el criterio de cierre (6) de `docs/propuesta/02_objetivos_y_alcance.md`.
- **Qué falta:** el documento que consolida resultados por campo, modos de error, comparación entre escalas, transferibilidad, límites y conclusiones. No existe.

### 9. Cobertura de pruebas

- **Origen:** `AGENTS.md` §Pruebas ("mínimo 120 pruebas unitarias").
- **Estado:** la suite colecciona 322 pruebas (por encima del mínimo de 120 exigido en `AGENTS.md`). Falta cubrir el registro en MLflow (parámetros, métricas, artefactos, tags y el modo "sin `MLFLOW_TRACKING_URI`").

## Contradicciones por resolver antes de implementar

1. **Umbral de la compuerta.** `AGENTS.md` lo exige como parámetro de la corrida, pero no existe en el código y `docs/propuesta/02_objetivos_y_alcance.md` declara explícitamente que el proyecto no se evalúa contra un umbral predefinido. Hay que decidir si se elimina del `AGENTS.md` o si se registra como `N/A` con una nota.
2. **Modelo y licencia.** La propuesta describe `Llama-3.1-8B-Instruct` / `Llama-3.3-70B-Instruct` y un tag de licencia "Llama 3.1 Community License". El modelo operativo documentado en `.env.example` y `docs/CONFIG_PROVEEDORES.md` es `openai/gpt-oss-20b` (sustituto por disponibilidad de proveedor). Si se corre con `gpt-oss`, el tag de licencia de Llama sería **incorrecto**. Hay que fijar la convención (registrar el modelo efectivo y su licencia real, o conseguir acceso a Llama).
3. **Alcance del registro.** Definir si el servicio de inferencia en producción también registra sesiones, o si por ahora el registro queda acotado al harness de evaluación.

## Orden de ejecución sugerido

1. Dependencia `mlflow` + cableado de `MLFLOW_TRACKING_URI` + modo "sin registro".
2. Registro de la corrida (parámetros, métricas, artefactos, tags) dentro del harness.
3. Matrices de confusión y volcado de predicciones como artefacto.
4. Pruebas del registro.
5. Corrida real (T-25) y análisis de modos de error.
6. Comparación de escala (T-26) y transferibilidad (T-27).
7. Informe de evaluación final (T-31).

## Nota sobre el corpus y el gold standard

T-24 y T-25 se apoyan en `gold_v1` como referencia. Ese gold se construyó con scripts (`eval-prompt/scripts/generar_corpus.py`, `generar_anotaciones.py`, `consolidar_gold.py`) que generan el corpus por plantillas y simulan la anotación de las cuatro partidas, con desviaciones inyectadas para producir el índice de concordancia. Antes de presentar un informe de evaluación contra ese gold conviene decidir si se declara explícitamente su naturaleza sintética o si se reemplaza por una anotación real.

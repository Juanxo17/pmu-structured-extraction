# AGENTS.md

Lineamientos para cualquier persona o agente de código (Claude Code, OpenCode, etc.) que trabaje en este repositorio. Léelo antes de modificar cualquier archivo.

## Contexto del proyecto

**SIRENA** — extracción estructurada de reportes ciudadanos de emergencia (Santiago de Cali) mediante un LLM de pesos abiertos (Llama 3.1 8B Instruct vía Groq), con validación de esquema y normalización geográfica determinista. Ver la propuesta completa en [`docs/propuesta/propuesta-final-sirena.md`](docs/propuesta/propuesta-final-sirena.md).

Los principios de producto y las exclusiones de alcance (qué no calcula ni decide el sistema, límites éticos, restricciones de despliegue) están en [`.specify/memory/constitution.md`](.specify/memory/constitution.md) — ese archivo es el que valida `/speckit-plan` y `/speckit-analyze`; este `AGENTS.md` cubre solo convenciones operativas del día a día.

## Frentes de trabajo (en paralelo)

Cuatro frentes, cada uno con dueño de módulo (ver 5.3 de la propuesta):

- **A — Datos y Evaluación**: corpus, anotación, MLflow, informe de evaluación
- **B — Núcleo de extracción**: esquema Pydantic v2 (compuerta + naturaleza + ubicación), prompts, cliente de inferencia (Groq), validador, orquestador de dos etapas
- **C — Geo e Ingesta**: gazetteer, normalización geográfica, anonimización (Ley 1581), fuentes de mensajes
- **D — Plataforma e Interfaz**: persistencia (SQLite + SQLAlchemy), API (FastAPI), tablero (Streamlit), Docker

El contrato central entre frentes es el esquema Pydantic de extracción — ver `docs/CONTRATOS_MODULOS.md` (pendiente de formalizar vía `/speckit-specify`). Nadie implementa contra ese esquema hasta que quede congelado y acordado por el equipo.

## Gestor de paquetes: uv, exclusivamente

Prohibido `pip install` directo.

```bash
uv add <paquete>          # dependencia de producción
uv add --dev <paquete>    # dependencia de desarrollo (linter, tests, etc.)
uv sync                   # instalar/actualizar el entorno desde pyproject.toml + uv.lock
```

## Estilo de código

- PEP 8, verificado con `ruff`.
- Docstrings obligatorios en todo módulo, clase, función y método público (Google style: `Args:`, `Returns:`, `Raises:`).
- Cero warnings: se corrige la causa, nunca se silencia con `warnings.filterwarnings`.
- Sin abstracciones ni manejo de errores para casos que no pueden ocurrir. No hacer refactors fuera del alcance de lo que se está trabajando.
- Alta cohesión, bajo acoplamiento — mismo criterio que en `uao-neumonia`: si un método hace algo claramente distinto al resto de la clase, se extrae a su propia clase con nombre específico, nunca a un `utils.py`/`Manager.py`.

## Pruebas

- Mínimo 120 pruebas unitarias con `pytest` en `tests/`.
- Toda función nueva o modificada necesita su prueba correspondiente.
- Patrón AAA (Arrange / Act / Assert), agrupadas en clases `TestNombreDeLoQueSePrueba`.
- La suite debe pasar en verde antes de abrir un Pull Request.

## MLflow

Como el modelo es preentrenado (no hay fine-tuning), cada corrida de MLflow registra una **evaluación o sesión de inferencia**, no un entrenamiento:

- **Parámetros**: repositorio + revisión del modelo en Groq/HF Hub, versión del corpus, umbral de la compuerta (etapa 1), configuración de prompts.
- **Métricas**: precisión exacta y F1 por campo del esquema, latencia media/p95.
- **Artefactos**: informe de evaluación, ejemplos de predicción.
- **Tags**: licencia Llama 3.1 Community License, equipo/autor, ambiente (dev/prod), PR asociado.

`mlflow server` + variable `MLFLOW_TRACKING_URI` compartida por el equipo (mismo flujo del laboratorio de Clase 7).

## Flujo de Git

- Gitflow: `main` (producción) ← `develop` (integración) ← `feature/<frente>-<algo>` (ej. `feature/b-esquema-pydantic`).
- Todo cambio se integra mediante Pull Request con la plantilla oficial (`.github/pull_request_template.md`) — nunca push directo a `main` ni a `develop`.
- Un PR no se mergea si `pytest` o `ruff` fallan.

## Contratos entre módulos

Las firmas y esquemas documentados en `docs/CONTRATOS_MODULOS.md` son la interfaz que el resto del equipo asume para integrar su propio módulo. Si necesitas cambiar el esquema de un campo ya contratado:

1. Actualiza `docs/CONTRATOS_MODULOS.md` en el mismo PR.
2. Avisa al equipo — quien depende de ese campo puede estar trabajando con un mock basado en la versión anterior.

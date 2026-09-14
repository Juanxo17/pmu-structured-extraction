### 📝 Convención del Título de la PR
Aplica un [prefijo convencional](https://www.conventionalcommits.org/) en el título para clasificar el trabajo:

| Prefijo | Cuándo usar | Ejemplo |
|--------|-------------|---------|
| `feat:` | Nueva funcionalidad o módulo | `feat: agregar esquema Pydantic de salida` |
| `fix:` | Corrección de errores o eliminación de warnings | `fix: corregir validación del validador de salidas` |
| `test:` | Adición o refactorización de pruebas unitarias | `test: agregar pruebas para el orquestador del pipeline` |
| `chore:` | Tareas de mantenimiento, Docker, docs o config | `chore: actualizar Dockerfile y configuración de CI` |

---

### 🧱 Servicio o Componente Afectado
Selecciona las áreas principales en las que trabaja esta PR:
- [ ] **BFF** (`backend/bff`) — gateway externo, proxy hacia CRUD
- [ ] **CRUD** (`backend/crud`) — persistencia SQLite/SQLAlchemy
- [ ] **Process** (`backend/process`) — anonimización, duplicados, orquestador
- [ ] **Inference** (`backend/inference`) — cliente de inferencia, prompts, validador
- [ ] **Geo** (`backend/geo`) — gazetteer, normalización geográfica
- [ ] **Frontend** (`frontend`) — tablero Streamlit
- [ ] **Datos / Evaluación** (`eval-prompt`) — corpus, anotación, métricas, informe
- [ ] **Contrato compartido** (`common/sirena-schema`, `config/ontologia.yaml`)
- [ ] **Infraestructura & Contenedores** (`Dockerfile`, `docker-compose.yml`, CI, dependencias)
- [ ] **Documentación** (`docs/`, README, plantillas)

---

### 📚 Descripción de los Cambios
<!---
Describe qué logra esta PR, la motivación y los detalles técnicos relevantes.
-->

**Tarea / Ticket asociado (si aplica):** <!-- Ej. T-14 · Orquestador del pipeline -->

#### Resumen de Cambios:
- 

#### Justificación del Diseño (Clean Code / Principios SOLID):
<!---
Explica brevemente cómo se mantuvo la Alta Cohesión y Bajo Acoplamiento en las clases/funciones modificadas.
-->
- 

---

### ✅ Lista de Chequeo Pre-PR
- [ ] El código se ejecutó y probó exitosamente con la herramienta de dependencias del proyecto (`uv`).
- [ ] La ejecución corre **sin advertencias (warnings)**.
- [ ] Artefactos generados y archivos sensibles (`.env`, credenciales, datos pesados) están excluidos en `.gitignore`.
- [ ] La estructura sigue las convenciones del repo (`backend/<servicio>/<servicio>`, `common/`, `frontend/`, `tests/`, `docs/`).
- [ ] Se ejecutaron las pruebas (`uv run pytest`) y pasan correctamente.
- [ ] Las funciones son cohesivas, con responsabilidad única y nombres descriptivos.

---

### 🧪 Evidencia de Pruebas Ejecutadas
<!---
Adjunta capturas de pantalla, logs o la salida de pruebas demostrando que el código funciona.
-->

```bash
# Salida de pruebas unitarias ejecutadas con UV:
uv run pytest

---

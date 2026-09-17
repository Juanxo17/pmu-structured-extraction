# Configuración de Proveedores y Conectividad (T-05)

Documento de referencia para la **configuración de credenciales** y la
**conectividad del servicio de inferencia** con el proveedor Groq.

## 1. Variables de entorno

El servicio de inferencia (`backend/inference`) lee la configuración desde
variables de entorno. No existe ningún secreto commiteado en el repositorio.

| Variable | Obligatoria | Descripción | Default |
|---|---|---|---|
| `GROQ_API_KEY` | Sí | Clave de API de Groq. Se obtiene en https://console.groq.com/keys | — |
| `INFERENCE_MODELO` | No | Modelo usado por `ProveedorGroq.completar`. | `openai/gpt-oss-20b` |
| `INFERENCE_INTENTOS_LLM` | No | Reintentos ante errores 429/5xx (backoff exponencial + jitter). | `3` |
| `INFERENCE_ESPERA_BASE` | No | Segundos base del backoff exponencial. | `1.0` |
| `INFERENCE_JITTER_MAX` | No | Jitter aleatorio máximo añadido a la espera. | `0.5` |
| `MLFLOW_TRACKING_URI` | No | URI del servidor MLflow para registrar corridas de evaluación. | (sin registro) |
| `ONTOLOGIA_PATH` | No | Ruta de la ontología inyectada en los prompts. | `config/ontologia.yaml` |

## 2. Preparación (una sola vez)

1. Copiar la plantilla: `cp .env.example .env`.
2. Completar `GROQ_API_KEY` con una clave generada en
   https://console.groq.com/keys → **Create API Key**.
3. Verificar que `.env` **no** se commitee (ya está en `.gitignore`, línea 9).
4. Puesta en marcha del servicio:
   ```bash
   make run-inference        # uvicorn en :8003
   ```

## 3. Verificación de conectividad

Prueba mínima de llama al proveedor (sin levantar el servidor):

```bash
uv run --package inference python - <<'PY'
import os
from inference.proveedor import ProveedorGroq

p = ProveedorGroq()
print(p.completar("Eres un asistente.", "Responde solo: OK"))
PY
```

Resultado observado el 2026-09-16:

```text
MODELO=openai/gpt-oss-20b
RESPUESTA=[OK]
CONECTIVIDAD=OK
```

## 4. Catálogo de modelos accesibles con la clave actual

> **Hallazgo T-05:** la clave provista tiene acceso a un **catálogo
> restringido** de modelos. Los modelos `llama-3.1-8b-instant` y
> `llama-3.3-70b-versatile` (referenciados en T-25/T-26) **no están
> disponibles** con esta clave (error `model_not_found`).

Modelos disponibles (consultados vía `GET /openai/v1/models` el 2026-09-16):

| Modelo | Perfil |
|---|---|
| `openai/gpt-oss-20b` | Actualable libre (MIT), 20B — **seleccionado como modelo base** (sustituto del perfil 8B de T-25) |
| `openai/gpt-oss-120b` | 120B — **candidato para la comparación de gama alta (T-26)** |
| `openai/gpt-oss-safeguard-20b` | GPT-OSS con capa de seguridad |
| `qwen/qwen3.8-27b` | Qwen 3 (gama media) |
| `allam-2-7b` | ALLaM 2 7B (multilingüe) |
| `groq/compound`, `groq/compound-mini` | Modelos compuestos/ruteados |
| `whisper-large-v3`, `whisper-large-v3-turbo` | Transcripción de audio |
| `meta-llama/llama-prompt-guard-2-*` | Detección de inyección de prompts |

Para seleccionar otro modelo basta cambiar `INFERENCE_MODELO` (o pasar el
argumento `modelo=` en pruebas):

```bash
INFERENCE_MODELO=openai/gpt-oss-120b uv run --package inference python ...
```

## 5. Notas de operación

- El proveedor reintenta automáticamente errores HTTP **429** y **5xx** con
  backoff exponencial, jitter y respeto de la cabecera `Retry-After`
  (`ProveedorGroq._admite_reintento`).
- La clave no se imprime en logs ni en salidas de proceso.
- El registro MLflow de las corridas del harness se habilita al definir
  `MLFLOW_TRACKING_URI`; si no está definida, las corridas se ejecutan igual
  pero sin registrarse (ver T-24).
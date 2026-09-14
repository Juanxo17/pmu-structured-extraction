"""Punto de entrada FastAPI del servicio Inference.

Endpoints por implementar (ver docs/CONTRATOS_SISTEMA.md, seccion 4):
- POST /compuerta, POST /extraccion
"""

from fastapi import FastAPI

app = FastAPI(title="SIRENA - Inference")


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}

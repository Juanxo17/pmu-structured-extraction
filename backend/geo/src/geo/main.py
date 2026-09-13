"""Punto de entrada FastAPI del servicio Geo.

Endpoints por implementar (ver docs/CONTRATOS_SISTEMA.md, seccion 5):
- POST /resolver
"""

from fastapi import FastAPI

app = FastAPI(title="SIRENA - Geo")


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}

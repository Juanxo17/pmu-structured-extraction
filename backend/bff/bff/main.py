"""Punto de entrada FastAPI del servicio BFF.

Endpoints por implementar (ver docs/CONTRATOS_SISTEMA.md, seccion 1):
- POST /mensajes
- GET /reportes, GET /reportes/{id}, PATCH /reportes/{id}, GET /reportes/resumen
"""

from fastapi import FastAPI

app = FastAPI(title="SIRENA - BFF")


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}

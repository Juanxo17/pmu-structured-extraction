"""Punto de entrada FastAPI del servicio CRUD.

Endpoints por implementar (ver docs/CONTRATOS_SISTEMA.md, seccion 2):
- POST /reportes, GET /reportes, GET /reportes/{id}, PATCH /reportes/{id}, GET /reportes/resumen
"""

from fastapi import FastAPI

app = FastAPI(title="SIRENA - CRUD")


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}

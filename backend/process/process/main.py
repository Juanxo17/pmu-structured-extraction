"""Punto de entrada FastAPI del servicio Process.

Endpoints por implementar (ver docs/CONTRATOS_SISTEMA.md, seccion 3):
- POST /procesar (orquesta: anonimiza -> duplicados -> Inference -> Geo -> CRUD)
"""

from fastapi import FastAPI

app = FastAPI(title="SIRENA - Process")


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}

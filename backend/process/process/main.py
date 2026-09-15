"""Punto de entrada FastAPI del servicio Process."""

from fastapi import FastAPI
from pydantic import BaseModel

from process.orquestador import procesar_mensaje

app = FastAPI(title="SIRENA - Process")


class PeticionProcesar(BaseModel):
    """Cuerpo de la peticion POST /procesar (ver docs/CONTRATOS_SISTEMA.md, seccion 3)."""

    mensaje_id: str
    texto_crudo: str
    fuente: str
    id_externo: str
    autor_id_telegram: str


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}


@app.post("/procesar")
async def procesar(peticion: PeticionProcesar) -> dict:
    """Orquesta el pipeline completo para un mensaje ciudadano.

    Args:
        peticion: Datos del mensaje crudo, ya validados por BFF.

    Returns:
        `{"estado": "estructurado", "reporte": ...}` o
        `{"estado": "descartado", "motivo": ...}`, segun el resultado del pipeline.

    """
    return await procesar_mensaje(
        mensaje_id=peticion.mensaje_id,
        texto_crudo=peticion.texto_crudo,
        fuente=peticion.fuente,
        id_externo=peticion.id_externo,
        autor_id_telegram=peticion.autor_id_telegram,
    )
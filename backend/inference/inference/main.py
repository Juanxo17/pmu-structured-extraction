"""Punto de entrada FastAPI del servicio Inference.

Expone las dos etapas de inferencia contratadas en docs/CONTRATOS_SISTEMA.md
(seccion 4): POST /compuerta y POST /extraccion. Ambas usan el proveedor del
LLM inyectado por dependencia, de modo que las pruebas pueden sustituirlo.
"""

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sirena_schema.schema import Compuerta, Naturaleza, UbicacionExtraida

from inference.proveedor import ProveedorGroq, ProveedorLLM
from inference.servicio import ServicioInferencia
from inference.validador import RechazoSalida

app = FastAPI(title="SIRENA - Inference")


class TextoEntrada(BaseModel):
    """Cuerpo de una peticion de inference.

    Attributes:
        texto: Texto crudo del mensaje ciudadano a clasificar o extraer.

    """

    texto: str = Field(min_length=1)


class ExtraccionResultado(BaseModel):
    """Respuesta de la etapa de extraccion.

    Attributes:
        naturaleza: Naturaleza validada del evento.
        ubicacion: Ubicacion textual validada del evento.

    """

    naturaleza: Naturaleza
    ubicacion: UbicacionExtraida


def obtener_proveedor() -> ProveedorLLM:
    """Devuelve el proveedor del LLM usado por el servicio.

    Returns:
        Proveedor del LLM configurado con el entorno.

    """
    return ProveedorGroq()


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}


@app.post("/compuerta", response_model=Compuerta)
def compuerta(
    entrada: TextoEntrada,
    proveedor: ProveedorLLM = Depends(obtener_proveedor),
) -> Compuerta:
    """Clasifica un reporte como accionable y lo enmarca.

    Args:
        entrada: Texto crudo del mensaje ciudadano.
        proveedor: Proveedor del LLM inyectado.

    Returns:
        Compuerta validada con la clasificacion del reporte.

    Raises:
        RechazoSalida: Si la salida no conforma al esquema tras los intentos.

    """
    servicio = ServicioInferencia(proveedor)
    return servicio.clasificar(entrada.texto)


@app.post("/extraccion", response_model=ExtraccionResultado)
def extraccion(
    entrada: TextoEntrada,
    proveedor: ProveedorLLM = Depends(obtener_proveedor),
) -> ExtraccionResultado:
    """Extrae naturaleza y ubicacion de un reporte accionable.

    Args:
        entrada: Texto crudo del mensaje ciudadano.
        proveedor: Proveedor del LLM inyectado.

    Returns:
        Naturaleza y ubicacion validadas del reporte.

    Raises:
        RechazoSalida: Si la salida no conforma al esquema tras los intentos.

    """
    servicio = ServicioInferencia(proveedor)
    naturaleza, ubicacion = servicio.extraer(entrada.texto)
    return ExtraccionResultado(naturaleza=naturaleza, ubicacion=ubicacion)


@app.exception_handler(RechazoSalida)
def manejar_rechazo_salida(request: Request, exc: RechazoSalida) -> JSONResponse:
    """Convierte un rechazo de validacion en una respuesta 422.

    Args:
        request: Peticion que causo la excepcion (no se usa, requerido por
            FastAPI).
        exc: Excepcion con el detalle del rechazo.

    Returns:
        Respuesta 422 con el detalle del rechazo.

    """
    return JSONResponse(status_code=422, content={"detalle": exc.detalle})

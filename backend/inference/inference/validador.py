"""Validador de la salida cruda del LLM contra el esquema compartido.

Un LLM no garantiza un JSON valido ni valores admitidos por la ontologia.
Este modulo convierte el texto crudo en los modelos del esquema, reportando
rechazos con un detalle legible para que el servicio reintente la generacion.
"""

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from sirena_schema.schema import Compuerta, Naturaleza, Ubicacion

_Modelo = TypeVar("_Modelo", bound=BaseModel)


class RechazoSalida(Exception):
    """La salida cruda del modelo no conforma al esquema o no es JSON.

    Attributes:
        detalle: Descripcion legible de por que se rechazo la salida.

    """

    def __init__(self, detalle: str) -> None:
        """Almacena el detalle del rechazo.

        Args:
            detalle: Descripcion legible del motivo del rechazo.

        """
        super().__init__(detalle)
        self.detalle = detalle


def _extraer_json(texto: str) -> dict[str, Any]:
    """Convierte el texto crudo en un objeto JSON.

    Tolera bloques de codigo (markdown) que algunos modelos agregan alrededor
    de la respuesta y extrae unicamente el JSON.

    Args:
        texto: Salida cruda del modelo.

    Returns:
        Objeto JSON decodificado.

    Raises:
        RechazoSalida: Si el texto no contiene JSON decodificable.

    """
    candidato = texto.strip()
    if candidato.startswith("```"):
        lineas = candidato.splitlines()
        sin_fence = [linea for linea in lineas if not linea.lstrip().startswith("```")]
        candidato = "\n".join(sin_fence).strip()
    try:
        datos = json.loads(candidato)
    except json.JSONDecodeError as error:
        raise RechazoSalida(f"JSON invalido: {error.msg}") from error
    if not isinstance(datos, dict):
        raise RechazoSalida(f"Se esperaba un objeto JSON, se recibio {type(datos).__name__}")
    return datos


def _validar(modelo: type[_Modelo], datos: dict[str, Any]) -> _Modelo:
    """Valida un objeto JSON contra un modelo Pydantic del esquema.

    Args:
        modelo: Modelo Pydantic que define la forma esperada.
        datos: Objeto JSON a validar.

    Returns:
        Instancia del modelo ya validada.

    Raises:
        RechazoSalida: Si los datos no conforman al modelo.

    """
    try:
        return modelo.model_validate(datos)
    except ValidationError as error:
        fallos = "; ".join(
            f"{'.'.join(map(str, fallo['loc']))}: {fallo['msg']}" for fallo in error.errors()
        )
        raise RechazoSalida(f"No conforma al esquema: {fallos}") from error


def validar_compuerta(texto: str) -> Compuerta:
    """Valida la salida cruda de la etapa de compuerta.

    Args:
        texto: Salida cruda del modelo.

    Returns:
        Compuerta validada.

    Raises:
        RechazoSalida: Si la salida no conforma al esquema o no es JSON.

    """
    datos = _extraer_json(texto)
    return _validar(Compuerta, datos)


def validar_extraccion(texto: str) -> tuple[Naturaleza, Ubicacion]:
    """Valida la salida cruda de la etapa de extraccion.

    Args:
        texto: Salida cruda del modelo.

    Returns:
        Tupla con la Naturaleza y la Ubicacion validadas.

    Raises:
        RechazoSalida: Si la salida no conforma al esquema o no es JSON.

    """
    datos = _extraer_json(texto)
    try:
        naturaleza = datos["naturaleza"]
        ubicacion = datos["ubicacion"]
    except KeyError as error:
        raise RechazoSalida(f"Falta el bloque '{error.args[0]}' en el JSON") from error
    if not isinstance(naturaleza, dict) or not isinstance(ubicacion, dict):
        raise RechazoSalida("Los bloques naturaleza y ubicacion deben ser objetos JSON")
    naturaleza_valida = _validar(Naturaleza, naturaleza)
    ubicacion_valida = _validar(Ubicacion, ubicacion)
    return naturaleza_valida, ubicacion_valida

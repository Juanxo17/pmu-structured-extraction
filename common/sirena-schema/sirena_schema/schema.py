"""Esquema Pydantic v2 del reporte estructurado."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

from sirena_schema.ontologia import ONTOLOGIA


class Compuerta(BaseModel):
    """Capa 1: clasificacion de accionabilidad, temporalidad e intencion."""

    es_reporte_accionable: bool
    temporalidad: Literal["ocurriendo_ahora", "ya_ocurrio", "riesgo_previsto", "referencia_noticia"]
    intencion: Literal["solicita_ayuda", "reporta_terceros", "ofrece_ayuda", "solicita_informacion"]


class Naturaleza(BaseModel):
    """Capa 2: tipo de evento y servicios de respuesta involucrados."""

    tipo_evento: str
    servicio_de_respuesta: list[str]

    @field_validator("tipo_evento")
    @classmethod
    def _validar_tipo_evento(cls, v: str) -> str:
        """Valida tipo_evento contra la ontologia vigente.

        Args:
            v: Valor recibido para tipo_evento.

        Returns:
            El mismo valor, si es valido.

        Raises:
            ValueError: Si el valor no esta en la ontologia vigente.

        """
        if v not in ONTOLOGIA.tipos_evento:
            raise ValueError(f"tipo_evento no esta en la ontologia vigente: {v}")
        return v

    @field_validator("servicio_de_respuesta")
    @classmethod
    def _validar_servicios(cls, v: list[str]) -> list[str]:
        """Valida servicio_de_respuesta contra la ontologia vigente.

        Args:
            v: Lista de codigos de servicio recibida.

        Returns:
            La misma lista, si todos los valores son validos.

        Raises:
            ValueError: Si algun valor no es un servicio reportable.

        """
        invalidos = set(v) - ONTOLOGIA.servicios_de_respuesta
        if invalidos:
            raise ValueError(f"servicio_de_respuesta no reportable: {invalidos}")
        return v


class UbicacionExtraida(BaseModel):
    """Capa 3 (extraccion): ubicacion tal como la nombra el mensaje.

    Solo contiene texto: la resolucion a barrio, comuna, nivel de granularidad
    y coordenadas la hace Geo de forma determinista. El modelo nunca geocodifica
    ni decide territorio.
    """

    ubicacion_texto_literal: str
    punto_referencia: str | None = None


class Ubicacion(BaseModel):
    """Capa 3 (resuelta): ubicacion con la resolucion geografica de Geo."""

    ubicacion_texto_literal: str
    barrio: str | None
    comuna: str | None
    punto_referencia: str | None
    nivel_granularidad: Literal["exacta", "barrio", "comuna", "ciudad", "indeterminada"]
    lat: float | None
    lon: float | None


class ReporteEstructurado(BaseModel):
    """Registro completo persistido por CRUD y consultado por BFF/Frontend."""

    id: str
    fuente: Literal["telegram"]
    id_externo: str
    autor_anonimizado_id: str
    mensaje_anonimizado: str
    estado_revision: Literal["pendiente", "revisado"]
    compuerta: Compuerta
    naturaleza: Naturaleza | None
    ubicacion: Ubicacion | None
    creado_en: datetime

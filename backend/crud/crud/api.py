"""Modelos HTTP del servicio CRUD (request/response de docs/CONTRATOS_SISTEMA.md).

La forma exacta de cada respuesta sigue la seccion 2 del contrato; los campos
`accionable`, `lat`, `lon` y los seis agregados nuevos de `/reportes/resumen`
corresponden a la revision aceptada por el equipo (PR #36) y se documentan en
este mismo modulo.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from sirena_schema.schema import ReporteEstructurado


class ReporteResumen(BaseModel):
    """Fila de la version resumida de `GET /reportes`.

    No incluye `mensaje_anonimizado` ni `punto_referencia` (carga rapida de la
    bandeja); si incluye `accionable`, `lat` y `lon` para el tablero.
    """

    id: str
    tipo_evento: str | None = None
    servicio_de_respuesta: list[str] = Field(default_factory=list)
    comuna: str | None = None
    barrio: str | None = None
    temporalidad: str
    intencion: str
    estado_revision: str
    nivel_granularidad: str | None = None
    accionable: bool | None = None
    lat: float | None = None
    lon: float | None = None
    creado_en: datetime


class PaginaReportes(BaseModel):
    """Respuesta paginada de `GET /reportes`."""

    total: int
    pagina: int
    tamano_pagina: int
    resultados: list[ReporteResumen]


class ResumenReportes(BaseModel):
    """Respuesta de `GET /reportes/resumen` (agregados del tablero)."""

    total: int
    pendientes: int
    revisados: int
    por_tipo_evento: dict[str, int] = Field(default_factory=dict)
    por_comuna: dict[str, int] = Field(default_factory=dict)
    por_accionable: dict[str, int] = Field(default_factory=dict)
    por_temporalidad: dict[str, int] = Field(default_factory=dict)
    por_intencion: dict[str, int] = Field(default_factory=dict)
    por_servicio_de_respuesta: dict[str, int] = Field(default_factory=dict)
    por_nivel_granularidad: dict[str, int] = Field(default_factory=dict)
    por_dia: dict[str, int] = Field(default_factory=dict)


class CorreccionRequest(BaseModel):
    """Cuerpo de `PATCH /reportes/{id}`."""

    estado_revision: Literal["pendiente", "revisado"] | None = None
    correccion: dict[str, object] | None = None


def a_resumen(reporte: ReporteEstructurado) -> ReporteResumen:
    """Proyecta un `ReporteEstructurado` a la forma resumida de listado.

    Args:
        reporte: Reporte completo.

    Returns:
        La version resumida, con `accionable`/`lat`/`lon` para el tablero.

    """
    return ReporteResumen(
        id=reporte.id,
        tipo_evento=reporte.naturaleza.tipo_evento if reporte.naturaleza else None,
        servicio_de_respuesta=(
            reporte.naturaleza.servicio_de_respuesta if reporte.naturaleza else []
        ),
        comuna=reporte.ubicacion.comuna if reporte.ubicacion else None,
        barrio=reporte.ubicacion.barrio if reporte.ubicacion else None,
        temporalidad=reporte.compuerta.temporalidad,
        intencion=reporte.compuerta.intencion,
        estado_revision=reporte.estado_revision,
        nivel_granularidad=(reporte.ubicacion.nivel_granularidad if reporte.ubicacion else None),
        accionable=reporte.compuerta.es_reporte_accionable,
        lat=reporte.ubicacion.lat if reporte.ubicacion else None,
        lon=reporte.ubicacion.lon if reporte.ubicacion else None,
        creado_en=reporte.creado_en,
    )

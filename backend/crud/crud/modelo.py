"""Modelo SQLAlchemy de `ReporteEstructurado` para persistencia en SQLite.

Se deriva del esquema Pydantic de T-02 (ver `sirena_schema.schema`): la fila
guarda el payload JSON completo del reporte (`payload_json`) más columnas
espejo indexadas de los campos de filtrado. Las columnas espejo permiten
filtrar y agregar con SQL directo (sin JSON path por expresión), y se derivan
una sola vez al insertar/actualizar.
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sirena_schema.schema import Naturaleza, ReporteEstructurado, Ubicacion

TAMANO_PAGINA_MAXIMO = 100
TAMANO_PAGINA_DEFAULT = 20


class Base(DeclarativeBase):
    """Base declarativa compartida por los modelos del CRUD."""


class Reporte(Base):
    """Representación relacional de un `ReporteEstructurado`.

    Guarda el payload JSON completo (`payload`) y columnas espejo indexadas de
    los campos de filtrado, derivadas al insertar/actualizar para que las
    consultas usen SQL directo.
    """

    __tablename__ = "reportes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    fuente: Mapped[str] = mapped_column(String(16))
    id_externo: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    autor_anonimizado_id: Mapped[str] = mapped_column(String(128), index=True)
    mensaje_anonimizado: Mapped[str] = mapped_column(Text)
    estado_revision: Mapped[str] = mapped_column(String(16), index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, index=True)
    tipo_evento: Mapped[str | None] = mapped_column(String(64), index=True)
    accionable: Mapped[bool | None] = mapped_column(Boolean, index=True)
    temporalidad: Mapped[str | None] = mapped_column(String(32), index=True)
    intencion: Mapped[str | None] = mapped_column(String(32), index=True)
    comuna: Mapped[str | None] = mapped_column(String(64), index=True)
    barrio: Mapped[str | None] = mapped_column(String(64), index=True)
    nivel_granularidad: Mapped[str | None] = mapped_column(String(16), index=True)
    servicios: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[str] = mapped_column(Text)

    @classmethod
    def desde_pydantic(cls, reporte: ReporteEstructurado) -> "Reporte":
        """Construye un modelo a partir de un reporte del esquema Pydantic.

        Args:
            reporte: Reporte a persistir.

        Returns:
            Un `Reporte` (sin asignar sesión) con columnas espejo derivadas.

        """
        naturaleza: Naturaleza | None = reporte.naturaleza
        ubicacion: Ubicacion | None = reporte.ubicacion
        return cls(
            id=reporte.id,
            fuente=reporte.fuente,
            id_externo=reporte.id_externo,
            autor_anonimizado_id=reporte.autor_anonimizado_id,
            mensaje_anonimizado=reporte.mensaje_anonimizado,
            estado_revision=reporte.estado_revision,
            creado_en=reporte.creado_en,
            tipo_evento=naturaleza.tipo_evento if naturaleza else None,
            accionable=reporte.compuerta.es_reporte_accionable,
            temporalidad=reporte.compuerta.temporalidad,
            intencion=reporte.compuerta.intencion,
            comuna=ubicacion.comuna if ubicacion else None,
            barrio=ubicacion.barrio if ubicacion else None,
            nivel_granularidad=ubicacion.nivel_granularidad if ubicacion else None,
            servicios=(json.dumps(naturaleza.servicio_de_respuesta) if naturaleza else None),
            payload=reporte.model_dump_json(),
        )

    def a_pydantic(self) -> ReporteEstructurado:
        """Recupera el `ReporteEstructurado` completo desde el payload JSON.

        Returns:
            El reporte reconstruido tal como se persistió.

        """
        return ReporteEstructurado.model_validate_json(self.payload)

"""Punto de entrada FastAPI del servicio Geo.

Implementa la resolucion geografica determinista (ver docs/CONTRATOS_SISTEMA.md,
seccion 5). No invoca al LLM.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from geo.geocodificador import Geocodificador, NivelGranularidad
from geo.gazetteer import Gazetteer
from geo.nominatim import NominatimResolver

app = FastAPI(title="SIRENA - Geo")

_gazetteer_inicial = Gazetteer()
_externo_inicial = NominatimResolver()
_geocodificador_actual = Geocodificador(_gazetteer_inicial, _externo_inicial)


class SolicitudResolver(BaseModel):
    """Cuerpo de POST /resolver."""

    ubicacion_texto_literal: str
    punto_referencia: str | None = None


class RespuestaResolver(BaseModel):
    """Respuesta normalizada de POST /resolver."""

    barrio: str | None = None
    comuna: str | None = None
    nivel_granularidad: NivelGranularidad
    lat: float | None = None
    lon: float | None = None


def obtener_geocodificador() -> Geocodificador:
    """Devuelve el geocodificador activo del servicio.

    Returns:
        Geocodificador con el catalogo y el respaldo externo configurados.

    """
    return _geocodificador_actual


def fijar_geocodificador(geocodificador: Geocodificador | None = None) -> None:
    """Intercambia el geocodificador activo; lo usan las pruebas.

    Args:
        geocodificador: Nuevo geocodificador. Si es None se restaura el que fue
            configurado al iniciar el servicio.

    """
    global _geocodificador_actual
    if geocodificador is None:
        geocodificador = Geocodificador(_gazetteer_inicial, _externo_inicial)
    _geocodificador_actual = geocodificador


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}


@app.post("/resolver", response_model=RespuestaResolver)
def resolver(
    solicitud: SolicitudResolver,
    geocodificador: Geocodificador = Depends(obtener_geocodificador),
) -> RespuestaResolver:
    """Resuelve una ubicacion libre a barrio, comuna y coordenadas.

    Args:
        solicitud: Texto libre de la ubicacion y referencia opcional.
        geocodificador: Resolutor activo inyectado por FastAPI.

    Returns:
        Resolucion con el nivel de granularidad mas especifico defendible.

    """
    resolucion = geocodificador.resolver(
        ubicacion_texto_literal=solicitud.ubicacion_texto_literal,
        punto_referencia=solicitud.punto_referencia,
    )
    return RespuestaResolver(**asdict(resolucion))

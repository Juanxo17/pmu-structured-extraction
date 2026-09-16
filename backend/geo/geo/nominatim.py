"""Adaptador externo de geocodificacion sobre Nominatim vía geopy."""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from typing import Protocol

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

ENV_URL = "NOMINATIM_URL"
ENV_USER_AGENT = "NOMINATIM_USER_AGENT"
ENV_COUNTRY_CODES = "NOMINATIM_COUNTRY_CODES"
ENV_TIMEOUT = "NOMINATIM_TIMEOUT"
ENV_MIN_INTERVAL = "NOMINATIM_MIN_INTERVAL"

_URL_POR_DEFECTO = "https://nominatim.openstreetmap.org"
_USER_AGENT_POR_DEFECTO = "sirena-geo/0.1"
_PAISES_POR_DEFECTO = "CO"
_TIMEOUT_POR_DEFECTO = 10
_MINIMO_INTERVALO_POR_DEFECTO = 1.0
_CAJA_URBANA_DE_CALI = [[3.30, -76.60], [3.58, -76.40]]

_NOMBRE_COMUNA = re.compile(r"comuna\s+(\d{1,2})", re.IGNORECASE)


@dataclass(frozen=True)
class ResultadoExterno:
    """Resultado de una geocodificacion externa exitosa."""

    lat: float
    lon: float
    barrio: str | None = None
    comuna: str | None = None


class ResolverExterno(Protocol):
    """Contrato de un geocodificador externo independiente del gazetteer."""

    def geocodificar(self, texto: str) -> ResultadoExterno | None:
        """Resuelve un texto a un resultado geografico externo.

        Args:
            texto: Descripcion libre de una ubicacion.

        Returns:
            El resultado, o None si no se puede resolver.

        """
        ...


def _nombre_comuna_desde(texto: str | None) -> str | None:
    """Extrae el nombre canonico de la comuna de un campo de direccion.

    Args:
        texto: Campo de direccion de Nominatim (ej. "Comuna 03").

    Returns:
        "Comuna N" con el numero sin ceros a la izquierda, o None si el texto
        no menciona una comuna.

    """
    if not texto:
        return None
    coincidencia = _NOMBRE_COMUNA.search(texto)
    if coincidencia is None:
        return None
    return f"Comuna {int(coincidencia.group(1))}"


class NominatimResolver(ResolverExterno):
    """Geocodificador externo con cache y respeto al uso aceptable.

    Adopta las buenas practicas de Nominatim: cache en memoria para evitar
    consultas repetidas y un intervalo minimo entre llamadas.
    """

    def __init__(
        self,
        url: str | None = None,
        user_agent: str | None = None,
        country_codes: str | None = None,
        timeout: int | None = None,
        min_interval: float | None = None,
    ) -> None:
        """Configura el adaptador; lo parametros explícitos vencen al entorno.

        Args:
            url: URL base del servidor Nominatim (env ``NOMINATIM_URL``).
            user_agent: Identificador del cliente (env ``NOMINATIM_USER_AGENT``).
            country_codes: Codigos de pais ISO 3166-1 (env ``NOMINATIM_COUNTRY_CODES``).
            timeout: Segundos de espera por llamada (env ``NOMINATIM_TIMEOUT``).
            min_interval: Segundos minimos entre llamadas consecutivas.

        """
        self._url = url or os.environ.get(ENV_URL, _URL_POR_DEFECTO)
        self._user_agent = user_agent or os.environ.get(ENV_USER_AGENT, _USER_AGENT_POR_DEFECTO)
        self._country_codes = country_codes or os.environ.get(
            ENV_COUNTRY_CODES, _PAISES_POR_DEFECTO
        )
        cadena_timeout = os.environ.get(ENV_TIMEOUT)
        self._timeout = timeout or (int(cadena_timeout) if cadena_timeout else _TIMEOUT_POR_DEFECTO)
        cadena_intervalo = os.environ.get(ENV_MIN_INTERVAL)
        self._min_interval = min_interval or (
            float(cadena_intervalo) if cadena_intervalo else _MINIMO_INTERVALO_POR_DEFECTO
        )
        self._cache: dict[str, ResultadoExterno | None] = {}
        self._candado = threading.Lock()
        sin_limite = self._geocodificar_sin_limite
        self._con_limite = RateLimiter(sin_limite, min_delay_seconds=self._min_interval)

    def geocodificar(self, texto: str) -> ResultadoExterno | None:
        """Resuelve un texto a coordenadas y comuna, consultando solo el cache.

        Args:
            texto: Descripcion libre de una ubicacion.

        Returns:
            El resultado externo, o None si no se puede resolver. Nunca lanza
            por fallas de red: se degrada a None para no inventar un valor.

        """
        texto_limpio = texto.strip()
        if not texto_limpio:
            return None
        with self._candado:
            if texto_limpio in self._cache:
                return self._cache[texto_limpio]
            try:
                resultado = self._con_limite(texto_limpio)
            except GeocoderServiceError:
                resultado = None
            self._cache[texto_limpio] = resultado
            return resultado

    def _geocodificar_sin_limite(self, texto: str) -> ResultadoExterno | None:
        """Consulta el servicio y traduce su respuesta (sin politeness).

        Args:
            texto: Descripcion libre de una ubicacion.

        Returns:
            El resultado externo, o None si el servicio no encuentra nada.

        """
        geolocalizador = Nominatim(user_agent=self._user_agent)
        ubicacion = geolocalizador.geocode(
            query=texto,
            addressdetails=True,
            language="es",
            country_codes=self._country_codes,
            viewbox=_CAJA_URBANA_DE_CALI,
            bounded=True,
            timeout=self._timeout,
        )
        if ubicacion is None:
            return None
        direccion = ubicacion.raw.get("address", {})
        barrio = direccion.get("neighbourhood") or direccion.get("suburb")
        comuna = _nombre_comuna_desde(direccion.get("city_district"))
        return ResultadoExterno(
            lat=ubicacion.latitude,
            lon=ubicacion.longitude,
            barrio=barrio,
            comuna=comuna,
        )

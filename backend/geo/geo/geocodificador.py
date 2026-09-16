"""Orquestacion determinista de la resolucion geografica de una ubicacion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from geo.gazetteer import Barrio, Gazetteer
from geo.normalizacion import normalizar
from geo.nominatim import ResolverExterno

NivelGranularidad = Literal["exacta", "barrio", "comuna", "ciudad", "indeterminada"]


@dataclass(frozen=True)
class ResolucionGeografica:
    """Resultado normalizado de la resolucion de una ubicacion libre."""

    barrio: str | None
    comuna: str | None
    nivel_granularidad: NivelGranularidad
    lat: float | None
    lon: float | None


class Geocodificador:
    """Resuelve ubicaciones usando primero el gazetteer y luego el externo.

    La resolucion es determinista: un mismo texto produce siempre el mismo
    resultado. Nunca inventa un valor: si nada es defendible, devuelve
    ``nivel_granularidad="indeterminada"`` con campos vacios.
    """

    def __init__(self, gazetteer: Gazetteer, externo: ResolverExterno | None = None) -> None:
        """Configura el geocodificador con su catalogo y su respaldo opcional.

        Args:
            gazetteer: Catalogo determinista de comunas, barrios y sectores.
            externo: Respaldo geografico externo (Nominatim por defecto).

        """
        self._gazetteer = gazetteer
        self._externo = externo

    def resolver(
        self, ubicacion_texto_literal: str, punto_referencia: str | None = None
    ) -> ResolucionGeografica:
        """Resuelve la ubicacion libre a barrio, comuna y coordenadas.

        El gazetteer tiene prioridad; solo si este no encuentra nada se consulta
        al resolutor externo. Ante una ubicacion vacia se retorna
        ``indeterminada``.

        Args:
            ubicacion_texto_literal: Texto libre de la ubicacion extraido por el
                LLM.
            punto_referencia: Referencia complementaria opcional (un barrio, un
                lugar cercano).

        Returns:
            Resolucion con el nivel mas especifico defendible.

        """
        texto = f"{ubicacion_texto_literal} {punto_referencia or ''}"
        texto_norm = normalizar(texto)
        if not texto_norm:
            return ResolucionGeografica(None, None, "indeterminada", None, None)
        local = self._resolver_con_gazetteer(texto_norm)
        if local is not None:
            return local
        if self._externo is not None:
            externo = self._resolver_con_externo(texto)
            if externo is not None:
                return externo
        return ResolucionGeografica(None, None, "indeterminada", None, None)

    def _resolver_con_gazetteer(self, texto_norm: str) -> ResolucionGeografica | None:
        """Resuelve la ubicacion contra el catalogo local, si es posible.

        Args:
            texto_norm: Texto normalizado de la ubicacion.

        Returns:
            Resolucion basada en datos propios, o None si nada coincide.

        """
        barrios = self._gazetteer.barrios_en_texto(texto_norm)
        if barrios:
            barrio = self._elegir_barrio(barrios, texto_norm)
            comuna = self._gazetteer.comuna(barrio.comuna_codigo)
            return ResolucionGeografica(
                barrio=barrio.nombre,
                comuna=comuna.nombre if comuna else None,
                nivel_granularidad="barrio",
                lat=barrio.lat,
                lon=barrio.lon,
            )
        comunas = self._gazetteer.comunas_por_numero(texto_norm)
        if comunas:
            comuna = comunas[0]
            return ResolucionGeografica(
                barrio=None,
                comuna=comuna.nombre,
                nivel_granularidad="comuna",
                lat=comuna.lat,
                lon=comuna.lon,
            )
        if self._gazetteer.menciona_ciudad(texto_norm):
            centroide = self._gazetteer.ciudad
            return ResolucionGeografica(
                barrio=None,
                comuna=None,
                nivel_granularidad="ciudad",
                lat=centroide.lat,
                lon=centroide.lon,
            )
        return None

    def _resolver_con_externo(self, texto: str) -> ResolucionGeografica | None:
        """Resuelve la ubicacion con el respaldo externo, si tiene exito.

        Args:
            texto: Texto completo de la ubicacion, incluyendo la referencia.

        Returns:
            Resolucion de nivel ``exacta`` con lo que reporte el externo, o None
            si el externo no encuentra nada.

        """
        resultado = self._externo.geocodificar(texto)
        if resultado is None:
            return None
        return ResolucionGeografica(
            barrio=resultado.barrio,
            comuna=resultado.comuna,
            nivel_granularidad="exacta",
            lat=resultado.lat,
            lon=resultado.lon,
        )

    def _elegir_barrio(self, barrios: list[Barrio], texto_norm: str) -> Barrio:
        """Elige el barrio mas especifico y determinista entre los candidatos.

        El nombre mas largo es el mas especifico; si persiste una ambiguedad de
        comuna (mismo nombre en varias comunas) se prefiere la mencionada en el
        texto y, en ultima instancia, la de codigo menor.

        Args:
            barrios: Candidatos hallados por el gazetteer.
            texto_norm: Texto normalizado de la ubicacion.

        Returns:
            El barrio seleccionado.

        """
        nombres = {barrio.nombre for barrio in barrios}
        nombre = max(nombres, key=len)
        candidatos = sorted(
            (barrio for barrio in barrios if barrio.nombre == nombre),
            key=lambda barrio: barrio.comuna_codigo,
        )
        if len(candidatos) == 1:
            return candidatos[0]
        comunas_mencionadas = {
            comuna.codigo for comuna in self._gazetteer.comunas_por_numero(texto_norm)
        }
        for barrio in candidatos:
            if barrio.comuna_codigo in comunas_mencionadas:
                return barrio
        return candidatos[0]

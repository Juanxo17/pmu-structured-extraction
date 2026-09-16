"""Centroides de las 22 comunas de Cali, exclusivos de los mapas del tablero.

`GET /reportes` (versión resumida) no confirma `lat`/`lon` todavía — ver
"Propuesto" en `docs/CONTRATOS_SISTEMA.md`. `ubicar_en_mapa` usa esta tabla
como respaldo cuando un reporte no trae coordenada exacta (o mientras el
campo no exista); no sustituye la resolución geográfica real de Geo
(`POST /resolver`) ni debe usarse para nada distinto de ubicar puntos en un
mapa.

Los centroides son el promedio ponderado por área de los polígonos
oficiales de la capa `dapm:pdt_dpa_comunas` del IDESC (Geoportal de
Planeación Municipal de Cali, http://idesc.cali.gov.co), no una
aproximación a mano — por eso cubren las 22, no solo las que aparecían en
el dataset de ejemplo original.
"""

from __future__ import annotations

_CENTROIDES_COMUNA: dict[str, tuple[float, float]] = {
    "Comuna 1": (3.4548, -76.5654),
    "Comuna 2": (3.4750, -76.5249),
    "Comuna 3": (3.4496, -76.5329),
    "Comuna 4": (3.4696, -76.5093),
    "Comuna 5": (3.4720, -76.4953),
    "Comuna 6": (3.4856, -76.4879),
    "Comuna 7": (3.4564, -76.4882),
    "Comuna 8": (3.4463, -76.5060),
    "Comuna 9": (3.4413, -76.5261),
    "Comuna 10": (3.4192, -76.5277),
    "Comuna 11": (3.4230, -76.5147),
    "Comuna 12": (3.4345, -76.5018),
    "Comuna 13": (3.4276, -76.4931),
    "Comuna 14": (3.4252, -76.4773),
    "Comuna 15": (3.4049, -76.5005),
    "Comuna 16": (3.4041, -76.5139),
    "Comuna 17": (3.3856, -76.5299),
    "Comuna 18": (3.3818, -76.5530),
    "Comuna 19": (3.4207, -76.5464),
    "Comuna 20": (3.4200, -76.5592),
    "Comuna 21": (3.4239, -76.4709),
    "Comuna 22": (3.3507, -76.5368),
}

COMUNAS_CONOCIDAS: list[str] = sorted(_CENTROIDES_COMUNA, key=lambda c: int(c.split()[-1]))


def centroide(comuna: str | None) -> tuple[float, float] | None:
    """Devuelve el centroide aproximado (lat, lon) de una comuna de Cali.

    Args:
        comuna: Nombre de la comuna tal como lo persiste CRUD (ej. "Comuna 13").

    Returns:
        Una tupla (lat, lon), o None si la comuna es None o no está en la
        tabla local (por ejemplo, si Geo normalizó a nivel de barrio con un
        nombre que aún no agregamos aquí).

    """
    if comuna is None:
        return None
    return _CENTROIDES_COMUNA.get(comuna)


def ubicar_en_mapa(
    lat: float | None, lon: float | None, comuna: str | None
) -> tuple[float, float] | None:
    """Resuelve dónde plantar un punto en el mapa: exacto si existe, si no por comuna.

    Usa la coordenada exacta (`lat`/`lon`, propuesta — ver
    docs/CONTRATOS_SISTEMA.md) cuando ya está disponible; si no, cae al
    centroide de la comuna.

    Args:
        lat: Latitud exacta, o None si no se conoce.
        lon: Longitud exacta, o None si no se conoce.
        comuna: Comuna resuelta, usada como respaldo.

    Returns:
        Una tupla `(lat, lon)`, o `None` si no hay forma de ubicar el punto.

    """
    if lat is not None and lon is not None:
        return (lat, lon)
    return centroide(comuna)

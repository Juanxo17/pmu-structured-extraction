"""Centroides aproximados de comunas de Cali, exclusivos de los mapas del tablero.

`GET /reportes` (versión resumida) no confirma `lat`/`lon` todavía — ver
"Propuesto" en `docs/CONTRATOS_SISTEMA.md`. `ubicar_en_mapa` usa esta tabla
como respaldo cuando un reporte no trae coordenada exacta (o mientras el
campo no exista); no sustituye la resolución geográfica real de Geo
(`POST /resolver`) ni debe usarse para nada distinto de ubicar puntos en un
mapa.
"""

from __future__ import annotations

_CENTROIDES_COMUNA: dict[str, tuple[float, float]] = {
    "Comuna 1": (3.4698, -76.5602),
    "Comuna 3": (3.4519, -76.5324),
    "Comuna 6": (3.4762, -76.5138),
    "Comuna 7": (3.4841, -76.4987),
    "Comuna 13": (3.4407, -76.4896),
    "Comuna 15": (3.4215, -76.4931),
    "Comuna 18": (3.3813, -76.5497),
    "Comuna 19": (3.3987, -76.5462),
    "Comuna 20": (3.4437, -76.5661),
}

COMUNAS_CONOCIDAS: list[str] = sorted(_CENTROIDES_COMUNA)


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

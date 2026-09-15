"""Centroides aproximados de comunas de Cali, exclusivos del mapa de la Bandeja.

`GET /reportes` (versión resumida) no incluye `lat`/`lon` hoy — ver
`docs/CONTRATOS_SISTEMA.md`. Esta tabla es una conveniencia local del frontend
para poder dibujar un mapa mientras ese campo no se agrega al contrato; no
sustituye la resolución geográfica real de Geo (`POST /resolver`) ni debe
usarse para nada distinto de ubicar puntos en el mapa de la Bandeja.
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

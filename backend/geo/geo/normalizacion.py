"""Normalizacion de texto para la busqueda determinista en el gazetteer."""

from __future__ import annotations

import re
import unicodedata

_SEPARADOR = re.compile(r"[^a-z0-9]+")


def normalizar(texto: str) -> str:
    """Normaliza un texto para comparar sin distinguir mayusculas ni acentos.

    Args:
        texto: Texto crudo proveniente del bloque de ubicacion.

    Returns:
        Texto en minusculas, sin acentos ni puntuacion y con un unico espacio
        entre palabras. Un texto vacio produce una cadena vacia.

    """
    sin_acentos = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )
    palabras = _SEPARADOR.split(sin_acentos.lower())
    return " ".join(palabra for palabra in palabras if palabra)

"""Catalogo determinista de comunas, barrios y sectores de Cali.

La informacion proviene de la DIVIPOLA del IDESC (acuerdo 0636 de 2026) y se
empaqueta en ``backend/geo/data/gazetteer.json`` con centroides en EPSG:4326.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from geo.normalizacion import normalizar

_GAZETTEER_POR_DEFECTO = Path(__file__).resolve().parent.parent / "data" / "gazetteer.json"
_COMUNA_MENCIONADA = re.compile(r"\bcomuna\s+(\d{1,2})\b")
_CIUDAD = "Santiago de Cali"


@dataclass(frozen=True)
class Comuna:
    """Comuna de Cali con su centroide en EPSG:4326."""

    codigo: int
    lat: float
    lon: float

    @property
    def nombre(self) -> str:
        """Nombre canonico de la comuna, tal como lo persiste CRUD.

        Returns:
            Cadena del tipo "Comuna 13".

        """
        return f"Comuna {self.codigo}"


@dataclass(frozen=True)
class Barrio:
    """Barrio o sector de Cali con su comuna y centroide."""

    codigo: int
    nombre: str
    comuna_codigo: int
    categoria: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Ciudad:
    """Punto de referencia de la ciudad para resoluciones a nivel ciudad."""

    lat: float
    lon: float


class Gazetteer:
    """Indices normalizados sobre el archivo de datos geograficos del IDESC."""

    def __init__(self, ruta: str | None = None) -> None:
        """Carga el gazetteer y construye los indices de busqueda.

        Args:
            ruta: Ubicacion del ``gazetteer.json``. Si no se indica, se usa la
                variable de entorno ``GAZETTEER_PATH`` o el archivo empaquetado
                con el servicio.

        """
        ruta_resuelta = ruta or os.environ.get("GAZETTEER_PATH") or str(_GAZETTEER_POR_DEFECTO)
        with open(ruta_resuelta, encoding="utf-8") as archivo:
            datos = json.load(archivo)

        self.ruta = ruta_resuelta
        self.comunas = {
            comuna["codigo"]: Comuna(
                codigo=comuna["codigo"],
                lat=comuna["centroide"][0],
                lon=comuna["centroide"][1],
            )
            for comuna in datos["comunas"]
        }
        self.barrios = [
            Barrio(
                codigo=barrio["codigo"],
                nombre=barrio["nombre"],
                comuna_codigo=barrio["comuna"],
                categoria=barrio["categoria"],
                lat=barrio["centroide"][0],
                lon=barrio["centroide"][1],
            )
            for barrio in datos["barrios"]
        ]
        self._barrios_por_nombre_norm = [
            (barrio, normalizar(barrio.nombre)) for barrio in self.barrios
        ]
        self.ciudad = Ciudad(lat=3.449568, lon=-76.532882)

    def comuna(self, codigo: int) -> Comuna | None:
        """Devuelve la comuna con el codigo dado.

        Args:
            codigo: Numero de comuna (1 a 22).

        Returns:
            La comuna, o None si el codigo no existe.

        """
        return self.comunas.get(codigo)

    def barrios_en_texto(self, texto_norm: str) -> list[Barrio]:
        """Barrios y sectores cuyo nombre aparece entero en el texto normalizado.

        El nombre debe aparecer como una secuencia completa de palabras, no
        como un prefijo ni un fragmento de otra palabra.

        Args:
            texto_norm: Texto normalizado (ver ``normalizar``).

        Returns:
            Lista de barrios/sectores coincidentes, en orden de aparicion en el
            catalogo.

        """
        texto_almohadilla = f" {texto_norm} "
        return [
            barrio
            for barrio, nombre_norm in self._barrios_por_nombre_norm
            if f" {nombre_norm} " in texto_almohadilla
        ]

    def comunas_por_numero(self, texto_norm: str) -> list[Comuna]:
        """Comunas mencionadas de forma explicita en el texto normalizado.

        Solo reconoce la forma "comuna N" o "comuna 0N".

        Args:
            texto_norm: Texto normalizado.

        Returns:
            Lista de comunas mencionadas, sin repeticiones.

        """
        comunas: list[Comuna] = []
        vistos: set[int] = set()
        for codigo in _COMUNA_MENCIONADA.findall(texto_norm):
            numero = int(codigo)
            if numero in vistos:
                continue
            comuna = self.comunas.get(numero)
            if comuna is None:
                continue
            vistos.add(numero)
            comunas.append(comuna)
        return comunas

    def menciona_ciudad(self, texto_norm: str) -> bool:
        """Indica si el texto menciona la ciudad de Cali.

        Args:
            texto_norm: Texto normalizado.

        Returns:
            True si el texto contiene la palabra "cali".

        """
        token_ciudad = _CIUDAD.split()[-1].lower()
        return f" {token_ciudad} " in f" {texto_norm} "

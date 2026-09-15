"""Anonimizacion de datos personales (Ley 1581 de 2012).

Este modulo recibe el texto crudo de un mensaje ciudadano y devuelve una
version sin datos que identifiquen a una persona: nombres propios y
telefonos.

DECISION DE EQUIPO: NO se anonimiza ningun dato de ubicacion/direccion,
estructurada o no -- se trata como informacion de entrada necesaria para
el pipeline (Inference/Geo), nunca como dato personal a suprimir. Esto se
aparta de la redaccion literal de `.specify/memory/constitution.md`
("direcciones exactas" listada junto a nombres/telefonos como dato a
anonimizar segun Ley 1581) -- pendiente de comunicar al equipo y, si se
mantiene, actualizar ese documento en el mismo PR (regla de gobernanza de
la propia constitucion).

Enfoque hibrido:
- Telefonos: expresion regular (deterministico, sin dependencia de
  ningun modelo).
- Nombres de persona: NER con spaCy (es_core_news_md), porque una lista
  fija de nombres no cubre nombres poco comunes o combinaciones nuevas.

Limitacion conocida (verificada empiricamente, no solo teorica): se
consideraron las etiquetas PER y MISC como candidatas a nombre de persona,
porque en pruebas algunos nombres reales ("Yhon Alexander") caen en MISC
en vez de PER. Sin embargo, MISC tambien atrapa menciones generales de via
sin numero de vivienda (ej. "Carrera 1", "Calle 5"), lo que destruiria
ubicacion util. Se prioriza no romper la extraccion de ubicacion sobre
capturar el 100% de los nombres: solo se enmascara PER. El costo es que
algunos nombres poco comunes pueden no detectarse -- se revisa el impacto
real durante la anotacion del corpus y se ajusta si hace falta.

Limitacion conocida #2: el modelo pierde precision con texto sin tildes
(comun en mensajeria informal, ej. "Andres" en vez de "Andres" con tilde).
Ver test_anonimizacion.py::test_nombre_sin_tilde_no_siempre_se_detecta,
marcado como limitacion documentada, no como bug a corregir de inmediato.
"""

import re
from functools import lru_cache

import spacy

MASCARA = "[DATO_PERSONAL]"

# Telefono colombiano: opcional +57, luego 10 digitos (movil) o 7 (fijo
# local), permitiendo espacios o guiones entre grupos.
_REGEX_TELEFONO = re.compile(
    r"(?:\+?57\s?)?(?:3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}|\d{7})\b"
)

# No hay regex de direccion -- decision de equipo: ninguna mencion de
# ubicacion/direccion se anonimiza, se trata como dato de entrada
# necesario para el pipeline, nunca como PII a suprimir. Ver docstring
# del modulo para la tension con la constitucion del proyecto.

# Etiquetas de entidad de spaCy que se tratan como "nombre de persona".
# Deliberadamente NO incluye "MISC": en pruebas tambien atrapaba menciones
# generales de via ("Carrera 1", "Calle 5") sin numero de vivienda, lo que
# habria borrado ubicacion util para Geo. Se prefiere perder algunos
# nombres poco comunes antes que romper la extraccion de ubicacion.
_ETIQUETAS_PERSONA = {"PER"}


@lru_cache(maxsize=1)
def _modelo_ner():
    """Carga el modelo de spaCy una sola vez y lo reutiliza (es lento de cargar).

    Returns:
        El pipeline de spaCy ya cargado.

    """
    return spacy.load("es_core_news_md")


def _enmascarar_nombres(texto: str) -> str:
    """Reemplaza las entidades de tipo persona detectadas por NER.

    Args:
        texto: Texto sobre el que ya se aplico el regex de telefono.

    Returns:
        Texto con los nombres de persona reemplazados por la mascara.

    """
    doc = _modelo_ner()(texto)
    resultado = texto
    # Se reemplaza de atras hacia adelante para no invalidar los indices
    # (start_char/end_char) de las entidades restantes al cambiar el largo
    # del texto con cada reemplazo.
    for ent in sorted(doc.ents, key=lambda e: e.start_char, reverse=True):
        if ent.label_ in _ETIQUETAS_PERSONA:
            resultado = resultado[: ent.start_char] + MASCARA + resultado[ent.end_char :]
    return resultado


def anonimizar_texto(texto: str) -> str:
    """Anonimiza telefonos y nombres de persona.

    No anonimiza ninguna mencion de ubicacion o direccion (decision de
    equipo, ver docstring del modulo) -- esa informacion la necesita el
    resto del pipeline (Inference, Geo).

    Args:
        texto: Texto crudo del mensaje ciudadano.

    Returns:
        Texto con los datos personales reemplazados por "[DATO_PERSONAL]".

    """
    texto = _REGEX_TELEFONO.sub(MASCARA, texto)
    texto = _enmascarar_nombres(texto)
    return texto

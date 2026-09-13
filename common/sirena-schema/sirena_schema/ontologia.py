"""Carga del vocabulario de tipo_evento y servicio_de_respuesta."""

import os
from pathlib import Path

import yaml

_RUTA_DEFECTO = Path(os.environ.get("ONTOLOGIA_PATH", "config/ontologia.yaml"))


class Ontologia:
    """Vocabulario vigente de tipo_evento y servicio_de_respuesta.

    Attributes:
        tipos_evento: Valores admitidos para el campo tipo_evento.
        servicios_de_respuesta: Valores admitidos para servicio_de_respuesta.

    """

    def __init__(self, ruta: Path = _RUTA_DEFECTO) -> None:
        """Carga la ontologia desde un archivo YAML.

        Args:
            ruta: Ruta al archivo de ontologia. Por defecto, config/ontologia.yaml
                en la raiz del repositorio.

        Raises:
            FileNotFoundError: Si el archivo no existe en la ruta indicada.

        """
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        self.tipos_evento: set[str] = set(datos["tipo_evento"])
        self.servicios_de_respuesta: set[str] = set(datos["servicio_de_respuesta"])


ONTOLOGIA = Ontologia()

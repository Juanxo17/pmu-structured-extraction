"""Pruebas del esquema Pydantic compartido."""

import pytest
from pydantic import ValidationError

from sirena_schema.schema import Naturaleza


class TestNaturaleza:
    """Pruebas de validacion de Naturaleza contra la ontologia vigente."""

    def test_acepta_tipo_evento_y_servicios_validos(self) -> None:
        """Un tipo_evento y servicios que existen en la ontologia se aceptan."""
        # Arrange
        datos = {"tipo_evento": "sismo", "servicio_de_respuesta": ["A", "G"]}

        # Act
        naturaleza = Naturaleza(**datos)

        # Assert
        assert naturaleza.tipo_evento == "sismo"
        assert naturaleza.servicio_de_respuesta == ["A", "G"]

    def test_rechaza_tipo_evento_fuera_de_la_ontologia(self) -> None:
        """Un tipo_evento inexistente en la ontologia lanza ValidationError."""
        # Arrange
        datos = {"tipo_evento": "huracan", "servicio_de_respuesta": ["A"]}

        # Act / Assert
        with pytest.raises(ValidationError):
            Naturaleza(**datos)

    def test_rechaza_servicio_de_respuesta_no_reportable(self) -> None:
        """Un codigo de servicio institucional (P/Q) no es aceptado."""
        # Arrange
        datos = {"tipo_evento": "sismo", "servicio_de_respuesta": ["P"]}

        # Act / Assert
        with pytest.raises(ValidationError):
            Naturaleza(**datos)

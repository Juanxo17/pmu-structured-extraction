"""Pruebas del validador de la salida cruda del LLM."""

import pytest

from inference.validador import RechazoSalida, validar_compuerta, validar_extraccion

COMPUERTA_VALIDA = (
    '{"es_reporte_accionable": true, "temporalidad": "ocurriendo_ahora", '
    '"intencion": "solicita_ayuda"}'
)

EXTRACCION_VALIDA = (
    '{"naturaleza": {"tipo_evento": "sismo", "servicio_de_respuesta": ["A", "G"]}, '
    '"ubicacion": {"ubicacion_texto_literal": "Calle 5 con 10", "barrio": "Centro", '
    '"comuna": "3", "punto_referencia": null, "nivel_granularidad": "exacta", '
    '"lat": null, "lon": null}}'
)


class TestValidarCompuerta:
    """Pruebas de validar_compuerta."""

    def test_retorna_compuerta_valida(self) -> None:
        """Valida un JSON conforme y devuelve el modelo."""
        # Arrange
        crudo = COMPUERTA_VALIDA

        # Act
        compuerta = validar_compuerta(crudo)

        # Assert
        assert compuerta.es_reporte_accionable is True
        assert compuerta.temporalidad == "ocurriendo_ahora"
        assert compuerta.intencion == "solicita_ayuda"

    def test_acepta_bloque_markdown(self) -> None:
        """Limpia fences de markdown alrededor del JSON."""
        # Arrange
        crudo = f"```json\n{COMPUERTA_VALIDA}\n```"

        # Act
        compuerta = validar_compuerta(crudo)

        # Assert
        assert compuerta.es_reporte_accionable is True

    def test_rechaza_json_invalido(self) -> None:
        """Lanza RechazoSalida cuando el texto no es JSON."""
        # Arrange
        crudo = "no soy un json"

        # Act / Assert
        with pytest.raises(RechazoSalida, match="JSON invalido"):
            validar_compuerta(crudo)

    def test_rechaza_objeto_no_diccionario(self) -> None:
        """Lanza RechazoSalida cuando el JSON no es un objeto."""
        # Arrange
        crudo = "[1, 2, 3]"

        # Act / Assert
        with pytest.raises(RechazoSalida, match="objeto JSON"):
            validar_compuerta(crudo)

    def test_rechaza_valor_fuera_de_literal(self) -> None:
        """Lanza RechazoSalida cuando un literal no es permitido."""
        # Arrange
        crudo = (
            '{"es_reporte_accionable": true, "temporalidad": "manana", '
            '"intencion": "solicita_ayuda"}'
        )

        # Act / Assert
        with pytest.raises(RechazoSalida, match="No conforma al esquema"):
            validar_compuerta(crudo)


class TestValidarExtraccion:
    """Pruebas de validar_extraccion."""

    def test_retorna_naturaleza_y_ubicacion(self) -> None:
        """Valida un JSON conforme y devuelve ambos modelos."""
        # Arrange
        crudo = EXTRACCION_VALIDA

        # Act
        naturaleza, ubicacion = validar_extraccion(crudo)

        # Assert
        assert naturaleza.tipo_evento == "sismo"
        assert naturaleza.servicio_de_respuesta == ["A", "G"]
        assert ubicacion.barrio == "Centro"
        assert ubicacion.nivel_granularidad == "exacta"

    def test_rechaza_falta_de_bloque(self) -> None:
        """Lanza RechazoSalida cuando falta el bloque naturaleza."""
        # Arrange
        crudo = '{"ubicacion": {"ubicacion_texto_literal": "Centro"}}'

        # Act / Assert
        with pytest.raises(RechazoSalida, match="Falta el bloque"):
            validar_extraccion(crudo)

    def test_rechaza_bloque_no_objeto(self) -> None:
        """Lanza RechazoSalida cuando un bloque no es un objeto."""
        # Arrange
        crudo = '{"naturaleza": [], "ubicacion": {}}'

        # Act / Assert
        with pytest.raises(RechazoSalida, match="deben ser objetos"):
            validar_extraccion(crudo)

    def test_rechaza_tipo_evento_fuera_de_ontologia(self) -> None:
        """Lanza RechazoSalida cuando tipo_evento no esta en la ontologia."""
        # Arrange
        crudo = (
            '{"naturaleza": {"tipo_evento": "terremoto_apocalipsis", '
            '"servicio_de_respuesta": ["A"]}, '
            '"ubicacion": {"ubicacion_texto_literal": "Centro", "barrio": null, '
            '"comuna": null, "punto_referencia": null, '
            '"nivel_granularidad": "indeterminada", "lat": null, "lon": null}}'
        )

        # Act / Assert
        with pytest.raises(RechazoSalida, match="No conforma al esquema"):
            validar_extraccion(crudo)

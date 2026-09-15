"""Pruebas del cargador de la ontologia compartida."""

from sirena_schema.ontologia import ONTOLOGIA


class TestOntologia:
    """Pruebas de Ontologia, el vocabulario vigente cargado desde el YAML."""

    def test_todo_tipo_evento_tiene_nombre_legible(self) -> None:
        """Cada tipo_evento de la ontologia tiene una entrada en nombres_tipo_evento."""
        # Arrange / Act / Assert
        assert ONTOLOGIA.tipos_evento == set(ONTOLOGIA.nombres_tipo_evento)

    def test_todo_servicio_de_respuesta_tiene_nombre_legible(self) -> None:
        """Cada código de servicio_de_respuesta tiene una entrada en su diccionario de nombres."""
        # Arrange / Act / Assert
        assert ONTOLOGIA.servicios_de_respuesta == set(ONTOLOGIA.nombres_servicio_de_respuesta)

    def test_nombre_de_sismo_es_legible(self) -> None:
        """El nombre de 'sismo' es el que se muestra en tableros, no el código interno."""
        # Arrange / Act / Assert
        assert ONTOLOGIA.nombres_tipo_evento["sismo"] == "Sismo"

    def test_nombre_del_servicio_a_es_busqueda_y_rescate(self) -> None:
        """El código 'A' se traduce a su nombre completo según la ERE de Cali."""
        # Arrange / Act / Assert
        assert ONTOLOGIA.nombres_servicio_de_respuesta["A"] == "Búsqueda y Rescate"

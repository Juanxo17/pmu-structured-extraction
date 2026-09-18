"""Pruebas del contenido de las instrucciones de sistema (prompts)."""

from typing import get_args

from sirena_schema.ontologia import ONTOLOGIA
from sirena_schema.schema import Compuerta

from inference import prompts


def _valores(campo: str) -> tuple[str, ...]:
    """Devuelve los valores Literal de un campo de Compuerta.

    Args:
        campo: Nombre del campo Literal de Compuerta.

    Returns:
        Valores admitidos por el esquema para ese campo.

    """
    return tuple(get_args(Compuerta.model_fields[campo].annotation))


def _etiquetas_servicio() -> list[str]:
    """Devuelve las etiquetas formateadas de cada servicio de respuesta.

    Returns:
        Lista con las etiquetas "Codigo Nombre" que arma el modulo.

    """
    return prompts._etiquetas_servicio().split(", ")


class TestConsultasPrompts:
    """Pruebas de la consulta de prompts de sistema."""

    def test_sistema_compuerta_nombra_la_tarea(self) -> None:
        """El prompt de compuerta describe su rol de primer filtro."""
        # Act
        prompt = prompts.sistema_compuerta()

        # Assert
        assert "SIRENA" in prompt
        assert "es_reporte_accionable" in prompt

    def test_sistema_compuerta_enumera_temporalidades(self) -> None:
        """El prompt incluye todos los valores de temporalidad del esquema."""
        # Arrange
        prompt = prompts.sistema_compuerta()

        # Act & Assert
        for valor in _valores("temporalidad"):
            assert valor in prompt

    def test_sistema_compuerta_enumera_intenciones(self) -> None:
        """El prompt incluye todos los valores de intencion del esquema."""
        # Arrange
        prompt = prompts.sistema_compuerta()

        # Act & Assert
        for valor in _valores("intencion"):
            assert valor in prompt

    def test_sistema_compuerta_incluye_ejemplos(self) -> None:
        """El prompt de compuerta trae al menos tres ejemplos few-shot."""
        # Act
        prompt = prompts.sistema_compuerta()

        # Assert
        assert prompt.count("Mensaje:") >= 3
        assert prompt.count("Salida:") >= 3

    def test_sistema_extraccion_nombra_la_tarea(self) -> None:
        """El prompt de extraccion describe su rol de extractor."""
        # Act
        prompt = prompts.sistema_extraccion()

        # Assert
        assert "SIRENA" in prompt
        assert "naturaleza" in prompt
        assert "ubicacion" in prompt

    def test_sistema_extraccion_enumera_tipos_de_evento(self) -> None:
        """El prompt incluye todos los tipo_evento de la ontologia vigente."""
        # Arrange
        prompt = prompts.sistema_extraccion()

        # Act & Assert
        for tipo in ONTOLOGIA.tipos_evento:
            assert tipo in prompt

    def test_sistema_extraccion_enumera_servicios(self) -> None:
        """El prompt incluye los codigos y nombres de los servicios."""
        # Arrange
        prompt = prompts.sistema_extraccion()

        # Act & Assert
        for etiqueta in _etiquetas_servicio():
            assert etiqueta in prompt

    def test_servicios_del_prompt_vienen_de_la_ontologia(self) -> None:
        """Los codigos de servicio del prompt son los de la ontologia."""
        # Arrange
        prompt = prompts.sistema_extraccion()

        # Act & Assert
        for codigo in ONTOLOGIA.servicios_de_respuesta:
            assert f"{codigo} " in prompt

    def test_nombres_de_servicio_cubren_la_ontologia(self) -> None:
        """Cada codigo de la ontologia tiene su nombre local."""
        # Act & Assert
        assert set(prompts._NOMBRES_SERVICIO) == ONTOLOGIA.servicios_de_respuesta

    def test_sistema_extraccion_incluye_ejemplos(self) -> None:
        """El prompt de extraccion trae al menos tres ejemplos few-shot."""
        # Act
        prompt = prompts.sistema_extraccion()

        # Assert
        assert prompt.count("Mensaje:") >= 3
        assert prompt.count("Salida:") >= 3

    def test_sistema_extraccion_no_pide_campos_geograficos(self) -> None:
        """El prompt solo pide ubicacion textual, no territorio ni coordenadas."""
        # Act
        prompt = prompts.sistema_extraccion()

        # Assert
        assert '"punto_referencia"' in prompt
        assert '"barrio"' not in prompt
        assert '"comuna"' not in prompt
        assert '"nivel_granularidad"' not in prompt
        assert '"lat"' not in prompt
        assert '"lon"' not in prompt


class TestVersionadoPrompts:
    """Pruebas del versionado de los prompts."""

    def test_version_no_esta_vacia(self) -> None:
        """La constante VERSION_PROMPTS es una cadena no vacia."""
        # Act & Assert
        assert isinstance(prompts.VERSION_PROMPTS, str)
        assert prompts.VERSION_PROMPTS.strip()

    def test_version_tiene_forma_semantica(self) -> None:
        """La version sigue el patron numerico punto numerico."""
        # Act & Assert
        partes = prompts.VERSION_PROMPTS.split(".")
        assert len(partes) == 2
        assert all(p.isdigit() for p in partes)

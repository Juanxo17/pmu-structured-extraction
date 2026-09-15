"""Pruebas de las funciones puras de la pantalla Resumen (frontend.resumen)."""

from frontend.bff_client import ResumenReportes
from frontend.resumen import (
    calcular_tasa_revision,
    construir_grafico_comuna,
    construir_grafico_tipo_evento,
)
from frontend.theme import COLOR_ACCENT, COLOR_TIPO_EVENTO


def _resumen(**overrides: object) -> ResumenReportes:
    """Construye un ResumenReportes de prueba con valores por defecto razonables.

    Args:
        **overrides: Campos a sobrescribir sobre los valores por defecto.

    Returns:
        Un ResumenReportes listo para usarse en una prueba.

    """
    base: dict[str, object] = {
        "total": 10,
        "pendientes": 4,
        "revisados": 6,
        "por_tipo_evento": {"sismo": 5, "inundacion_subita": 3, "incendio_estructural": 2},
        "por_comuna": {"Comuna 13": 4, "Comuna 20": 3, "Comuna 1": 3},
    }
    base.update(overrides)
    return ResumenReportes(**base)


class TestCalcularTasaRevision:
    """Pruebas de calcular_tasa_revision."""

    def test_calcula_el_porcentaje_de_revisados_sobre_el_total(self) -> None:
        """6 de 10 revisados da 60.0%."""
        # Arrange
        resumen = _resumen(total=10, revisados=6)

        # Act
        tasa = calcular_tasa_revision(resumen)

        # Assert
        assert tasa == 60.0

    def test_devuelve_cero_si_el_total_es_cero(self) -> None:
        """Sin reportes en el rango, la tasa es 0.0, nunca una división por cero."""
        # Arrange
        resumen = _resumen(total=0, pendientes=0, revisados=0, por_tipo_evento={}, por_comuna={})

        # Act
        tasa = calcular_tasa_revision(resumen)

        # Assert
        assert tasa == 0.0


class TestConstruirGraficoTipoEvento:
    """Pruebas de construir_grafico_tipo_evento."""

    def test_una_barra_por_categoria_con_conteo_mayor_a_cero(self) -> None:
        """Las categorías con conteo 0 no aparecen en el gráfico."""
        # Arrange
        resumen = _resumen(por_tipo_evento={"sismo": 5, "salud_ambiental": 0})

        # Act
        figura = construir_grafico_tipo_evento(resumen)

        # Assert
        assert len(figura.data[0].y) == 1
        assert figura.data[0].y[0] == "Sismo"

    def test_el_color_de_cada_barra_sigue_a_su_categoria(self) -> None:
        """El color de la barra de sismo es siempre el mismo, sin importar el ranking."""
        # Arrange
        resumen = _resumen(por_tipo_evento={"sismo": 5, "inundacion_subita": 8})

        # Act
        figura = construir_grafico_tipo_evento(resumen)

        # Assert
        colores_por_etiqueta = dict(zip(figura.data[0].y, figura.data[0].marker.color))
        assert colores_por_etiqueta["Sismo"] == COLOR_TIPO_EVENTO["sismo"]

    def test_la_categoria_con_mas_reportes_queda_al_final_de_la_lista(self) -> None:
        """Plotly dibuja barras horizontales de abajo hacia arriba: la mayor va última."""
        # Arrange
        resumen = _resumen(por_tipo_evento={"sismo": 2, "inundacion_subita": 8})

        # Act
        figura = construir_grafico_tipo_evento(resumen)

        # Assert
        assert figura.data[0].y[-1] == "Inundación súbita"


class TestConstruirGraficoComuna:
    """Pruebas de construir_grafico_comuna."""

    def test_respeta_el_top_n(self) -> None:
        """Con top_n=2 solo aparecen las 2 comunas con más reportes."""
        # Arrange
        resumen = _resumen(por_comuna={"Comuna 13": 4, "Comuna 20": 3, "Comuna 1": 9})

        # Act
        figura = construir_grafico_comuna(resumen, top_n=2)

        # Assert
        assert len(figura.data[0].y) == 2
        assert "Comuna 20" not in figura.data[0].y

    def test_usa_un_solo_color_de_acento_para_todas_las_barras(self) -> None:
        """A diferencia de tipo_evento, comuna es un ranking, no identidad: un solo hue."""
        # Arrange
        resumen = _resumen(por_comuna={"Comuna 13": 4, "Comuna 20": 3})

        # Act
        figura = construir_grafico_comuna(resumen)

        # Assert
        assert figura.data[0].marker.color == COLOR_ACCENT

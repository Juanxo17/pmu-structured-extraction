"""Pruebas de las funciones puras de la pantalla Resumen (frontend.resumen)."""

from frontend.bff_client import ResumenReportes
from frontend.resumen import (
    calcular_tasa_accionable,
    calcular_tasa_revision,
    construir_grafico_comuna,
    construir_grafico_granularidad,
    construir_grafico_intencion,
    construir_grafico_servicio,
    construir_grafico_temporalidad,
    construir_grafico_tendencia,
    construir_grafico_tipo_evento,
)
from frontend.theme import COLOR_ACCENT_PASTEL


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
        "por_accionable": {"accionable": 8, "no_accionable": 2},
        "por_temporalidad": {"ocurriendo_ahora": 3, "ya_ocurrio": 5, "riesgo_previsto": 2},
        "por_intencion": {"solicita_ayuda": 4, "reporta_terceros": 6},
        "por_servicio_de_respuesta": {"A": 5, "G": 4, "B": 2},
        "por_nivel_granularidad": {"exacta": 3, "barrio": 4, "comuna": 1},
        "por_dia": {"2026-09-14": 4, "2026-09-15": 6},
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

    def test_usa_el_mismo_color_de_acento_que_los_demas_graficos(self) -> None:
        """Todos los gráficos de Resumen comparten un único color (pedido de diseño)."""
        # Arrange
        resumen = _resumen(por_tipo_evento={"sismo": 5, "inundacion_subita": 8})

        # Act
        figura = construir_grafico_tipo_evento(resumen)

        # Assert
        assert figura.data[0].marker.color == COLOR_ACCENT_PASTEL

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
        assert figura.data[0].marker.color == COLOR_ACCENT_PASTEL


class TestCalcularTasaAccionable:
    """Pruebas de calcular_tasa_accionable."""

    def test_calcula_el_porcentaje_de_accionables(self) -> None:
        """8 accionables de 10 clasificados da 80.0%."""
        # Arrange
        resumen = _resumen(por_accionable={"accionable": 8, "no_accionable": 2})

        # Act
        tasa = calcular_tasa_accionable(resumen)

        # Assert
        assert tasa == 80.0

    def test_devuelve_cero_si_no_hay_reportes_clasificados(self) -> None:
        """Sin accionables ni no_accionables, la tasa es 0.0, nunca una división por cero."""
        # Arrange
        resumen = _resumen(por_accionable={"accionable": 0, "no_accionable": 0})

        # Act
        tasa = calcular_tasa_accionable(resumen)

        # Assert
        assert tasa == 0.0


class TestConstruirGraficoTemporalidad:
    """Pruebas de construir_grafico_temporalidad."""

    def test_incluye_una_barra_por_temporalidad_con_conteo_mayor_a_cero(self) -> None:
        """Las temporalidades sin reportes no aparecen en el gráfico."""
        # Arrange
        resumen = _resumen(por_temporalidad={"ocurriendo_ahora": 3, "referencia_noticia": 0})

        # Act
        figura = construir_grafico_temporalidad(resumen)

        # Assert
        assert len(figura.data[0].y) == 1
        assert figura.data[0].y[0] == "Ocurriendo ahora"

    def test_usa_un_solo_color_de_acento(self) -> None:
        """Temporalidad es una distribución de pocos valores fijos, no identidad: un solo hue."""
        # Arrange
        resumen = _resumen(por_temporalidad={"ocurriendo_ahora": 3, "ya_ocurrio": 5})

        # Act
        figura = construir_grafico_temporalidad(resumen)

        # Assert
        assert figura.data[0].marker.color == COLOR_ACCENT_PASTEL


class TestConstruirGraficoIntencion:
    """Pruebas de construir_grafico_intencion."""

    def test_incluye_una_barra_por_intencion_con_conteo_mayor_a_cero(self) -> None:
        """Las intenciones sin reportes no aparecen en el gráfico."""
        # Arrange
        resumen = _resumen(por_intencion={"solicita_ayuda": 4, "ofrece_ayuda": 0})

        # Act
        figura = construir_grafico_intencion(resumen)

        # Assert
        assert len(figura.data[0].y) == 1
        assert figura.data[0].y[0] == "Solicita ayuda"


class TestConstruirGraficoServicio:
    """Pruebas de construir_grafico_servicio."""

    def test_usa_el_nombre_completo_del_servicio_no_la_letra(self) -> None:
        """El eje de categorías muestra el nombre legible, no el código."""
        # Arrange
        resumen = _resumen(por_servicio_de_respuesta={"A": 5})

        # Act
        figura = construir_grafico_servicio(resumen)

        # Assert
        assert figura.data[0].y[0] == "Búsqueda y Rescate"

    def test_respeta_el_top_n(self) -> None:
        """Con top_n=1 solo aparece el servicio más solicitado."""
        # Arrange
        resumen = _resumen(por_servicio_de_respuesta={"A": 5, "G": 9, "B": 2})

        # Act
        figura = construir_grafico_servicio(resumen, top_n=1)

        # Assert
        assert len(figura.data[0].y) == 1
        assert figura.data[0].y[0] == "Salud"


class TestConstruirGraficoGranularidad:
    """Pruebas de construir_grafico_granularidad."""

    def test_usa_el_mismo_color_de_acento_que_los_demas_graficos(self) -> None:
        """Mismo color en todos los gráficos de Resumen (pedido de diseño)."""
        # Arrange
        resumen = _resumen(por_nivel_granularidad={"exacta": 3, "indeterminada": 1})

        # Act
        figura = construir_grafico_granularidad(resumen)

        # Assert
        assert figura.data[0].marker.color == COLOR_ACCENT_PASTEL


class TestConstruirGraficoTendencia:
    """Pruebas de construir_grafico_tendencia."""

    def test_ordena_los_dias_de_forma_ascendente(self) -> None:
        """Las fechas quedan en orden cronológico en el eje X, sin importar el orden del dict."""
        # Arrange
        resumen = _resumen(por_dia={"2026-09-15": 6, "2026-09-13": 2, "2026-09-14": 4})

        # Act
        figura = construir_grafico_tendencia(resumen)

        # Assert
        assert list(figura.data[0].x) == ["2026-09-13", "2026-09-14", "2026-09-15"]
        assert list(figura.data[0].y) == [2, 4, 6]

    def test_usa_el_mismo_color_de_linea_que_los_demas_graficos(self) -> None:
        """Mismo color de línea en todos los gráficos de Resumen (pedido de diseño)."""
        # Arrange
        resumen = _resumen(por_dia={"2026-09-14": 4, "2026-09-15": 6})

        # Act
        figura = construir_grafico_tendencia(resumen)

        # Assert
        assert figura.data[0].line.color == COLOR_ACCENT_PASTEL

    def test_sin_dias_da_una_serie_vacia_sin_reventar(self) -> None:
        """Sin por_dia, la figura se arma igual, sin puntos."""
        # Arrange
        resumen = _resumen(por_dia={})

        # Act
        figura = construir_grafico_tendencia(resumen)

        # Assert
        assert list(figura.data[0].x) == []

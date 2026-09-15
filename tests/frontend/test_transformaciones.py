"""Pruebas de las funciones puras de la Bandeja (frontend.bandeja)."""

from datetime import datetime, timezone

import folium
import pandas as pd
import pytest

from frontend.bandeja import (
    construir_filas_exportacion,
    construir_filas_grid,
    construir_grid_options,
    construir_mapa,
    elegir_cliente,
    exportar_csv,
    fila_seleccionada_de,
    usa_datos_de_ejemplo,
)
from frontend.bff_client import BFFClient, ReporteResumen
from frontend.reportes_mock import ClienteReportesSimulado
from frontend.theme import ICONO_ESTADO, ICONO_TIPO_EVENTO

_CREADO_EN = datetime(2026, 9, 15, 8, 0, tzinfo=timezone.utc)


def _resumen(**overrides: object) -> ReporteResumen:
    """Construye un ReporteResumen de prueba con valores por defecto razonables.

    Args:
        **overrides: Campos a sobrescribir sobre los valores por defecto.

    Returns:
        Un ReporteResumen listo para usarse en una prueba.

    """
    base = {
        "id": "rpt_1",
        "tipo_evento": "sismo",
        "servicio_de_respuesta": ["A", "G"],
        "comuna": "Comuna 20",
        "barrio": "Siloé",
        "temporalidad": "ya_ocurrio",
        "intencion": "reporta_terceros",
        "estado_revision": "pendiente",
        "nivel_granularidad": "barrio",
        "creado_en": _CREADO_EN,
    }
    base.update(overrides)
    return ReporteResumen(**base)


class TestElegirCliente:
    """Pruebas de la selección de cliente real vs. simulado según BFF_URL."""

    def test_usa_cliente_simulado_si_no_hay_bff_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sin BFF_URL, se usa el cliente con datos de ejemplo."""
        # Arrange
        monkeypatch.delenv("BFF_URL", raising=False)

        # Act
        cliente = elegir_cliente()

        # Assert
        assert isinstance(cliente, ClienteReportesSimulado)

    def test_usa_cliente_real_si_bff_url_esta_definida(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Con BFF_URL definida, se usa el cliente HTTP real."""
        # Arrange
        monkeypatch.setenv("BFF_URL", "http://bff.test")

        # Act
        cliente = elegir_cliente()

        # Assert
        assert isinstance(cliente, BFFClient)


class TestUsaDatosDeEjemplo:
    """Pruebas del indicador de modo demo usado por el pie del sidebar."""

    def test_es_true_sin_bff_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sin BFF_URL, el tablero está en modo demo."""
        # Arrange
        monkeypatch.delenv("BFF_URL", raising=False)

        # Act / Assert
        assert usa_datos_de_ejemplo() is True

    def test_es_false_con_bff_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Con BFF_URL definida, ya no es modo demo."""
        # Arrange
        monkeypatch.setenv("BFF_URL", "http://bff.test")

        # Act / Assert
        assert usa_datos_de_ejemplo() is False


class TestConstruirFilasGrid:
    """Pruebas de la proyección de resultados a filas de la tabla."""

    def test_incluye_etiqueta_e_icono_por_tipo_de_evento(self) -> None:
        """Cada fila trae la etiqueta legible y el ícono fijo de su tipo_evento.

        El ícono va como texto plano (emoji), no como HTML: un cellRenderer
        de streamlit-aggrid que inyecta HTML/DOM no es confiable en esta
        versión de la librería (ver AGENTS.md del cambio que lo reemplazó).
        """
        # Arrange
        resultados = [_resumen()]

        # Act
        filas = construir_filas_grid(resultados)

        # Assert
        assert filas[0]["tipo_evento_label"] == f"{ICONO_TIPO_EVENTO['sismo']} Sismo"
        assert filas[0]["estado_label"] == f"{ICONO_ESTADO['pendiente']} Pendiente"

    def test_columna_servicios_usa_nombres_completos_no_codigos(self) -> None:
        """La columna de servicios muestra el nombre legible, no la letra sola."""
        # Arrange
        resultados = [_resumen(servicio_de_respuesta=["A", "G"])]

        # Act
        filas = construir_filas_grid(resultados)

        # Assert
        assert filas[0]["servicios"] == "Búsqueda y Rescate, Salud"

    def test_tipo_evento_ausente_no_rompe_la_fila(self) -> None:
        """Un resultado sin naturaleza (no accionable) igual arma una fila válida."""
        # Arrange
        resultados = [_resumen(tipo_evento=None, servicio_de_respuesta=[])]

        # Act
        filas = construir_filas_grid(resultados)

        # Assert
        assert filas[0]["tipo_evento_label"] == "⚪ —"


class TestExportarCsv:
    """Pruebas de la exportación a CSV de la Bandeja."""

    def test_filas_de_exportacion_no_llevan_emoji(self) -> None:
        """A diferencia de la tabla en pantalla, las filas de exportación son texto plano."""
        # Arrange
        resultados = [_resumen()]

        # Act
        filas = construir_filas_exportacion(resultados)

        # Assert
        assert filas[0]["tipo_evento"] == "Sismo"
        assert filas[0]["estado"] == "Pendiente"

    def test_filas_de_exportacion_usan_nombres_completos_de_servicios(self) -> None:
        """Igual que en la tabla, servicios va con el nombre completo, no la letra."""
        # Arrange
        resultados = [_resumen(servicio_de_respuesta=["A", "G"])]

        # Act
        filas = construir_filas_exportacion(resultados)

        # Assert
        assert filas[0]["servicios"] == "Búsqueda y Rescate, Salud"

    def test_exportar_csv_produce_un_csv_valido_con_encabezados_esperados(self) -> None:
        """El CSV resultante se puede decodificar y trae las columnas esperadas."""
        # Arrange
        resultados = [_resumen(id="rpt_1"), _resumen(id="rpt_2", estado_revision="revisado")]

        # Act
        contenido = exportar_csv(resultados).decode("utf-8-sig")

        # Assert
        primera_linea = contenido.splitlines()[0]
        assert "id" in primera_linea
        assert "tipo_evento" in primera_linea
        assert "rpt_1" in contenido
        assert "rpt_2" in contenido


class TestConstruirGridOptions:
    """Pruebas de la configuración de AgGrid para la tabla de la Bandeja."""

    def test_configura_encabezados_de_estado_y_tipo_evento(self) -> None:
        """Las columnas de estado y tipo de evento tienen encabezado legible."""
        # Arrange
        filas = pd.DataFrame(construir_filas_grid([_resumen()]))

        # Act
        opciones = construir_grid_options(filas)

        # Assert
        columnas = {c["field"]: c for c in opciones["columnDefs"]}
        assert columnas["estado_label"]["headerName"] == "Estado"
        assert columnas["tipo_evento_label"]["headerName"] == "Tipo de evento"

    def test_columna_recibido_ordena_por_defecto(self) -> None:
        """La columna 'recibido' trae orden descendente configurado por defecto."""
        # Arrange
        filas = pd.DataFrame(construir_filas_grid([_resumen()]))

        # Act
        opciones = construir_grid_options(filas)

        # Assert
        columnas = {c["field"]: c for c in opciones["columnDefs"]}
        assert columnas["recibido"]["sort"] == "desc"


class TestConstruirMapa:
    """Pruebas del armado del mapa de la Bandeja."""

    def test_agrega_un_marcador_por_resultado_con_comuna_conocida(self) -> None:
        """Un resultado con comuna sin centroide local no agrega marcador."""
        # Arrange
        resultados = [
            _resumen(id="rpt_a", comuna="Comuna 20"),
            _resumen(id="rpt_b", comuna="Comuna inexistente"),
        ]

        # Act
        mapa = construir_mapa(resultados)

        # Assert
        marcadores = [
            hijo for hijo in mapa._children.values() if isinstance(hijo, folium.CircleMarker)
        ]
        assert len(marcadores) == 1


class TestFilaSeleccionadaDe:
    """Pruebas de la extracción de la fila seleccionada en la respuesta de AgGrid."""

    def test_devuelve_none_si_no_hay_seleccion(self) -> None:
        """Una respuesta sin selected_rows, o con lista vacía, no da ninguna fila."""
        # Arrange / Act / Assert
        assert fila_seleccionada_de({"selected_rows": []}) is None
        assert fila_seleccionada_de({"selected_rows": None}) is None

    def test_extrae_la_primera_fila_de_una_lista(self) -> None:
        """Con selected_rows como lista de dicts, se toma el primero."""
        # Arrange
        grid_response = {"selected_rows": [{"id": "rpt_1"}, {"id": "rpt_2"}]}

        # Act
        fila = fila_seleccionada_de(grid_response)

        # Assert
        assert fila == {"id": "rpt_1"}

    def test_extrae_la_primera_fila_de_un_dataframe(self) -> None:
        """Con selected_rows como DataFrame (versiones nuevas de aggrid), también funciona."""
        # Arrange
        grid_response = {"selected_rows": pd.DataFrame([{"id": "rpt_1"}])}

        # Act
        fila = fila_seleccionada_de(grid_response)

        # Assert
        assert fila is not None
        assert fila["id"] == "rpt_1"

"""Pruebas de las funciones puras de la Bandeja (frontend.bandeja)."""

from datetime import datetime, timezone

import folium
import pandas as pd

from frontend.bandeja import (
    calcular_total_paginas,
    construir_filas_exportacion,
    construir_filas_grid,
    construir_grid_options,
    construir_mapa,
    exportar_csv,
    fila_seleccionada_de,
    listar_todo,
)
from frontend.bff_client import FiltrosReportes, PaginaReportes, ReporteResumen
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

    def test_agrega_marcador_con_coordenada_exacta_aunque_la_comuna_no_se_conozca(self) -> None:
        """Con lat/lon, el marcador se planta aunque la comuna no tenga centroide local."""
        # Arrange
        resultados = [_resumen(id="rpt_a", comuna="Comuna inexistente", lat=3.45, lon=-76.53)]

        # Act
        mapa = construir_mapa(resultados)

        # Assert
        marcadores = [
            hijo for hijo in mapa._children.values() if isinstance(hijo, folium.CircleMarker)
        ]
        assert len(marcadores) == 1
        assert marcadores[0].location == [3.45, -76.53]


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


class TestCalcularTotalPaginas:
    """Pruebas de calcular_total_paginas."""

    def test_redondea_hacia_arriba(self) -> None:
        """45 resultados con tamano_pagina=20 son 3 páginas, no 2."""
        # Arrange / Act / Assert
        assert calcular_total_paginas(45, 20) == 3

    def test_resultado_exacto_no_agrega_una_pagina_de_mas(self) -> None:
        """40 resultados con tamano_pagina=20 son exactamente 2 páginas."""
        # Arrange / Act / Assert
        assert calcular_total_paginas(40, 20) == 2

    def test_sin_resultados_devuelve_una_pagina_no_cero(self) -> None:
        """ "Página 1 de 0" no tiene sentido en la UI; con total=0 igual es 1."""
        # Arrange / Act / Assert
        assert calcular_total_paginas(0, 20) == 1


class _ClienteFalso:
    """Cliente de prueba con resultados repartidos en varias páginas fijas."""

    def __init__(self, paginas: list[list[ReporteResumen]], total: int) -> None:
        """Guarda las páginas ya armadas y el total a devolver en cada una.

        Args:
            paginas: Una lista de páginas, cada una una lista de resultados.
            total: Total a reportar en cada `PaginaReportes` (simula el
                conteo real del filtro, no `len(paginas)`).

        """
        self._paginas = paginas
        self._total = total
        self.pedidos: list[int] = []

    def listar(self, filtros: FiltrosReportes) -> PaginaReportes:
        """Devuelve la página pedida en `filtros.pagina` (1-indexada)."""
        self.pedidos.append(filtros.pagina)
        indice = filtros.pagina - 1
        resultados = self._paginas[indice] if indice < len(self._paginas) else []
        return PaginaReportes(
            total=self._total,
            pagina=filtros.pagina,
            tamano_pagina=filtros.tamano_pagina,
            resultados=resultados,
        )


class TestListarTodo:
    """Pruebas de listar_todo, usado para el CSV completo de la Bandeja."""

    def test_junta_los_resultados_de_todas_las_paginas(self) -> None:
        """Con 3 páginas de 2, listar_todo trae los 5 resultados reales."""
        # Arrange
        pagina_1 = [_resumen(id="rpt_1"), _resumen(id="rpt_2")]
        pagina_2 = [_resumen(id="rpt_3"), _resumen(id="rpt_4")]
        pagina_3 = [_resumen(id="rpt_5")]
        cliente = _ClienteFalso([pagina_1, pagina_2, pagina_3], total=5)

        # Act
        resultados = listar_todo(cliente, FiltrosReportes(), tamano_pagina=2)

        # Assert
        assert [r.id for r in resultados] == ["rpt_1", "rpt_2", "rpt_3", "rpt_4", "rpt_5"]
        assert cliente.pedidos == [1, 2, 3]

    def test_no_pide_paginas_de_mas_una_vez_completado_el_total(self) -> None:
        """Al alcanzar pagina.total no sigue pidiendo, aunque el tope sea mayor."""
        # Arrange
        cliente = _ClienteFalso([[_resumen(id="rpt_1")]], total=1)

        # Act
        listar_todo(cliente, FiltrosReportes(), tamano_pagina=50)

        # Assert
        assert cliente.pedidos == [1]

    def test_sin_resultados_no_reventa(self) -> None:
        """Un filtro sin resultados no dispara ninguna página de más."""
        # Arrange
        cliente = _ClienteFalso([], total=0)

        # Act
        resultados = listar_todo(cliente, FiltrosReportes())

        # Assert
        assert resultados == []
        assert cliente.pedidos == [1]

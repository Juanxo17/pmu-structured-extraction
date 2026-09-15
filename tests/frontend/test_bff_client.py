"""Pruebas del cliente HTTP hacia BFF, contra un transporte simulado."""

import httpx
import pytest

from frontend.bff_client import BFFClient, ErrorBFF, FiltrosReportes

_REPORTE_JSON = {
    "id": "rpt_1",
    "fuente": "telegram",
    "id_externo": "tg_1",
    "autor_anonimizado_id": "anon_1",
    "mensaje_anonimizado": "el agua subió rápido",
    "estado_revision": "pendiente",
    "compuerta": {
        "es_reporte_accionable": True,
        "temporalidad": "ocurriendo_ahora",
        "intencion": "solicita_ayuda",
    },
    "naturaleza": {"tipo_evento": "inundacion_subita", "servicio_de_respuesta": ["A", "G"]},
    "ubicacion": {
        "ubicacion_texto_literal": "cerca al puente",
        "barrio": "El Vergel",
        "comuna": "Comuna 13",
        "punto_referencia": "puente peatonal",
        "nivel_granularidad": "barrio",
        "lat": None,
        "lon": None,
    },
    "creado_en": "2026-09-15T08:00:00Z",
}


def _cliente_con_transporte(handler) -> BFFClient:
    """Construye un BFFClient cuyo httpx.Client usa un transporte simulado.

    Args:
        handler: Función que recibe un httpx.Request y devuelve un httpx.Response.

    Returns:
        Un BFFClient listo para usarse en pruebas, sin red real.

    """
    transporte = httpx.MockTransport(handler)
    cliente_http = httpx.Client(base_url="http://bff.test", transport=transporte)
    return BFFClient(base_url="http://bff.test", cliente_http=cliente_http)


class TestFiltrosReportes:
    """Pruebas de la construcción de query params a partir de FiltrosReportes."""

    def test_omite_filtros_vacios(self) -> None:
        """Solo pagina y tamano_pagina viajan cuando no hay filtros activos."""
        # Arrange
        filtros = FiltrosReportes()

        # Act
        params = filtros.como_query_params()

        # Assert
        assert params == {"pagina": 1, "tamano_pagina": 20}

    def test_incluye_listas_de_tipo_evento_y_servicios(self) -> None:
        """tipo_evento y servicio_de_respuesta viajan como listas cuando se definen."""
        # Arrange
        filtros = FiltrosReportes(tipo_evento=["sismo"], servicio_de_respuesta=["A", "G"])

        # Act
        params = filtros.como_query_params()

        # Assert
        assert params["tipo_evento"] == ["sismo"]
        assert params["servicio_de_respuesta"] == ["A", "G"]

    def test_incluye_solo_los_campos_simples_definidos(self) -> None:
        """Un filtro simple sin definir no aparece en los query params."""
        # Arrange
        filtros = FiltrosReportes(comuna="Comuna 13")

        # Act
        params = filtros.como_query_params()

        # Assert
        assert params["comuna"] == "Comuna 13"
        assert "barrio" not in params


class TestBFFClientListar:
    """Pruebas de BFFClient.listar contra un transporte HTTP simulado."""

    def test_arma_la_peticion_y_parsea_la_pagina(self) -> None:
        """listar hace GET /reportes con los filtros y devuelve una PaginaReportes."""
        # Arrange
        capturado: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            capturado["url"] = str(request.url)
            return httpx.Response(
                200,
                json={
                    "total": 1,
                    "pagina": 1,
                    "tamano_pagina": 20,
                    "resultados": [
                        {
                            "id": "rpt_1",
                            "tipo_evento": "sismo",
                            "servicio_de_respuesta": ["A"],
                            "comuna": "Comuna 20",
                            "barrio": "Siloé",
                            "temporalidad": "ya_ocurrio",
                            "intencion": "reporta_terceros",
                            "estado_revision": "pendiente",
                            "nivel_granularidad": "barrio",
                            "creado_en": "2026-09-15T08:00:00Z",
                        }
                    ],
                },
            )

        cliente = _cliente_con_transporte(handler)

        # Act
        pagina = cliente.listar(FiltrosReportes(tipo_evento=["sismo"]))

        # Assert
        assert "/reportes" in capturado["url"]
        assert "tipo_evento=sismo" in capturado["url"]
        assert pagina.total == 1
        assert pagina.resultados[0].id == "rpt_1"
        assert pagina.resultados[0].servicio_de_respuesta == ["A"]

    def test_lanza_error_bff_si_la_respuesta_es_4xx(self) -> None:
        """Un 422 de BFF se traduce en ErrorBFF con el detalle del cuerpo."""

        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, text="filtro invalido")

        cliente = _cliente_con_transporte(handler)

        # Act / Assert
        with pytest.raises(ErrorBFF) as excinfo:
            cliente.listar(FiltrosReportes())
        assert excinfo.value.status_code == 422


class TestBFFClientObtenerYActualizar:
    """Pruebas de BFFClient.obtener y BFFClient.actualizar."""

    def test_obtener_parsea_reporte_completo(self) -> None:
        """obtener hace GET /reportes/{id} y devuelve un ReporteEstructurado."""

        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/reportes/rpt_1"
            return httpx.Response(200, json=_REPORTE_JSON)

        cliente = _cliente_con_transporte(handler)

        # Act
        reporte = cliente.obtener("rpt_1")

        # Assert
        assert reporte.id == "rpt_1"
        assert reporte.naturaleza is not None
        assert reporte.naturaleza.tipo_evento == "inundacion_subita"

    def test_obtener_lanza_error_bff_si_no_existe(self) -> None:
        """Un 404 de BFF se traduce en ErrorBFF."""

        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="no encontrado")

        cliente = _cliente_con_transporte(handler)

        # Act / Assert
        with pytest.raises(ErrorBFF) as excinfo:
            cliente.obtener("rpt_inexistente")
        assert excinfo.value.status_code == 404

    def test_actualizar_envia_patch_con_estado_y_correccion(self) -> None:
        """actualizar hace PATCH /reportes/{id} con el cuerpo esperado."""
        # Arrange
        capturado: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            capturado["metodo"] = request.method
            capturado["cuerpo"] = request.content
            return httpx.Response(200, json=_REPORTE_JSON)

        cliente = _cliente_con_transporte(handler)

        # Act
        reporte = cliente.actualizar(
            "rpt_1", estado_revision="revisado", correccion={"tipo_evento": "sismo"}
        )

        # Assert
        assert capturado["metodo"] == "PATCH"
        assert reporte.id == "rpt_1"


class TestBFFClientResumen:
    """Pruebas de BFFClient.resumen."""

    def test_resumen_parsea_agregados(self) -> None:
        """resumen hace GET /reportes/resumen y devuelve un ResumenReportes."""

        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "total": 10,
                    "pendientes": 4,
                    "revisados": 6,
                    "por_tipo_evento": {"sismo": 2},
                    "por_comuna": {"Comuna 13": 3},
                },
            )

        cliente = _cliente_con_transporte(handler)

        # Act
        resumen = cliente.resumen(desde="2026-09-01", hasta="2026-09-15")

        # Assert
        assert resumen.total == 10
        assert resumen.pendientes == 4
        assert resumen.por_tipo_evento["sismo"] == 2

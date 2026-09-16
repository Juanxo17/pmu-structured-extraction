"""Pruebas de los endpoints del servicio BFF."""

import pytest
from fastapi.testclient import TestClient

from bff import main
from bff.main import app

MENSAJE_VALIDO = {
    "fuente": "telegram",
    "id_externo": "msg_1",
    "texto": "Hay un incendio en Siloe",
    "marca_temporal_origen": "2026-09-16T10:00:00",
    "autor_id_telegram": "user_1",
}


class TestHealthCheck:
    """Pruebas de GET /health."""

    def test_retorna_estado_ok(self) -> None:
        """GET /health responde 200 con status ok."""
        # Arrange
        client = TestClient(app)

        # Act
        respuesta = client.get("/health")

        # Assert
        assert respuesta.status_code == 200
        assert respuesta.json() == {"status": "ok"}


class TestRecibirMensaje:
    """Pruebas de POST /mensajes."""

    def test_mensaje_nuevo_dispara_procesamiento_y_responde_202(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un mensaje sin duplicado dispara Process en segundo plano y responde 202."""

        # Arrange
        async def _sin_duplicado(fuente: str, id_externo: str) -> bool:  # noqa: ARG001
            return False

        async def _proceso_arriba() -> bool:
            return True

        llamadas_a_process: list[main.MensajeEntrante] = []

        async def _capturar_disparo(mensaje: main.MensajeEntrante) -> None:
            llamadas_a_process.append(mensaje)

        monkeypatch.setattr(main, "_existe_duplicado", _sin_duplicado)
        monkeypatch.setattr(main, "_proceso_disponible", _proceso_arriba)
        monkeypatch.setattr(main, "_disparar_procesamiento", _capturar_disparo)
        client = TestClient(app)

        # Act
        respuesta = client.post("/mensajes", json=MENSAJE_VALIDO)

        # Assert
        assert respuesta.status_code == 202
        assert respuesta.json() == {"id_mensaje": "msg_1", "estado": "recibido"}
        assert len(llamadas_a_process) == 1
        assert llamadas_a_process[0].id_externo == "msg_1"
        assert llamadas_a_process[0].autor_id_telegram == "user_1"

    def test_mensaje_duplicado_responde_409_y_no_dispara_process(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un id_externo ya recibido responde 409 y nunca llama a Process."""

        # Arrange
        async def _con_duplicado(fuente: str, id_externo: str) -> bool:  # noqa: ARG001
            return True

        async def _no_deberia_llamarse(mensaje: main.MensajeEntrante) -> None:  # noqa: ARG001
            raise AssertionError("no deberia dispararse Process para un mensaje duplicado")

        monkeypatch.setattr(main, "_existe_duplicado", _con_duplicado)
        monkeypatch.setattr(main, "_disparar_procesamiento", _no_deberia_llamarse)
        client = TestClient(app)

        # Act
        respuesta = client.post("/mensajes", json=MENSAJE_VALIDO)

        # Assert
        assert respuesta.status_code == 409

    def test_falta_campo_obligatorio_responde_400(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Si falta un campo obligatorio, responde 400 (no el 422 automatico de FastAPI)."""

        # Arrange
        async def _no_deberia_llamarse(*args: object, **kwargs: object) -> bool:
            raise AssertionError("no deberia consultarse duplicados sin un cuerpo valido")

        monkeypatch.setattr(main, "_existe_duplicado", _no_deberia_llamarse)
        cuerpo_incompleto = {k: v for k, v in MENSAJE_VALIDO.items() if k != "texto"}
        client = TestClient(app)

        # Act
        respuesta = client.post("/mensajes", json=cuerpo_incompleto)

        # Assert
        assert respuesta.status_code == 400

    def test_cuerpo_no_es_json_responde_400(self) -> None:
        """Si el cuerpo no es JSON valido, responde 400."""
        # Arrange
        client = TestClient(app)

        # Act
        respuesta = client.post(
            "/mensajes", content=b"esto no es json", headers={"Content-Type": "application/json"}
        )

        # Assert
        assert respuesta.status_code == 400

    def test_process_no_disponible_responde_503_y_no_dispara_process(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Si Process no esta alcanzable, responde 503 y nunca agenda el disparo."""

        # Arrange
        async def _sin_duplicado(fuente: str, id_externo: str) -> bool:  # noqa: ARG001
            return False

        async def _proceso_caido() -> bool:
            return False

        async def _no_deberia_llamarse(mensaje: main.MensajeEntrante) -> None:  # noqa: ARG001
            raise AssertionError("no deberia dispararse Process si no esta disponible")

        monkeypatch.setattr(main, "_existe_duplicado", _sin_duplicado)
        monkeypatch.setattr(main, "_proceso_disponible", _proceso_caido)
        monkeypatch.setattr(main, "_disparar_procesamiento", _no_deberia_llamarse)
        client = TestClient(app)

        # Act
        respuesta = client.post("/mensajes", json=MENSAJE_VALIDO)

        # Assert
        assert respuesta.status_code == 503


class TestListarReportes:
    """Pruebas de GET /reportes (proxy puro hacia CRUD)."""

    def test_reenvia_filtros_y_respuesta_de_crud_tal_cual(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Los query params se reenvian tal cual a CRUD, y su respuesta tambien."""

        # Arrange
        llamadas: list[tuple[str, list]] = []

        async def _crud_simulado(ruta: str, parametros: list) -> tuple[int, dict]:
            llamadas.append((ruta, parametros))
            return 200, {"total": 0, "pagina": 1, "tamano_pagina": 20, "resultados": []}

        monkeypatch.setattr(main, "_reenviar_get", _crud_simulado)
        client = TestClient(app)

        # Act
        respuesta = client.get("/reportes", params={"comuna": "20", "pagina": "2"})

        # Assert
        assert respuesta.status_code == 200
        assert respuesta.json() == {"total": 0, "pagina": 1, "tamano_pagina": 20, "resultados": []}
        assert llamadas == [("/reportes", [("comuna", "20"), ("pagina", "2")])]

    def test_filtro_repetible_no_pierde_valores(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """servicio_de_respuesta es repetible (OR) -- ningun valor se debe perder al reenviar.

        Un dict de Python no puede tener la misma llave dos veces; si BFF
        convirtiera los query params a dict antes de reenviarlos, este
        filtro perderia todos los valores repetidos menos el ultimo.
        """

        # Arrange
        llamadas: list[tuple[str, list]] = []

        async def _crud_simulado(ruta: str, parametros: list) -> tuple[int, dict]:
            llamadas.append((ruta, parametros))
            return 200, {"total": 0, "pagina": 1, "tamano_pagina": 20, "resultados": []}

        monkeypatch.setattr(main, "_reenviar_get", _crud_simulado)
        client = TestClient(app)

        # Act
        respuesta = client.get(
            "/reportes?servicio_de_respuesta=bomberos&servicio_de_respuesta=policia"
        )

        # Assert
        assert respuesta.status_code == 200
        assert llamadas == [
            (
                "/reportes",
                [("servicio_de_respuesta", "bomberos"), ("servicio_de_respuesta", "policia")],
            )
        ]


class TestResumenReportes:
    """Pruebas de GET /reportes/resumen (proxy puro hacia CRUD)."""

    def test_no_se_confunde_con_reportes_por_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """GET /reportes/resumen debe llegar al handler de resumen, no al de detalle por id.

        Si el orden de las rutas estuviera mal declarado, FastAPI interpretaria
        "resumen" como un id_reporte y llamaria a `obtener_reporte` en su lugar
        -- este test lo distingue verificando que los query params (desde/hasta)
        SI llegaron a CRUD, algo que `obtener_reporte` nunca reenvia.
        """

        # Arrange
        llamadas: list[tuple[str, list]] = []

        async def _crud_simulado(ruta: str, parametros: list) -> tuple[int, dict]:
            llamadas.append((ruta, parametros))
            return 200, {
                "total": 0,
                "pendientes": 0,
                "revisados": 0,
                "por_tipo_evento": {},
                "por_comuna": {},
            }

        monkeypatch.setattr(main, "_reenviar_get", _crud_simulado)
        client = TestClient(app)

        # Act
        respuesta = client.get("/reportes/resumen", params={"desde": "2026-01-01"})

        # Assert
        assert respuesta.status_code == 200
        assert llamadas == [("/reportes/resumen", [("desde", "2026-01-01")])]


class TestObtenerReporte:
    """Pruebas de GET /reportes/{id} (proxy puro hacia CRUD)."""

    def test_reporte_existente_responde_200(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Un id existente reenvia la respuesta 200 de CRUD tal cual."""

        # Arrange
        async def _crud_simulado(ruta: str, parametros: dict) -> tuple[int, dict]:  # noqa: ARG001
            assert ruta == "/reportes/rep_1"
            return 200, {"id": "rep_1"}

        monkeypatch.setattr(main, "_reenviar_get", _crud_simulado)
        client = TestClient(app)

        # Act
        respuesta = client.get("/reportes/rep_1")

        # Assert
        assert respuesta.status_code == 200
        assert respuesta.json() == {"id": "rep_1"}

    def test_reporte_inexistente_responde_404(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Un id inexistente reenvia el 404 de CRUD tal cual."""

        # Arrange
        async def _crud_simulado(ruta: str, parametros: dict) -> tuple[int, dict]:  # noqa: ARG001
            return 404, {"detail": "no encontrado"}

        monkeypatch.setattr(main, "_reenviar_get", _crud_simulado)
        client = TestClient(app)

        # Act
        respuesta = client.get("/reportes/no_existe")

        # Assert
        assert respuesta.status_code == 404


class TestCorregirReporte:
    """Pruebas de PATCH /reportes/{id} (proxy puro hacia CRUD)."""

    def test_correccion_valida_reenvia_cuerpo_y_respuesta_de_crud(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """El cuerpo del PATCH se reenvia tal cual a CRUD, y su respuesta tambien."""

        # Arrange
        llamadas: list[tuple[str, dict]] = []

        async def _crud_simulado(ruta: str, cuerpo: dict) -> tuple[int, dict]:
            llamadas.append((ruta, cuerpo))
            return 200, {"id": "rep_1", "estado_revision": "revisado"}

        monkeypatch.setattr(main, "_reenviar_patch", _crud_simulado)
        client = TestClient(app)

        # Act
        respuesta = client.patch("/reportes/rep_1", json={"estado_revision": "revisado"})

        # Assert
        assert respuesta.status_code == 200
        assert respuesta.json() == {"id": "rep_1", "estado_revision": "revisado"}
        assert llamadas == [("/reportes/rep_1", {"estado_revision": "revisado"})]

    def test_correccion_invalida_reenvia_422_de_crud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Un cuerpo que CRUD rechaza reenvia su 422 tal cual (BFF no valida esto)."""

        # Arrange
        async def _crud_simulado(ruta: str, cuerpo: dict) -> tuple[int, dict]:  # noqa: ARG001
            return 422, {"detail": "estado_revision invalido"}

        monkeypatch.setattr(main, "_reenviar_patch", _crud_simulado)
        client = TestClient(app)

        # Act
        respuesta = client.patch("/reportes/rep_1", json={"estado_revision": "no_existe"})

        # Assert
        assert respuesta.status_code == 422

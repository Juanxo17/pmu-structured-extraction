"""Pruebas de los endpoints del servicio Process."""

import pytest
from fastapi.testclient import TestClient

from process import main
from process.main import app


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


class TestProcesarEndpoint:
    """Pruebas de POST /procesar -- delega en orquestador.procesar_mensaje."""

    def test_delega_en_el_orquestador_y_retorna_su_resultado(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """El endpoint pasa los datos de la peticion al orquestador tal cual."""

        # Arrange
        async def _orquestador_simulado(**kwargs) -> dict:
            assert kwargs == {
                "mensaje_id": "msg_1",
                "texto_crudo": "hay un incendio",
                "fuente": "telegram",
                "id_externo": "msg_1",
                "autor_id_telegram": "user_1",
            }
            return {"estado": "descartado", "motivo": "no_accionable"}

        monkeypatch.setattr(main, "procesar_mensaje", _orquestador_simulado)
        client = TestClient(app)

        # Act
        respuesta = client.post(
            "/procesar",
            json={
                "mensaje_id": "msg_1",
                "texto_crudo": "hay un incendio",
                "fuente": "telegram",
                "id_externo": "msg_1",
                "autor_id_telegram": "user_1",
            },
        )

        # Assert
        assert respuesta.status_code == 200
        assert respuesta.json() == {"estado": "descartado", "motivo": "no_accionable"}

    def test_peticion_incompleta_retorna_422(self) -> None:
        """Si falta un campo obligatorio, FastAPI/Pydantic responde 422 automaticamente."""
        # Arrange
        client = TestClient(app)

        # Act
        respuesta = client.post("/procesar", json={"mensaje_id": "msg_1"})

        # Assert
        assert respuesta.status_code == 422

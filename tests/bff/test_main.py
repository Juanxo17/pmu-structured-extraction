"""Pruebas del endpoint de salud del servicio BFF."""

from fastapi.testclient import TestClient

from bff.main import app


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

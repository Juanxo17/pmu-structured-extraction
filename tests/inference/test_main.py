"""Pruebas de los endpoints del servicio Inference."""

from fastapi.testclient import TestClient

from inference.main import app, obtener_proveedor
from tests.inference.test_servicio import (
    COMPUERTA_MALA,
    COMPUERTA_OK,
    EXTRACCION_OK,
    ProveedorFalso,
)


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


class TestCompuertaEndpoint:
    """Pruebas de POST /compuerta."""

    def test_clasifica_reporte_valido(self) -> None:
        """Responde 200 con la Compuerta valida del proveedor."""
        # Arrange
        proveedor = ProveedorFalso(COMPUERTA_OK)
        app.dependency_overrides[obtener_proveedor] = lambda: proveedor
        try:
            client = TestClient(app)

            # Act
            respuesta = client.post("/compuerta", json={"texto": "hay un incendio"})

            # Assert
            assert respuesta.status_code == 200
            assert respuesta.json()["es_reporte_accionable"] is True
        finally:
            app.dependency_overrides.clear()

    def test_rechaza_texto_vacio(self) -> None:
        """Responde 422 cuando el texto esta vacio."""
        # Arrange
        proveedor = ProveedorFalso(COMPUERTA_OK)
        app.dependency_overrides[obtener_proveedor] = lambda: proveedor
        try:
            client = TestClient(app)

            # Act
            respuesta = client.post("/compuerta", json={"texto": ""})

            # Assert
            assert respuesta.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_responde_422_cuando_no_conforma(self) -> None:
        """Responde 422 con detalle cuando la salida no conforme."""
        # Arrange
        proveedor = ProveedorFalso(COMPUERTA_MALA)
        app.dependency_overrides[obtener_proveedor] = lambda: proveedor
        try:
            client = TestClient(app)

            # Act
            respuesta = client.post("/compuerta", json={"texto": "hay un incendio"})

            # Assert
            assert respuesta.status_code == 422
            assert "detalle" in respuesta.json()
        finally:
            app.dependency_overrides.clear()


class TestExtraccionEndpoint:
    """Pruebas de POST /extraccion."""

    def test_extrae_naturaleza_y_ubicacion(self) -> None:
        """Responde 200 con naturaleza y ubicacion validas."""
        # Arrange
        proveedor = ProveedorFalso(EXTRACCION_OK)
        app.dependency_overrides[obtener_proveedor] = lambda: proveedor
        try:
            client = TestClient(app)

            # Act
            respuesta = client.post("/extraccion", json={"texto": "tiembla en cali"})

            # Assert
            assert respuesta.status_code == 200
            cuerpo = respuesta.json()
            assert cuerpo["naturaleza"]["tipo_evento"] == "sismo"
            assert "ubicacion" in cuerpo
            assert "ubicacion_texto_literal" in cuerpo["ubicacion"]
            assert "barrio" not in cuerpo["ubicacion"]
        finally:
            app.dependency_overrides.clear()

    def test_responde_422_cuando_no_conforma(self) -> None:
        """Responde 422 con detalle cuando la salida no conforme."""
        # Arrange
        proveedor = ProveedorFalso(COMPUERTA_MALA)
        app.dependency_overrides[obtener_proveedor] = lambda: proveedor
        try:
            client = TestClient(app)

            # Act
            respuesta = client.post("/extraccion", json={"texto": "tiembla en cali"})

            # Assert
            assert respuesta.status_code == 422
            assert "detalle" in respuesta.json()
        finally:
            app.dependency_overrides.clear()

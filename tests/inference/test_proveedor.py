"""Pruebas del proveedor del LLM (configuracion sin red)."""

import pytest

from inference import proveedor


class TestProveedorGroq:
    """Pruebas de configuracion de ProveedorGroq."""

    def test_lanza_error_sin_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Lanza ValueError cuando falta la clave de la API."""
        # Arrange
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        # Act / Assert
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            proveedor.ProveedorGroq()

    def test_usa_clave_y_modelo_entregados(self) -> None:
        """Usa la clave y el modelo explicitos sin leer el entorno."""
        # Arrange
        cliente = proveedor.ProveedorGroq(
            api_key="clave-de-prueba", modelo="modelo-de-prueba"
        )

        # Act
        configurado = (
            cliente._modelo == "modelo-de-prueba"
        )

        # Assert
        assert configurado

    def test_temperatura_por_defecto_es_cero(self) -> None:
        """La temperatura por defecto favorece determinismo."""
        # Arrange
        cliente = proveedor.ProveedorGroq(api_key="clave-de-prueba")

        # Act
        temperatura = cliente.temperatura

        # Assert
        assert temperatura == 0.0
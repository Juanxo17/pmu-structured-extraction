"""Pruebas de la selección de cliente (frontend.cliente)."""

import pytest

from frontend.bff_client import BFFClient
from frontend.cliente import elegir_cliente, usa_datos_de_ejemplo
from frontend.reportes_mock import ClienteReportesSimulado


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

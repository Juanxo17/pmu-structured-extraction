"""Pruebas del adaptador externo Nominatim (sin contacto con la red)."""

from __future__ import annotations

import pytest

from geo.nominatim import NominatimResolver


def _capturar_cliente(url: str | None, monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """Construye el resolver y captura los kwargs de `Nominatim`.

    Reemplaza `geo.nominatim.Nominatim` por un doble que registra los parametros
    del constructor y nunca falla, de modo que se puede verificar hacia donde
    apunta `NOMINATIM_URL` sin tocar la red.

    Args:
        url: URL a pasar al resolver (None usa el entorno por defecto).
        monkeypatch: Fixture de pytest para suplantar la clase.

    Returns:
        Lista con los kwargs recibidos por cada instancia creada.

    """
    capturado: list[dict[str, object]] = []

    class ClienteFalso:
        """Reemplazo de `geopy.geocoders.Nominatim` sin red."""

        def __init__(self, **kwargs: object) -> None:
            capturado.append(kwargs)

        def geocode(self, **kwargs: object) -> None:
            return None

    monkeypatch.setattr("geo.nominatim.Nominatim", ClienteFalso)
    resolver = NominatimResolver(url=url)
    resolver._geocodificar_sin_limite("lugar de prueba")
    return capturado


class TestNOMINATIMURL:
    """`NOMINATIM_URL` define a que servidor se consulta realmente."""

    def test_usa_el_esquema_y_dominio_de_la_url_explicita(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Una url explicita controla esquema y dominio del cliente."""
        capturado = _capturar_cliente("http://nominatim.local:8080", monkeypatch)

        assert capturado[0]["scheme"] == "http"
        assert capturado[0]["domain"] == "nominatim.local:8080"

    def test_usa_la_url_del_entorno(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sin url explicita, se respeta `NOMINATIM_URL` del entorno."""
        monkeypatch.setenv("NOMINATIM_URL", "http://nominatim.local:8080")
        capturado = _capturar_cliente(None, monkeypatch)

        assert capturado[0]["scheme"] == "http"
        assert capturado[0]["domain"] == "nominatim.local:8080"

    def test_sin_url_usa_el_servidor_publico(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sin configuracion, el destino es el servidor publico de la URL base."""
        capturado = _capturar_cliente(None, monkeypatch)

        assert capturado[0]["scheme"] == "https"
        assert capturado[0]["domain"] == "nominatim.openstreetmap.org"

    def test_url_sin_esquema_usa_https(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Un dominio sin esquema se interpreta como https."""
        capturado = _capturar_cliente("nominatim.local", monkeypatch)

        assert capturado[0]["scheme"] == "https"
        assert capturado[0]["domain"] == "nominatim.local"


class TestReutilizacionDelCliente:
    """El cliente se crea una sola vez y se reutiliza entre llamadas."""

    def test_una_instancia_para_varias_consultas(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cada consulta reutiliza el mismo `Nominatim`, no crea uno nuevo."""
        capturado: list[dict[str, object]] = []

        class ClienteFalso:
            """Reemplazo de `Nominatim` que registra sus instancias."""

            def __init__(self, **kwargs: object) -> None:
                capturado.append(kwargs)

            def geocode(self, **kwargs: object) -> None:
                return None

        monkeypatch.setattr("geo.nominatim.Nominatim", ClienteFalso)
        resolver = NominatimResolver(url="nominatim.local")
        resolver._geocodificar_sin_limite("lugar uno")
        resolver._geocodificar_sin_limite("lugar dos")

        assert len(capturado) == 1

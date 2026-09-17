"""Pruebas del endpoint POST /resolver del servicio Geo."""

import pytest
from fastapi.testclient import TestClient

from geo.gazetteer import Gazetteer
from geo.geocodificador import Geocodificador
from geo.main import app, fijar_geocodificador


class ExternoInerte:
    """Resolutor externo que nunca encuentra nada (evita la red)."""

    def geocodificar(self, texto: str) -> None:
        return None


@pytest.fixture(autouse=True)
def geocodificador_fijo() -> None:
    """Sustituye el geocodificador del servicio por uno sin red."""
    fijar_geocodificador(Geocodificador(Gazetteer(), ExternoInerte()))
    yield
    fijar_geocodificador()


class TestResolverEndpoint:
    """Pruebas del comportamiento del endpoint POST /resolver."""

    def test_resuelve_barrio_devuelve_esquema_completo(self) -> None:
        """La respuesta incluye barrio, comuna, nivel y coordenadas."""
        client = TestClient(app)

        respuesta = client.post("/resolver", json={"ubicacion_texto_literal": "El Vergel"})

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["barrio"] == "El Vergel"
        assert cuerpo["comuna"] == "Comuna 13"
        assert cuerpo["nivel_granularidad"] == "barrio"
        assert cuerpo["lat"] is not None
        assert cuerpo["lon"] is not None

    def test_resuelve_con_punto_de_referencia(self) -> None:
        """El punto de referencia complementa la ubicacion."""
        client = TestClient(app)

        respuesta = client.post(
            "/resolver",
            json={
                "ubicacion_texto_literal": "humo",
                "punto_referencia": "El Vergel",
            },
        )

        assert respuesta.status_code == 200
        assert respuesta.json()["barrio"] == "El Vergel"

    def test_ubicacion_desconocida_es_indeterminada(self) -> None:
        """Sin coincidencias locales ni externas responde indeterminada."""
        client = TestClient(app)

        respuesta = client.post(
            "/resolver",
            json={"ubicacion_texto_literal": "entre la esquina y el árbol"},
        )

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["nivel_granularidad"] == "indeterminada"
        assert cuerpo["barrio"] is None
        assert cuerpo["comuna"] is None
        assert cuerpo["lat"] is None
        assert cuerpo["lon"] is None

    def test_sin_ubicacion_es_indeterminada(self) -> None:
        """Una ubicacion vacia se degrada sin error."""
        client = TestClient(app)

        respuesta = client.post("/resolver", json={"ubicacion_texto_literal": ""})

        assert respuesta.status_code == 200
        assert respuesta.json()["nivel_granularidad"] == "indeterminada"

    def test_punto_de_referencia_opcional(self) -> None:
        """El campo punto_referencia no es obligatorio."""
        client = TestClient(app)

        respuesta = client.post("/resolver", json={"ubicacion_texto_literal": "comuna 3"})

        assert respuesta.status_code == 200
        assert respuesta.json()["comuna"] == "Comuna 3"

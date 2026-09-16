"""Pruebas de los endpoints del servicio CRUD."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.crud.datos import ReportesFabrica


def _post(client: TestClient, datos: ReportesFabrica, **kwargs) -> dict:
    """Crea un reporte via POST y devuelve la respuesta JSON.

    Args:
        client: Cliente HTTP de la app.
        datos: Fabrica de reportes.
        **kwargs: Argumentos a pasar a `datos.reporte`.

    Returns:
        La respuesta JSON del endpoint.

    """
    payload = datos.reporte(**kwargs)
    respuesta = client.post("/reportes", json=payload)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


class TestCrearReporte:
    """POST /reportes."""

    def test_crea_reporte_completo(self, cliente: TestClient, datos: ReportesFabrica):
        """Devuelve 201 con el reporte completo persistido."""
        client = cliente
        payload = datos.reporte(comuna="2", barrio="San Fernando")
        respuesta = client.post("/reportes", json=payload)
        assert respuesta.status_code == 201
        cuerpo = respuesta.json()
        assert cuerpo["id"] == payload["id"]
        assert cuerpo["id_externo"] == payload["id_externo"]
        assert cuerpo["naturaleza"]["tipo_evento"] == payload["naturaleza"]["tipo_evento"]
        assert cuerpo["ubicacion"]["comuna"] == "2"

    def test_rechaza_duplicado_por_id(self, cliente: TestClient, datos: ReportesFabrica):
        """Devuelve 409 si el id ya existe."""
        client = cliente
        payload = datos.reporte()
        client.post("/reportes", json=payload)
        duplicado = {**payload, "id_externo": "otro-id"}
        respuesta = client.post("/reportes", json=duplicado)
        assert respuesta.status_code == 409

    def test_rechaza_duplicado_por_id_externo(self, cliente: TestClient, datos: ReportesFabrica):
        """Devuelve 409 si el id_externo ya existe."""
        client = cliente
        payload = datos.reporte()
        client.post("/reportes", json=payload)
        duplicado = {**payload, "id": "rpt-nuevo"}
        respuesta = client.post("/reportes", json=duplicado)
        assert respuesta.status_code == 409


class TestListarReportes:
    """GET /reportes."""

    def test_lista_vacia(self, cliente: TestClient):
        """Devuelve total 0 y lista vacia sobre base limpia."""
        client = cliente
        respuesta = client.get("/reportes")
        assert respuesta.status_code == 200
        assert respuesta.json()["total"] == 0
        assert respuesta.json()["resultados"] == []

    def test_devuelve_reportes_creados(self, cliente: TestClient, datos: ReportesFabrica):
        """Devuelve los reportes creados en orden inverso de creacion."""
        client = cliente
        r1 = _post(client, datos, comuna="1")
        r2 = _post(client, datos, comuna="2")
        respuesta = client.get("/reportes")
        assert respuesta.json()["total"] == 2
        ids = [r["id"] for r in respuesta.json()["resultados"]]
        assert ids == [r2["id"], r1["id"]]

    def test_filtro_tipo_evento(self, cliente: TestClient, datos: ReportesFabrica):
        """Filtra por tipo_evento (solo los de ese tipo)."""
        client = cliente
        _post(client, datos, tipo_evento="sismo")
        _post(client, datos, tipo_evento="inundacion_subita")
        _post(client, datos, tipo_evento="sismo")
        respuesta = client.get("/reportes", params={"tipo_evento": ["sismo"]})
        assert respuesta.json()["total"] == 2
        for r in respuesta.json()["resultados"]:
            assert r["tipo_evento"] == "sismo"

    def test_filtro_servicio(self, cliente: TestClient, datos: ReportesFabrica):
        """Filtra por servicio_de_respuesta (OR, alguno de la lista)."""
        client = cliente
        _post(client, datos, servicios=["A", "G"])
        _post(client, datos, servicios=["B"])
        respuesta = client.get("/reportes", params={"servicio_de_respuesta": ["A"]})
        assert respuesta.json()["total"] == 1
        assert respuesta.json()["resultados"][0]["id"] == "rpt-1"

    def test_filtro_comuna(self, cliente: TestClient, datos: ReportesFabrica):
        """Filtra por comuna exacta."""
        client = cliente
        _post(client, datos, comuna="1")
        _post(client, datos, comuna="2")
        respuesta = client.get("/reportes", params={"comuna": "2"})
        assert respuesta.json()["total"] == 1
        assert respuesta.json()["resultados"][0]["comuna"] == "2"

    def test_filtro_accionable(self, cliente: TestClient, datos: ReportesFabrica):
        """Filtra por accionable=True."""
        client = cliente
        _post(client, datos, accionable=True)
        _post(client, datos, accionable=False)
        respuesta = client.get("/reportes", params={"accionable": True})
        assert respuesta.json()["total"] == 1
        assert respuesta.json()["resultados"][0]["accionable"] is True

    def test_filtro_estado_revision(self, cliente: TestClient, datos: ReportesFabrica):
        """Filtra por estado_revision."""
        client = cliente
        _post(client, datos, estado_revision="pendiente")
        _post(client, datos, estado_revision="revisado")
        respuesta = client.get("/reportes", params={"estado_revision": "pendiente"})
        assert respuesta.json()["total"] == 1
        assert respuesta.json()["resultados"][0]["estado_revision"] == "pendiente"

    def test_listado_resumido_sin_mensaje(self, cliente: TestClient, datos: ReportesFabrica):
        """El listado NO incluye mensaje_anonimizado ni punto_referencia."""
        client = cliente
        _post(client, datos)
        resultado = client.get("/reportes").json()["resultados"][0]
        assert "mensaje_anonimizado" not in resultado
        assert "punto_referencia" not in resultado

    def test_listado_incluye_lat_lon(self, cliente: TestClient, datos: ReportesFabrica):
        """El listado SÃ incluye accionable, lat y lon."""
        client = cliente
        _post(client, datos, lat=3.5, lon=-76.6, accionable=True)
        resultado = client.get("/reportes").json()["resultados"][0]
        assert resultado["accionable"] is True
        assert resultado["lat"] == pytest.approx(3.5, abs=1e-6)
        assert resultado["lon"] == pytest.approx(-76.6, abs=1e-6)

    def test_paginacion_cap(self, cliente: TestClient, datos: ReportesFabrica):
        """El tamano de pagina se capa a 100 y pagina valida."""
        client = cliente
        for _ in range(5):
            _post(client, datos)
        respuesta = client.get("/reportes", params={"tamano_pagina": 200, "pagina": 1})
        assert respuesta.json()["tamano_pagina"] == 100

    def test_segunda_pagina(self, cliente: TestClient, datos: ReportesFabrica):
        """La segunda pagina devuelve el resto de reportes."""
        client = cliente
        for _ in range(3):
            _post(client, datos)
        p1 = client.get("/reportes", params={"tamano_pagina": 2}).json()
        assert len(p1["resultados"]) == 2
        assert p1["total"] == 3
        p2 = client.get("/reportes", params={"tamano_pagina": 2, "pagina": 2}).json()
        assert len(p2["resultados"]) == 1
        assert p2["total"] == 3


class TestObtenerReporte:
    """GET /reportes/{id_reporte}."""

    def test_devuelve_reporte_completo(self, cliente: TestClient, datos: ReportesFabrica):
        """Devuelve el reporte completo con todas las capas."""
        client = cliente
        payload = datos.reporte()
        client.post("/reportes", json=payload)
        respuesta = client.get(f"/reportes/{payload['id']}")
        assert respuesta.status_code == 200
        assert respuesta.json()["id"] == payload["id"]
        assert respuesta.json()["naturaleza"] is not None
        assert respuesta.json()["ubicacion"] is not None

    def test_devuelve_404_si_no_existe(self, cliente: TestClient):
        """Devuelve 404 si el id no esta en la base."""
        client = cliente
        respuesta = client.get("/reportes/no-existe")
        assert respuesta.status_code == 404

    def test_devuelve_naturaleza_none(self, cliente: TestClient, datos: ReportesFabrica):
        """Devuelve naturaleza=None cuando accionable=False."""
        client = cliente
        payload = datos.reporte(accionable=False)
        client.post("/reportes", json=payload)
        respuesta = client.get(f"/reportes/{payload['id']}")
        assert respuesta.json()["naturaleza"] is None


class TestActualizarReporte:
    """PATCH /reportes/{id_reporte}."""

    def test_cambia_estado_revision(self, cliente: TestClient, datos: ReportesFabrica):
        """Actualiza solo el estado_revision."""
        client = cliente
        payload = datos.reporte()
        client.post("/reportes", json=payload)
        respuesta = client.patch(
            f"/reportes/{payload['id']}",
            json={"estado_revision": "revisado"},
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["estado_revision"] == "revisado"

    def test_aplica_correccion(self, cliente: TestClient, datos: ReportesFabrica):
        """Corrige un campo de naturaleza."""
        client = cliente
        payload = datos.reporte(tipo_evento="sismo")
        client.post("/reportes", json=payload)
        respuesta = client.patch(
            f"/reportes/{payload['id']}",
            json={"correccion": {"tipo_evento": "inundacion_subita"}},
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["naturaleza"]["tipo_evento"] == "inundacion_subita"

    def test_correccion_compuerta(self, cliente: TestClient, datos: ReportesFabrica):
        """Corrige un campo de compuerta."""
        client = cliente
        payload = datos.reporte(temporalidad="ocurriendo_ahora")
        client.post("/reportes", json=payload)
        respuesta = client.patch(
            f"/reportes/{payload['id']}",
            json={"correccion": {"temporalidad": "ya_ocurrio"}},
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["compuerta"]["temporalidad"] == "ya_ocurrio"

    def test_correccion_ubicacion(self, cliente: TestClient, datos: ReportesFabrica):
        """Corrige un campo de ubicacion."""
        client = cliente
        payload = datos.reporte(comuna="1")
        client.post("/reportes", json=payload)
        respuesta = client.patch(
            f"/reportes/{payload['id']}",
            json={"correccion": {"comuna": "13"}},
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["ubicacion"]["comuna"] == "13"

    def test_devuelve_404_si_no_existe(self, cliente: TestClient):
        """Devuelve 404 si el id no esta en la base."""
        client = cliente
        respuesta = client.patch(
            "/reportes/no-existe",
            json={"estado_revision": "revisado"},
        )
        assert respuesta.status_code == 404

    def test_rechaza_correccion_desconocida(self, cliente: TestClient, datos: ReportesFabrica):
        """Devuelve 422 si la correccion tiene campos no conocidos."""
        client = cliente
        payload = datos.reporte()
        client.post("/reportes", json=payload)
        respuesta = client.patch(
            f"/reportes/{payload['id']}",
            json={"correccion": {"campo_fantasma": "valor"}},
        )
        assert respuesta.status_code == 422


class TestResumenReportes:
    """GET /reportes/resumen."""

    def test_estructura_resumen(self, cliente: TestClient, datos: ReportesFabrica):
        """Devuelve la estructura completa con todos los agregados."""
        client = cliente
        _post(client, datos, accionable=True, comuna="1", tipo_evento="sismo")
        _post(client, datos, accionable=False, comuna="2")
        respuesta = client.get("/reportes/resumen")
        assert respuesta.status_code == 200
        body = respuesta.json()
        assert body["total"] == 2
        assert body["pendientes"] == 2
        assert body["revisados"] == 0
        assert body["por_tipo_evento"]["sismo"] == 1
        assert body["por_comuna"]["1"] == 1
        assert body["por_accionable"]["accionable"] == 1
        assert body["por_accionable"]["no_accionable"] == 1

    def test_resumen_vacio(self, cliente: TestClient):
        """Devuelve ceros cuando no hay reportes."""
        client = cliente
        body = client.get("/reportes/resumen").json()
        assert body["total"] == 0
        assert body["pendientes"] == 0
        assert body["revisados"] == 0

    def test_filtro_desde_hasta(self, cliente: TestClient, datos: ReportesFabrica):
        """Filtra por rango de fechas (creado_en)."""
        client = cliente
        _post(client, datos, id_fijo="rpt-1", fecha_fija="2025-09-10T10:00:00Z")
        _post(client, datos, id_fijo="rpt-2", fecha_fija="2025-09-20T10:00:00Z")
        _post(client, datos, id_fijo="rpt-3", fecha_fija="2025-09-25T10:00:00Z")
        body = client.get(
            "/reportes/resumen",
            params={"desde": "2025-09-15", "hasta": "2025-09-24"},
        ).json()
        assert body["total"] == 1

"""Pruebas de la capa RepositorioReportes (sin endpoints HTTP)."""

from __future__ import annotations

import pytest
from sirena_schema.schema import ReporteEstructurado


from crud.db import FabricaSesiones
from crud.repositorio import (
    CorreccionInvalida,
    FiltrosReportes,
    ReporteNoEncontrado,
    RepositorioReportes,
)

from tests.crud.datos import ReportesFabrica


def _valido(reporte: dict) -> ReporteEstructurado:
    """Convierte un dict de la fabrica a `ReporteEstructurado` validado.

    Args:
        reporte: El dict devuelto por `ReportesFabrica.reporte`.

    Returns:
        El reporte validado por el esquema T-02.

    """
    return ReporteEstructurado.model_validate(reporte)


@pytest.fixture
def repo(base_temporal: FabricaSesiones) -> RepositorioReportes:
    """Repositorio sobre la base temporal del test.

    Args:
        base_temporal: Base SQLite temporal del fixture.

    Returns:
        Un repositorio con sesion ya abierta sobre esa base.

    """
    from sqlalchemy.orm import sessionmaker

    registro = sessionmaker(bind=base_temporal._engine_propio(), expire_on_commit=False)
    return RepositorioReportes(registro())


class TestCrearYObtener:
    """crear() y obtener()."""

    def test_crear_devuelve_reporte_completo(
        self, repo: RepositorioReportes, datos: ReportesFabrica
    ):
        """crear() persiste y devuelve el reporte completo."""
        reporte = _valido(datos.reporte())
        persistido = repo.crear(reporte)
        assert persistido.id == reporte.id
        assert persistido.naturaleza is not None
        assert persistido.naturaleza.tipo_evento == "sismo"

    def test_obtener_devuelve_el_mismo(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """obtener() recupera el reporte por id exacto."""
        reporte = _valido(datos.reporte())
        repo.crear(reporte)
        recuperado = repo.obtener(reporte.id)
        assert recuperado.id == reporte.id

    def test_obtener_lanza_404(self, repo: RepositorioReportes):
        """obtener() lanza ReporteNoEncontrado si el id no existe."""
        with pytest.raises(ReporteNoEncontrado):
            repo.obtener("no-existe")


class TestListar:
    """listar()."""

    def test_filtro_tipo_evento(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Filtra por tipo_evento (solo los de ese tipo)."""
        repo.crear(_valido(datos.reporte(tipo_evento="sismo")))
        repo.crear(_valido(datos.reporte(tipo_evento="inundacion_subita")))
        repo.crear(_valido(datos.reporte(tipo_evento="sismo")))
        total, reportes = repo.listar(FiltrosReportes(tipo_evento=["sismo"]))
        assert total == 2
        assert all(r.naturaleza.tipo_evento == "sismo" for r in reportes)

    def test_filtro_servicio(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Filtra por servicio_de_respuesta (OR sobre la lista JSON)."""
        repo.crear(_valido(datos.reporte(servicios=["A", "G"])))
        repo.crear(_valido(datos.reporte(servicios=["B"])))
        total, reportes = repo.listar(FiltrosReportes(servicio_de_respuesta=["A"]))
        assert total == 1
        assert reportes[0].id == "rpt-1"

    def test_filtro_comuna(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Filtra por comuna exacta."""
        repo.crear(_valido(datos.reporte(comuna="1")))
        repo.crear(_valido(datos.reporte(comuna="2")))
        total, reportes = repo.listar(FiltrosReportes(comuna="2"))
        assert total == 1
        assert reportes[0].ubicacion.comuna == "2"

    def test_filtro_accionable(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Filtra por accionable=True."""
        repo.crear(_valido(datos.reporte(accionable=True)))
        repo.crear(_valido(datos.reporte(accionable=False)))
        total, _ = repo.listar(FiltrosReportes(accionable=True))
        assert total == 1

    def test_filtro_estado(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Filtra por estado_revision."""
        repo.crear(_valido(datos.reporte(estado_revision="pendiente")))
        repo.crear(_valido(datos.reporte(estado_revision="revisado")))
        total, _ = repo.listar(FiltrosReportes(estado_revision="pendiente"))
        assert total == 1

    def test_filtro_q(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Busca texto libre en mensaje_anonimizado (case-sensitive)."""
        repo.crear(_valido(datos.reporte()))
        repo.crear(_valido(datos.reporte()))
        total, reportes = repo.listar(FiltrosReportes(q="prueba 1"))
        assert total == 1
        assert reportes[0].id == "rpt-1"

    def test_paginacion(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Devuelve paginas correctas y total independiente de la pagina."""
        for _ in range(5):
            repo.crear(_valido(datos.reporte()))
        total, p1 = repo.listar(FiltrosReportes(pagina=1, tamano_pagina=2))
        assert total == 5
        assert len(p1) == 2
        _, p2 = repo.listar(FiltrosReportes(pagina=2, tamano_pagina=2))
        assert len(p2) == 2
        _, p3 = repo.listar(FiltrosReportes(pagina=3, tamano_pagina=2))
        assert len(p3) == 1

    def test_orden_inverso_por_creado_en(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Ordena por creado_en descendente (mas reciente primero)."""
        repo.crear(_valido(datos.reporte(id_fijo="rpt-1", fecha_fija="2025-09-10T08:00:00Z")))
        repo.crear(_valido(datos.reporte(id_fijo="rpt-2", fecha_fija="2025-09-10T10:00:00Z")))
        _, reportes = repo.listar(FiltrosReportes())
        ids = [r.id for r in reportes]
        assert ids == ["rpt-2", "rpt-1"]

    def test_filtros_combinados(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Filtra por tipo_evento Y accionable a la vez."""
        repo.crear(_valido(datos.reporte(tipo_evento="sismo", accionable=True)))
        repo.crear(_valido(datos.reporte(tipo_evento="sismo", accionable=False)))
        repo.crear(_valido(datos.reporte(tipo_evento="inundacion_subita", accionable=True)))
        total, reportes = repo.listar(FiltrosReportes(tipo_evento=["sismo"], accionable=True))
        assert total == 1
        assert reportes[0].naturaleza.tipo_evento == "sismo"


class TestActualizar:
    """actualizar()."""

    def test_cambia_estado(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Cambia solo el estado_revision."""
        reporte = _valido(datos.reporte())
        repo.crear(reporte)
        actualizado = repo.actualizar(reporte.id, estado_revision="revisado", correccion=None)
        assert actualizado.estado_revision == "revisado"

    def test_aplica_correccion(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Corrige campos de naturaleza."""
        reporte = _valido(datos.reporte(tipo_evento="sismo"))
        repo.crear(reporte)
        actualizado = repo.actualizar(
            reporte.id, estado_revision=None, correccion={"tipo_evento": "inundacion_subita"}
        )
        assert actualizado.naturaleza.tipo_evento == "inundacion_subita"

    def test_rechaza_correccion_invalida(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Lanza CorreccionInvalida ante campos desconocidos."""
        reporte = _valido(datos.reporte())
        repo.crear(reporte)
        with pytest.raises(CorreccionInvalida):
            repo.actualizar(reporte.id, estado_revision=None, correccion={"campo_raro": "x"})

    def test_lanza_404_si_no_existe(self, repo: RepositorioReportes):
        """Lanza ReporteNoEncontrado si el id no existe."""
        with pytest.raises(ReporteNoEncontrado):
            repo.actualizar("no-existe", estado_revision="revisado", correccion=None)


class TestResumen:
    """resumen()."""

    def test_totales_y_pendientes(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Calcula pendientes y revisados."""
        repo.crear(_valido(datos.reporte(estado_revision="pendiente", accionable=True)))
        repo.crear(_valido(datos.reporte(estado_revision="revisado", accionable=True)))
        repo.crear(_valido(datos.reporte(estado_revision="pendiente", accionable=False)))
        res = repo.resumen()
        assert res["total"] == 3
        assert res["pendientes"] == 2
        assert res["revisados"] == 1

    def test_accionable_solo_acciona(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Agregados por tipo_evento/comuna/servicio solo cuentan accionables."""
        repo.crear(
            _valido(
                datos.reporte(accionable=True, tipo_evento="sismo", servicios=["A"], comuna="1")
            )
        )
        repo.crear(
            _valido(
                datos.reporte(accionable=False, tipo_evento="sismo", servicios=["A"], comuna="1")
            )
        )
        res = repo.resumen()
        assert res["por_tipo_evento"]["sismo"] == 1
        assert res["por_comuna"]["1"] == 1
        assert res["por_servicio_de_respuesta"]["A"] == 1
        assert res["por_accionable"]["accionable"] == 1
        assert res["por_accionable"]["no_accionable"] == 1

    def test_rango_de_fechas(self, repo: RepositorioReportes, datos: ReportesFabrica):
        """Filtra por rango desde/hasta sobre creado_en."""
        repo.crear(_valido(datos.reporte(id_fijo="rpt-1", fecha_fija="2025-09-10T10:00:00Z")))
        repo.crear(_valido(datos.reporte(id_fijo="rpt-2", fecha_fija="2025-09-20T10:00:00Z")))
        repo.crear(_valido(datos.reporte(id_fijo="rpt-3", fecha_fija="2025-09-25T10:00:00Z")))
        res = repo.resumen(desde="2025-09-15", hasta="2025-09-24")
        assert res["total"] == 1
        assert res["por_dia"]["2025-09-20"] == 1

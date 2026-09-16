"""Fixpoints compartidos de las pruebas del servicio CRUD.

Cada prueba obtiene una base SQLite temporal aislada, y la app FastAPI usa esa
base a traves de `fabrica_actual` (suplantada con `set_fabrica_actual`), sin
tocar `backend/crud/data/` ni crear bloqueos de archivo entre tests.
"""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from crud.db import FabricaSesiones
from crud.main import fabrica as fabrica_default, set_fabrica_actual

from tests.crud.datos import ReportesFabrica


@pytest.fixture
def base_temporal() -> Iterator[FabricaSesiones]:
    """Base SQLite temporal configurada, aislada por prueba.

    Crea la fabria sobre un archivo en `%TEMP%` y devuelve la fabria lista.
    La base se borra al terminar el test.

    Yields:
        La `FabricaSesiones` apuntando al archivo temporal.

    """
    ruta = Path(tempfile.mkstemp(suffix=".db", prefix="crud_test_")[1])
    fab = FabricaSesiones(url=f"sqlite:///{ruta.as_posix()}")
    fab.crear_esquema()
    yield fab
    fab._engine_propio().dispose(close=True)
    try:
        ruta.unlink(missing_ok=True)
    except PermissionError:
        # En Windows el archivo puede quedar retenido unos instantes por el
        # pool de conexiones; se recicla el proximo test con un nuevo tempfile.
        pass


@pytest.fixture
def cliente(base_temporal: FabricaSesiones) -> Iterator[TestClient]:
    """Cliente HTTP de la app con la base temporal como fabrica de sesiones.

    Args:
        base_temporal: Base aislada que reemplaza a la fabrica default.

    Yields:
        Un `TestClient` listo; la lifespan crea el esquema en la base temporal.

    """
    set_fabrica_actual(base_temporal)
    with TestClient(app=_importar_app()) as client:
        yield client
    set_fabrica_actual(fabrica_default)


def _importar_app():
    """Devuelve la app FastAPI para construir el TestClient.

    Returns:
        La instancia global de FastAPI de `crud.main`.

    """
    from crud.main import app as _app

    return _app


@pytest.fixture
def datos() -> ReportesFabrica:
    """Fabrica de reportes con valores unicos por test.

    Returns:
        Una instancia de `ReportesFabrica` con ids independientes.

    """
    return ReportesFabrica()

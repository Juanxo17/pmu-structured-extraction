"""Configuracion de la base de datos SQLite y las sesiones SQLAlchemy del CRUD.

El esquema se crea automaticamente al arrancar el servicio (`create_all`); en
pruebas se usa SQLite en memoria. La ruta del archivo se configura con la
variable de entorno `CRUD_DATABASE_PATH` y la ruta por defecto es `data/sirena.db`
bajo `backend/crud/`. La conexion se abre de forma perezosa (al primer uso), de
modo que importar el modulo no toca el sistema de archivos.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from crud.repositorio import RepositorioReportes

_ESTADO = {"engine": None, "factory": None}


def _engine_global() -> Engine:
    """Crea una sola vez el engine SQLite global (lazy).

    Returns:
        El engine listo para crear el esquema y abrir sesiones.

    """
    if _ESTADO["engine"] is None:
        ruta = os.environ.get("CRUD_DATABASE_PATH")
        if ruta:
            url = f"sqlite:///{ruta}"
        else:
            carpeta = Path(__file__).resolve().parent.parent / "data"
            carpeta.mkdir(parents=True, exist_ok=True)
            url = f"sqlite:///{(carpeta / 'sirena.db').as_posix()}"
        _ESTADO["engine"] = create_engine(url, connect_args={"check_same_thread": False})
    return _ESTADO["engine"]


def _factory_global() -> sessionmaker[Session]:
    """Crea una sola vez el sessionmaker global (lazy).

    Returns:
        La factory de sesiones vinculada al engine global.

    """
    if _ESTADO["factory"] is None:
        _ESTADO["factory"] = sessionmaker(bind=_engine_global(), expire_on_commit=False)
    return _ESTADO["factory"]


def fabrica_sesiones() -> Generator[Session, None, None]:
    """Generador de sesiones para FastAPI `Depends`.

    Yields:
        Una sesion con autocommit en la operacion; cierra al terminar la
        peticion.

    """
    sesion = _factory_global()()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


def crear_esquema() -> None:
    """Crea las tablas faltantes (idempotente) sobre el engine global."""
    from crud.modelo import Base

    Base.metadata.create_all(bind=_engine_global())


def repositorio(sesion: Session) -> RepositorioReportes:
    """Crea un repositorio sobre la sesion de la peticion.

    Args:
        sesion: Sesion inyectada por `fabrica_sesiones`.

    Returns:
        Repositorio listo para la peticion.

    """
    return RepositorioReportes(sesion)


class FabricaSesiones:
    """Fabrica de sesiones (base configurable; compatible con la API de la app).

    Usada por la app para inyectar sesiones y por las pruebas para aislar
    comletamente la base. Es un envoltorio sobre `create_engine`/`sessionmaker`.
    """

    def __init__(self, url: str | None = None) -> None:
        """Prepara (sin conectar aun) un engine para la base indicada.

        Args:
            url: URL de conexion SQLAlchemy (`sqlite:///...`); si no se da, se
                usa `CRUD_DATABASE_PATH` y, faltando, `data/sirena.db`.

        """
        if url is None:
            ruta = os.environ.get("CRUD_DATABASE_PATH")
            if ruta:
                url = f"sqlite:///{ruta}"
            else:
                carpeta = Path(__file__).resolve().parent.parent / "data"
                carpeta.mkdir(parents=True, exist_ok=True)
                url = f"sqlite:///{(carpeta / 'sirena.db').as_posix()}"
        self._url = url
        self._engine = None
        self._factory = None

    def _engine_propio(self) -> Engine:
        """Crea el engine propio sobre la base configurada (lazy).

        Returns:
            El engine de esta fabria.

        """
        if self._engine is None:
            self._engine = create_engine(self._url, connect_args={"check_same_thread": False})
        return self._engine

    def _factory_propia(self) -> sessionmaker[Session]:
        """Crea el sessionmaker propio (lazy).

        Returns:
            La factory vinculada al engine de esta fabria.

        """
        if self._factory is None:
            self._factory = sessionmaker(bind=self._engine_propio(), expire_on_commit=False)
        return self._factory

    def crear_esquema(self) -> None:
        """Crea las tablas faltantes (idempotente) en la base de esta fabria."""
        from crud.modelo import Base

        Base.metadata.create_all(bind=self._engine_propio())

    def sesion(self) -> Generator[Session, None, None]:
        """Generador de sesiones para FastAPI `Depends`.

        Yields:
            Una sesion con autocommit en la operacion; cierra al terminar la
            peticion.

        """
        sesion = self._factory_propia()()
        try:
            yield sesion
            sesion.commit()
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()

    def repositorio(self, sesion: Session) -> RepositorioReportes:
        """Crea un repositorio sobre la sesion de la peticion.

        Args:
            sesion: Sesion inyectada por `self.sesion`.

        Returns:
            Repositorio listo para la peticion.

        """
        return RepositorioReportes(sesion)


fabrica = FabricaSesiones()

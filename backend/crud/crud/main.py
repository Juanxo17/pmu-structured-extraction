"""Punto de entrada FastAPI del servicio CRUD.

Endpoints del contrato (docs/CONTRATOS_SISTEMA.md, seccion 2): POST /reportes,
GET /reportes, GET /reportes/{id}, PATCH /reportes/{id} y GET /reportes/resumen.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sirena_schema.schema import ReporteEstructurado

from crud.api import CorreccionRequest, PaginaReportes, ResumenReportes, a_resumen
from crud.db import FabricaSesiones, fabrica
from crud.repositorio import CorreccionInvalida, FiltrosReportes, ReporteNoEncontrado

# Fabrica de sesiones de la app; `set_fabrica_actual()` la suplanta en pruebas
# para correr sobre una base aislada sin tocar `backend/crud/data/`.
fabrica_actual: FabricaSesiones = fabrica


def set_fabrica_actual(fabrica_nueva: FabricaSesiones) -> None:
    """Define la fabria de sesiones vigente para la app.

    Args:
        fabrica_nueva: Fabria que usan los endpoints y la lifespan.

    """
    global fabrica_actual
    fabrica_actual = fabrica_nueva


def _sesion_actual() -> AsyncIterator[Session]:
    """Generador de sesiones de la fabrica vigente (inyectable).

    Yields:
        Sesion que `fabrica_actual` abre para la peticion.

    """
    yield from fabrica_actual.sesion()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Crea el esquema SQLite al arrancar (idempotente)."""
    fabrica_actual.crear_esquema()
    yield


app = FastAPI(
    title="SIRENA - CRUD",
    lifespan=_lifespan,
)


def _repositorio(
    sesion: Annotated[Session, Depends(_sesion_actual)],
):
    """Inyecta el repositorio con la sesion de la peticion.

    Args:
        sesion: Sesion abierta por `fabrica_actual.sesion`.

    Returns:
        Repositorio listo para la peticion.

    """
    return fabrica_actual.repositorio(sesion)


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}


@app.post("/reportes", response_model=ReporteEstructurado, status_code=201)
def crear_reporte(
    reporte: ReporteEstructurado,
    repositorio: Annotated[object, Depends(_repositorio)],
) -> ReporteEstructurado:
    """Guarda el reporte estructurado (llamado por Process al final del pipeline).

    Args:
        reporte: Reporte a guardar.
        repositorio: Repositorio inyectado.

    Returns:
        El reporte tal como quedo persistido.

    Raises:
        HTTPException 409: Si `id` o `id_externo` ya existen.

    """
    try:
        return repositorio.crear(reporte)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="el reporte ya existe (id o id_externo duplicado)",
        ) from None


@app.get("/reportes", response_model=PaginaReportes)
def listar_reportes(
    tipo_evento: Annotated[list[str] | None, Query()] = None,
    servicio_de_respuesta: Annotated[list[str] | None, Query()] = None,
    comuna: str | None = Query(default=None),
    barrio: str | None = Query(default=None),
    temporalidad: str | None = Query(default=None),
    intencion: str | None = Query(default=None),
    estado_revision: str | None = Query(default=None),
    nivel_granularidad: str | None = Query(default=None),
    accionable: bool | None = Query(default=None),
    desde: str | None = Query(default=None),
    hasta: str | None = Query(default=None),
    q: str | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    tamano_pagina: int = Query(default=20, ge=1),
    repositorio: Annotated[object, Depends(_repositorio)] = None,
) -> PaginaReportes:
    """Lista reportes (version resumida) con filtros y paginacion.

    Aplica los filtros del contrato (docs/CONTRATOS_SISTEMA.md, seccion 2);
    `tamano_pagina` se capa a 100 en `FiltrosReportes.tamano_validado`.

    Args:
        tipo_evento: Tipo(s) de evento a incluir (OR).
        servicio_de_respuesta: Servicio(s) de respuesta (OR sobre la lista).
        comuna: Comuna a incluir.
        barrio: Barrio a incluir.
        temporalidad: Temporalidad de la compuerta.
        intencion: Intencion de la compuerta.
        estado_revision: Estado de revision.
        nivel_granularidad: Nivel de granularidad de la ubicacion.
        accionable: Filtra por `es_reporte_accionable`.
        desde: Fecha `YYYY-MM-DD` de inicio (por `creado_en`).
        hasta: Fecha `YYYY-MM-DD` de fin (inclusive).
        q: Busqueda libre sobre `mensaje_anonimizado`.
        pagina: Numero de pagina (desde 1).
        tamano_pagina: Cantidad por pagina (se capa a 100, default 20).
        repositorio: Repositorio inyectado.

    Returns:
        Pagina de reportes resumidos (sin mensaje ni punto de referencia).

    """
    filtros = FiltrosReportes(
        tipo_evento=tipo_evento or [],
        servicio_de_respuesta=servicio_de_respuesta or [],
        comuna=comuna,
        barrio=barrio,
        temporalidad=temporalidad,
        intencion=intencion,
        estado_revision=estado_revision,
        nivel_granularidad=nivel_granularidad,
        accionable=accionable,
        desde=desde,
        hasta=hasta,
        q=q,
        pagina=pagina,
        tamano_pagina=tamano_pagina,
    )
    total, reportes = repositorio.listar(filtros)
    pagina_respuesta = PaginaReportes(
        total=total,
        pagina=filtros.pagina,
        tamano_pagina=filtros.tamano_validado(),
        resultados=[a_resumen(r) for r in reportes],
    )
    return pagina_respuesta


@app.get("/reportes/resumen", response_model=ResumenReportes)
def resumen_reportes(
    desde: str | None = Query(default=None),
    hasta: str | None = Query(default=None),
    repositorio: Annotated[object, Depends(_repositorio)] = None,
) -> ResumenReportes:
    """Devuelve los agregados para las tarjetas del encabezado del tablero.

    Debe declararse antes que `/reportes/{id_reporte}`: FastAPI resuelve las
    rutas en orden de registro y `resumen` coincidiria con el `{id_reporte}`.

    Args:
        desde: Fecha `YYYY-MM-DD` de inicio.
        hasta: Fecha `YYYY-MM-DD` de fin.
        repositorio: Repositorio inyectado.

    Returns:
        Los agregados calculados por el repositorio.

    """
    return repositorio.resumen(desde=desde, hasta=hasta)


@app.get("/reportes/{id_reporte}", response_model=ReporteEstructurado)
def obtener_reporte(
    id_reporte: str = Path(...),
    repositorio: Annotated[object, Depends(_repositorio)] = None,
) -> ReporteEstructurado:
    """Obtiene el reporte completo por id.

    Args:
        id_reporte: Id del reporte.
        repositorio: Repositorio inyectado.

    Returns:
        El reporte completo.

    Raises:
        HTTPException 404: Si el reporte no existe.

    """
    try:
        return repositorio.obtener(id_reporte)
    except ReporteNoEncontrado:
        raise HTTPException(status_code=404, detail="reporte no encontrado") from None


@app.patch("/reportes/{id_reporte}", response_model=ReporteEstructurado)
def actualizar_reporte(
    cambios: CorreccionRequest,
    id_reporte: str = Path(...),
    repositorio: Annotated[object, Depends(_repositorio)] = None,
) -> ReporteEstructurado:
    """Aplica un triaje: cambio de estado y/o correccion de campos.

    Args:
        cambios: `estado_revision` opcional y `correccion` parcial.
        id_reporte: Id del reporte.
        repositorio: Repositorio inyectado.

    Returns:
        El reporte actualizado.

    Raises:
        HTTPException 404: Si el reporte no existe.
        HTTPException 422: Si la correccion referencia campos desconocidos.

    """
    try:
        return repositorio.actualizar(
            id_reporte,
            estado_revision=cambios.estado_revision,
            correccion=cambios.correccion,
        )
    except ReporteNoEncontrado:
        raise HTTPException(status_code=404, detail="reporte no encontrado") from None
    except CorreccionInvalida as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

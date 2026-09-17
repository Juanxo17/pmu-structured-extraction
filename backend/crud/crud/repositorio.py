"""Capa de acceso a datos del servicio CRUD.

Implementa las operaciones del contrato (docs/CONTRATOS_SISTEMA.md, seccion 2)
sobre el modelo SQLAlchemy: crear, listar (filtros + paginacion), obtener,
actualizar con correccion parcial y agregados de `/reportes/resumen`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from sirena_schema.schema import Compuerta, Naturaleza, ReporteEstructurado, Ubicacion

from crud.modelo import Reporte, TAMANO_PAGINA_DEFAULT, TAMANO_PAGINA_MAXIMO

_CAMPOS_POR_SECCION = {
    "compuerta": {"es_reporte_accionable", "temporalidad", "intencion"},
    "naturaleza": {"tipo_evento", "servicio_de_respuesta"},
    "ubicacion": {
        "ubicacion_texto_literal",
        "comuna",
        "barrio",
        "punto_referencia",
        "nivel_granularidad",
        "lat",
        "lon",
    },
}

_SECCIONES_POR_CAMPO = {
    "compuerta": Compuerta,
    "naturaleza": Naturaleza,
    "ubicacion": Ubicacion,
}

# Campos anulables que, al reconstruir una seccion desde cero, se asumen en
# `None` salvo que la correccion los provea (el esquema exige pasarlos aunque
# valgan None).
_NULOS_POR_SECCION = {
    "ubicacion": {
        "barrio": None,
        "comuna": None,
        "punto_referencia": None,
        "lat": None,
        "lon": None,
    },
}


@dataclass(frozen=True)
class FiltrosReportes:
    """Filtros de `GET /reportes` (mismas claves y semantica que el Frontend).

    `desde`/`hasta` son fechas `YYYY-MM-DD` (sin huso) que se interpretan en
    medianoche UTC, igual que en el mock del Frontend.
    """

    tipo_evento: list[str] = field(default_factory=list)
    servicio_de_respuesta: list[str] = field(default_factory=list)
    comuna: str | None = None
    barrio: str | None = None
    temporalidad: str | None = None
    intencion: str | None = None
    estado_revision: str | None = None
    nivel_granularidad: str | None = None
    accionable: bool | None = None
    desde: str | None = None
    hasta: str | None = None
    q: str | None = None
    pagina: int = 1
    tamano_pagina: int = TAMANO_PAGINA_DEFAULT

    def tamano_validado(self) -> int:
        """Devuelve `tamano_pagina` dentro del maximo del contrato.

        Returns:
            El tamano de pagina a usar, capado a `TAMANO_PAGINA_MAXIMO`.

        """
        return min(self.tamano_pagina, TAMANO_PAGINA_MAXIMO)


class ReporteNoEncontrado(Exception):
    """Se lanza cuando un `id` pedido no existe en la base de datos."""


class CorreccionInvalida(ValueError):
    """Se lanza cuando una correccion referencia campos no conocidos."""


def _inicio_de_dia(fecha_iso: str) -> datetime:
    """Convierte una fecha `YYYY-MM-DD` en medianoche UTC.

    Args:
        fecha_iso: Fecha en formato `YYYY-MM-DD`.

    Returns:
        La medianoche de esa fecha, con huso UTC.

    """
    valor = datetime.fromisoformat(fecha_iso)
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor


class RepositorioReportes:
    """Operaciones de persistencia sobre la sesion SQLAlchemy inyectada."""

    def __init__(self, sesion: Session) -> None:
        """Crea el repositorio sobre una sesion.

        Args:
            sesion: Sesion SQLAlchemy activa (una por peticion, creada por la
                app). El repositorio no la abre ni la cierra.

        """
        self._sesion = sesion

    def crear(self, reporte: ReporteEstructurado) -> ReporteEstructurado:
        """Guarda el reporte nuevo.

        Args:
            reporte: Reporte estructurado a guardar.

        Returns:
            El reporte tal como quedo persistido.

        Raises:
            sqlalchemy.exc.IntegrityError: Si `id` o `id_externo` ya existen
                (la app la traduce a HTTP 409).

        """
        modelo = Reporte.desde_pydantic(reporte)
        self._sesion.add(modelo)
        self._sesion.flush()
        return modelo.a_pydantic()

    def obtener(self, id_reporte: str) -> ReporteEstructurado:
        """Obtiene el reporte completo por id.

        Args:
            id_reporte: Id del reporte.

        Returns:
            El reporte completo.

        Raises:
            ReporteNoEncontrado: Si el id no existe.

        """
        modelo = self._sesion.get(Reporte, id_reporte)
        if modelo is None:
            raise ReporteNoEncontrado(id_reporte)
        return modelo.a_pydantic()

    def _aplicar_filtros(self, filtros: FiltrosReportes) -> Select[tuple[Reporte]]:
        """Construye la consulta `select(Reporte)` con los filtros definidos.

        Args:
            filtros: Filtros activos de `GET /reportes`.

        Returns:
            La consulta lista para paginarse y ejecutarse.

        """
        consulta = select(Reporte)
        if filtros.tipo_evento:
            consulta = consulta.where(Reporte.tipo_evento.in_(filtros.tipo_evento))
        if filtros.servicio_de_respuesta:
            condiciones = [
                Reporte.servicios.like(f'%"{codigo}"%')
                for codigo in set(filtros.servicio_de_respuesta)
            ]
            if condiciones:
                consulta = consulta.where(or_(*condiciones))
        if filtros.comuna:
            consulta = consulta.where(Reporte.comuna == filtros.comuna)
        if filtros.barrio:
            consulta = consulta.where(Reporte.barrio == filtros.barrio)
        if filtros.temporalidad:
            consulta = consulta.where(Reporte.temporalidad == filtros.temporalidad)
        if filtros.intencion:
            consulta = consulta.where(Reporte.intencion == filtros.intencion)
        if filtros.estado_revision:
            consulta = consulta.where(Reporte.estado_revision == filtros.estado_revision)
        if filtros.nivel_granularidad:
            consulta = consulta.where(Reporte.nivel_granularidad == filtros.nivel_granularidad)
        if filtros.accionable is not None:
            consulta = consulta.where(Reporte.accionable == filtros.accionable)
        if filtros.desde:
            consulta = consulta.where(Reporte.creado_en >= _inicio_de_dia(filtros.desde))
        if filtros.hasta:
            consulta = consulta.where(
                Reporte.creado_en < _inicio_de_dia(filtros.hasta) + timedelta(days=1)
            )
        if filtros.q:
            consulta = consulta.where(Reporte.mensaje_anonimizado.like(f"%{filtros.q.lower()}%"))
        return consulta

    def listar(self, filtros: FiltrosReportes) -> tuple[int, list[ReporteEstructurado]]:
        """Lista reportes completos filtrados y paginados.

        Args:
            filtros: Filtros y pagina/tamano a usar.

        Returns:
            Tupla (total_de_filtrados, pagina_de_reportes). El `tamano_pagina`
            se capa al maximo del contrato.

        """
        desde = select(func.count()).select_from(self._aplicar_filtros(filtros).subquery())
        total = self._sesion.scalar(desde) or 0
        tamano = filtros.tamano_validado()
        filas = (
            self._sesion.scalars(
                self._aplicar_filtros(filtros)
                .order_by(Reporte.creado_en.desc())
                .offset((filtros.pagina - 1) * tamano)
                .limit(tamano)
            )
        ).all()
        return total, [f.a_pydantic() for f in filas]

    def actualizar(
        self,
        id_reporte: str,
        estado_revision: str | None,
        correccion: dict[str, object] | None,
    ) -> ReporteEstructurado:
        """Aplica un triaje: cambio de estado y/o correccion de campos.

        Args:
            id_reporte: Id del reporte a actualizar.
            estado_revision: Nuevo estado (`pendiente`/`revisado`), o None si
                solo se corrige.
            correccion: Dict plano de campos de compuerta/naturaleza/ubicacion
                a corregir (ver `PATCH /reportes/{id}` en el contrato).

        Returns:
            El reporte actualizado.

        Raises:
            ReporteNoEncontrado: Si el id no existe.
            CorreccionInvalida: Si la correccion referencia campos no conocidos.
            pydantic.ValidationError: Si el resultado de la correccion no
                conforma al esquema (ontologia fuera de catalogo, seccion
                incompleta) o no se impone el invariante de reportes no
                accionables. La app la traduce a HTTP 422.

        """
        modelo = self._sesion.get(Reporte, id_reporte)
        if modelo is None:
            raise ReporteNoEncontrado(id_reporte)
        reporte = modelo.a_pydantic()
        if estado_revision is not None:
            reporte = reporte.model_copy(update={"estado_revision": estado_revision})
        if correccion:
            reporte = _aplicar_correccion(reporte, correccion)
        # `model_copy` no re-valida (Pydantic v2); se fuerza la validacion
        # completa para que la ontologia, los campos requeridos y el invariante
        # "no accionable => secciones vacias" se cumplan antes de persistir.
        reporte = ReporteEstructurado.model_validate(reporte.model_dump())
        actualizado = Reporte.desde_pydantic(reporte)
        modelo.payload = actualizado.payload
        modelo.fuente = actualizado.fuente
        modelo.id_externo = actualizado.id_externo
        modelo.autor_anonimizado_id = actualizado.autor_anonimizado_id
        modelo.mensaje_anonimizado = actualizado.mensaje_anonimizado
        modelo.estado_revision = actualizado.estado_revision
        modelo.creado_en = actualizado.creado_en
        modelo.tipo_evento = actualizado.tipo_evento
        modelo.accionable = actualizado.accionable
        modelo.temporalidad = actualizado.temporalidad
        modelo.intencion = actualizado.intencion
        modelo.comuna = actualizado.comuna
        modelo.barrio = actualizado.barrio
        modelo.nivel_granularidad = actualizado.nivel_granularidad
        modelo.servicios = actualizado.servicios
        self._sesion.flush()
        return self.obtener(id_reporte)

    def eliminar(self, id_reporte: str) -> None:
        """Elimina un reporte por id (uso interno/test, fuera del contrato).

        Args:
            id_reporte: Id del reporte a eliminar.

        Raises:
            ReporteNoEncontrado: Si el id no existe.

        """
        modelo = self._sesion.get(Reporte, id_reporte)
        if modelo is None:
            raise ReporteNoEncontrado(id_reporte)
        self._sesion.delete(modelo)
        self._sesion.flush()

    def resumen(self, desde: str | None = None, hasta: str | None = None) -> dict[str, object]:
        """Calcula los agregados de `/reportes/resumen` en el rango dado.

        Args:
            desde: Fecha `YYYY-MM-DD` de inicio (inclusive).
            hasta: Fecha `YYYY-MM-DD` de fin (inclusive, se interpreta hasta
                la medianoche del dia siguiente).

        Returns:
            Del mismo universo de reportes en el rango se derivan total,
            pendientes, revisados y los agregados por dimension. `por_tipo_evento`,
            `por_comuna`, `por_servicio_de_respuesta` y `por_nivel_granularidad`
            solo cuentan reportes accionables (con naturaleza/ubicacion);
            `por_temporalidad`, `por_intencion`, `por_accionable` y `por_dia`
            cuentan todos.

        """
        filtros = FiltrosReportes(desde=desde, hasta=hasta, tamano_pagina=TAMANO_PAGINA_MAXIMO)
        total, todos = self.listar(filtros)
        if len(todos) < total:
            restantes = total - len(todos)
            cuantas_paginas = (restantes - 1) // TAMANO_PAGINA_MAXIMO + 1
            for pagina in range(2, 2 + cuantas_paginas):
                _, reportes = self.listar(FiltrosReportes(**{**filtros.__dict__, "pagina": pagina}))
                todos.extend(reportes)
        por_tipo: dict[str, int] = {}
        por_comuna: dict[str, int] = {}
        por_accionable = {"accionable": 0, "no_accionable": 0}
        por_temporalidad: dict[str, int] = {}
        por_intencion: dict[str, int] = {}
        por_servicio: dict[str, int] = {}
        por_granularidad: dict[str, int] = {}
        por_dia: dict[str, int] = {}
        pendientes = 0
        revisados = 0
        for reporte in todos:
            if reporte.estado_revision == "pendiente":
                pendientes += 1
            else:
                revisados += 1
            clave_dia = reporte.creado_en.date().isoformat()
            por_dia[clave_dia] = por_dia.get(clave_dia, 0) + 1
            clave_accionable = (
                "accionable" if reporte.compuerta.es_reporte_accionable else "no_accionable"
            )
            por_accionable[clave_accionable] += 1
            por_temporalidad[reporte.compuerta.temporalidad] = (
                por_temporalidad.get(reporte.compuerta.temporalidad, 0) + 1
            )
            por_intencion[reporte.compuerta.intencion] = (
                por_intencion.get(reporte.compuerta.intencion, 0) + 1
            )
            if not reporte.compuerta.es_reporte_accionable:
                continue
            if reporte.naturaleza is None:
                continue
            por_tipo[reporte.naturaleza.tipo_evento] = (
                por_tipo.get(reporte.naturaleza.tipo_evento, 0) + 1
            )
            for servicio in reporte.naturaleza.servicio_de_respuesta:
                por_servicio[servicio] = por_servicio.get(servicio, 0) + 1
            if reporte.ubicacion is None:
                continue
            por_comuna[reporte.ubicacion.comuna or "indeterminada"] = (
                por_comuna.get(reporte.ubicacion.comuna or "indeterminada", 0) + 1
            )
            por_granularidad[reporte.ubicacion.nivel_granularidad] = (
                por_granularidad.get(reporte.ubicacion.nivel_granularidad, 0) + 1
            )
        return {
            "total": total,
            "pendientes": pendientes,
            "revisados": revisados,
            "por_tipo_evento": por_tipo,
            "por_comuna": por_comuna,
            "por_accionable": por_accionable,
            "por_temporalidad": por_temporalidad,
            "por_intencion": por_intencion,
            "por_servicio_de_respuesta": por_servicio,
            "por_nivel_granularidad": por_granularidad,
            "por_dia": por_dia,
        }


def _aplicar_correccion(
    reporte: ReporteEstructurado, correccion: dict[str, object]
) -> ReporteEstructurado:
    """Aplica una correccion parcial plana sobre compuerta/naturaleza/ubicacion.

    Si la seccion ya existe se actualiza con `model_copy` (la validacion
    completa se fuerza luego en `actualizar`); si la seccion es `None` (un
    reporte no accionable que se vuelve accionable) se reconstruye desde los
    campos provistos, validando sus campos requeridos al instante.

    Args:
        reporte: Reporte original.
        correccion: Dict plano; cada llave debe pertenecer a exactamente una
            de las secciones compuerta/naturaleza/ubicacion.

    Returns:
        Una copia del reporte con la seccion correspondiente actualizada.

    Raises:
        CorreccionInvalida: Si alguna llave no pertenece a ninguna seccion
            conocida o a un campo protegido.

    """
    conocidas: set[str] = set()
    actualizado = reporte
    for seccion, campos in _CAMPOS_POR_SECCION.items():
        conocidas |= campos
        cambios_seccion = {k: v for k, v in correccion.items() if k in campos}
        if not cambios_seccion:
            continue
        actual = getattr(actualizado, seccion)
        if actual is None:
            campos_completos = {**_NULOS_POR_SECCION.get(seccion, {}), **cambios_seccion}
            actual = _SECCIONES_POR_CAMPO[seccion](**campos_completos)
        else:
            actual = actual.model_copy(update=cambios_seccion)
        actualizado = actualizado.model_copy(update={seccion: actual})
    desconocidas = set(correccion) - conocidas
    if desconocidas:
        raise CorreccionInvalida(f"campos de correccion desconocidos: {sorted(desconocidas)}")
    return actualizado

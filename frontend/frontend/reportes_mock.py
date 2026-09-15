"""Cliente simulado de `/reportes`, para desarrollar el frontend sin BFF.

Se activa automáticamente cuando la variable de entorno `BFF_URL` no está
definida (ver `frontend.bandeja.elegir_cliente`) — mismo principio que
`docs/CONTRATOS_SISTEMA.md` describe para el resto de servicios: "cada
servicio se mockea contra este contrato mientras los demás no estén listos".

El dataset se construye instanciando `ReporteEstructurado` por cada registro,
así que si alguna vez se desalinea del esquema compartido, la importación de
este módulo falla de inmediato en vez de dejarlo pasar en silencio.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sirena_schema.schema import Compuerta, Naturaleza, ReporteEstructurado, Ubicacion

from frontend.bff_client import (
    ClienteReportes,
    FiltrosReportes,
    PaginaReportes,
    ReporteResumen,
    ResumenReportes,
)

_AHORA = datetime(2026, 9, 15, 8, 0, tzinfo=timezone.utc)

_CAMPOS_POR_SECCION: dict[str, set[str]] = {
    "compuerta": {"es_reporte_accionable", "temporalidad", "intencion"},
    "naturaleza": {"tipo_evento", "servicio_de_respuesta"},
    "ubicacion": {
        "ubicacion_texto_literal",
        "barrio",
        "comuna",
        "punto_referencia",
        "nivel_granularidad",
        "lat",
        "lon",
    },
}


def _reporte(
    sufijo: str,
    minutos_desde_ahora: int,
    tipo_evento: str,
    servicios: list[str],
    comuna: str,
    barrio: str,
    ref: str | None,
    temporalidad: str,
    intencion: str,
    estado: str,
    granularidad: str,
    mensaje: str,
) -> ReporteEstructurado:
    """Arma un ReporteEstructurado de ejemplo con los campos mínimos variables.

    Args:
        sufijo: Sufijo corto para el id y el id_externo del reporte.
        minutos_desde_ahora: Antigüedad del reporte respecto a `_AHORA`.
        tipo_evento: Ver `config/ontologia.yaml`.
        servicios: Códigos de servicio_de_respuesta.
        comuna: Comuna resuelta por Geo (mock).
        barrio: Barrio resuelto por Geo (mock).
        ref: Punto de referencia libre, o None si no se reportó.
        temporalidad: Ver Compuerta.
        intencion: Ver Compuerta.
        estado: "pendiente" o "revisado".
        granularidad: Ver Ubicacion.nivel_granularidad.
        mensaje: Texto ya anonimizado del reporte.

    Returns:
        El reporte de ejemplo, validado contra el esquema compartido.

    """
    return ReporteEstructurado(
        id=f"rpt_{sufijo}",
        fuente="telegram",
        id_externo=f"tg_{sufijo}",
        autor_anonimizado_id=f"anon_{sufijo}",
        mensaje_anonimizado=mensaje,
        estado_revision=estado,
        compuerta=Compuerta(
            es_reporte_accionable=True, temporalidad=temporalidad, intencion=intencion
        ),
        naturaleza=Naturaleza(tipo_evento=tipo_evento, servicio_de_respuesta=servicios),
        ubicacion=Ubicacion(
            ubicacion_texto_literal=ref or f"{barrio}, {comuna}",
            barrio=barrio,
            comuna=comuna,
            punto_referencia=ref,
            nivel_granularidad=granularidad,
            lat=None,
            lon=None,
        ),
        creado_en=_AHORA - timedelta(minutes=minutos_desde_ahora),
    )


def _reporte_no_accionable(
    sufijo: str,
    minutos_desde_ahora: int,
    temporalidad: str,
    intencion: str,
    estado: str,
    mensaje: str,
) -> ReporteEstructurado:
    """Arma un ReporteEstructurado de ejemplo descartado en la compuerta (etapa 1).

    Sin `naturaleza` ni `ubicacion`, tal como los deja Process cuando
    `es_reporte_accionable = False` (ver docs/CONTRATOS_SISTEMA.md).

    Args:
        sufijo: Sufijo corto para el id y el id_externo del reporte.
        minutos_desde_ahora: Antigüedad del reporte respecto a `_AHORA`.
        temporalidad: Ver Compuerta.
        intencion: Ver Compuerta.
        estado: "pendiente" o "revisado".
        mensaje: Texto ya anonimizado del reporte.

    Returns:
        El reporte de ejemplo, validado contra el esquema compartido.

    """
    return ReporteEstructurado(
        id=f"rpt_{sufijo}",
        fuente="telegram",
        id_externo=f"tg_{sufijo}",
        autor_anonimizado_id=f"anon_{sufijo}",
        mensaje_anonimizado=mensaje,
        estado_revision=estado,
        compuerta=Compuerta(
            es_reporte_accionable=False, temporalidad=temporalidad, intencion=intencion
        ),
        naturaleza=None,
        ubicacion=None,
        creado_en=_AHORA - timedelta(minutes=minutos_desde_ahora),
    )


_REPORTES: list[ReporteEstructurado] = [
    _reporte(
        "8f3a1c02",
        4,
        "inundacion_subita",
        ["A", "G", "J"],
        "Comuna 13",
        "El Vergel",
        "cerca al puente peatonal de la calle 70",
        "ocurriendo_ahora",
        "solicita_ayuda",
        "pendiente",
        "barrio",
        "El agua ya entró hasta la sala de la casa, hay dos niños adentro y sigue subiendo.",
    ),
    _reporte(
        "2b9d77e4",
        9,
        "incendio_estructural",
        ["B", "A"],
        "Comuna 3",
        "El Peñón",
        "a media cuadra de la iglesia",
        "ocurriendo_ahora",
        "reporta_terceros",
        "pendiente",
        "exacta",
        "Se está incendiando una bodega de madera, el humo llega hasta la calle principal.",
    ),
    _reporte(
        "a410cc19",
        22,
        "movimiento_en_masa",
        ["A", "F"],
        "Comuna 1",
        "Terrón Colorado",
        "vía al mirador",
        "riesgo_previsto",
        "solicita_informacion",
        "pendiente",
        "barrio",
        "Después de la lluvia de anoche se ve una grieta grande en el talud, "
        "la gente pregunta si deben evacuar.",
    ),
    _reporte(
        "5e6712bb",
        60,
        "salud_ambiental",
        ["G", "H"],
        "Comuna 7",
        "Navarro",
        "cerca al relleno sanitario",
        "ya_ocurrio",
        "reporta_terceros",
        "revisado",
        "barrio",
        "Llevamos días con un olor muy fuerte y varios vecinos con dolor de cabeza.",
    ),
    _reporte(
        "c209ee01",
        65,
        "aglomeracion_publico",
        ["E", "G"],
        "Comuna 19",
        "San Fernando",
        "parque del barrio",
        "ocurriendo_ahora",
        "reporta_terceros",
        "pendiente",
        "exacta",
        "Hay una pelea grande cerca al parque, ya se ve gente lastimada.",
    ),
    _reporte(
        "77aab310",
        120,
        "incendio_cobertura_vegetal",
        ["B", "N"],
        "Comuna 18",
        "Meléndez",
        "ladera detrás de la universidad",
        "ocurriendo_ahora",
        "solicita_ayuda",
        "pendiente",
        "barrio",
        "Se ve fuego subiendo por la ladera, con este viento puede llegar a las casas.",
    ),
    _reporte(
        "9034fe22",
        180,
        "inundacion_lenta",
        ["J", "H", "L"],
        "Comuna 13",
        "Aguablanca",
        None,
        "ya_ocurrio",
        "reporta_terceros",
        "revisado",
        "comuna",
        "El sector lleva casi una semana con agua estancada en las calles, "
        "el mal olor ya es insoportable.",
    ),
    _reporte(
        "1145cd88",
        300,
        "sismo",
        ["A", "G", "J"],
        "Comuna 20",
        "Siloé",
        "parte alta del barrio",
        "ya_ocurrio",
        "reporta_terceros",
        "revisado",
        "barrio",
        "Se sintió fuerte el temblor de la madrugada, algunas casas de la parte alta "
        "quedaron con grietas nuevas.",
    ),
    _reporte(
        "66f0a9de",
        360,
        "incendio_estructural",
        ["B"],
        "Comuna 6",
        "Floralia",
        None,
        "ya_ocurrio",
        "solicita_informacion",
        "revisado",
        "comuna",
        "Preguntan si ya pueden regresar a la casa después del conato de incendio de anoche.",
    ),
    _reporte(
        "e02b5511",
        480,
        "inundacion_subita",
        ["A", "F"],
        "Comuna 1",
        "Vista Hermosa",
        "quebrada El Cabuyal",
        "ocurriendo_ahora",
        "solicita_ayuda",
        "pendiente",
        "barrio",
        "La quebrada se creció y ya se llevó parte de la vía, hay un carro varado.",
    ),
    _reporte(
        "d817f402",
        600,
        "movimiento_en_masa",
        ["A"],
        "Comuna 20",
        "Siloé",
        None,
        "riesgo_previsto",
        "reporta_terceros",
        "pendiente",
        "comuna",
        "Varias familias reportan que el terreno detrás de sus casas se sigue "
        "moviendo poco a poco.",
    ),
    _reporte(
        "3a9c1170",
        720,
        "salud_ambiental",
        ["H", "L"],
        "Comuna 15",
        "Distrito de Aguablanca",
        None,
        "ya_ocurrio",
        "reporta_terceros",
        "pendiente",
        "comuna",
        "El agua que llega a las casas sale con un color raro desde hace dos días.",
    ),
    _reporte(
        "bb44e903",
        840,
        "aglomeracion_publico",
        ["E"],
        "Comuna 3",
        "Centro",
        "plazoleta principal",
        "riesgo_previsto",
        "solicita_informacion",
        "revisado",
        "exacta",
        "Se está reuniendo mucha gente para la marcha de esta tarde, preguntan si hay desvíos.",
    ),
    _reporte(
        "f10ac266",
        1440,
        "incendio_cobertura_vegetal",
        ["B", "O"],
        "Comuna 18",
        "El Refugio",
        None,
        "ya_ocurrio",
        "reporta_terceros",
        "revisado",
        "comuna",
        "El fuego del cerro de ayer ya está controlado según los vecinos del sector.",
    ),
    _reporte_no_accionable(
        "e5f10a91",
        200,
        "referencia_noticia",
        "solicita_informacion",
        "revisado",
        "Vi en las noticias que hubo un temblor fuerte en otra ciudad, por acá no se sintió.",
    ),
    _reporte_no_accionable(
        "77c22b40",
        900,
        "ya_ocurrio",
        "reporta_terceros",
        "revisado",
        "Gracias a los bomberos y a los vecinos por la atención de ayer, todo salió bien.",
    ),
]


def reportes_de_ejemplo() -> list[ReporteEstructurado]:
    """Devuelve una copia de la lista de reportes de ejemplo.

    Returns:
        Una nueva lista (no comparte identidad con el estado interno del
        cliente simulado) con los reportes de ejemplo.

    """
    return list(_REPORTES)


def coincide_con_filtros(reporte: ReporteEstructurado, filtros: FiltrosReportes) -> bool:
    """Aplica los filtros de `GET /reportes` sobre un reporte, en memoria.

    Args:
        reporte: Reporte a evaluar.
        filtros: Filtros activos.

    Returns:
        True si el reporte cumple todos los filtros definidos.

    """
    naturaleza = reporte.naturaleza
    ubicacion = reporte.ubicacion

    if filtros.tipo_evento and (
        naturaleza is None or naturaleza.tipo_evento not in filtros.tipo_evento
    ):
        return False
    if filtros.servicio_de_respuesta and (
        naturaleza is None
        or not set(filtros.servicio_de_respuesta) & set(naturaleza.servicio_de_respuesta)
    ):
        return False
    if filtros.comuna and (ubicacion is None or ubicacion.comuna != filtros.comuna):
        return False
    if filtros.barrio and (ubicacion is None or ubicacion.barrio != filtros.barrio):
        return False
    if filtros.nivel_granularidad and (
        ubicacion is None or ubicacion.nivel_granularidad != filtros.nivel_granularidad
    ):
        return False
    if filtros.temporalidad and reporte.compuerta.temporalidad != filtros.temporalidad:
        return False
    if filtros.intencion and reporte.compuerta.intencion != filtros.intencion:
        return False
    if filtros.estado_revision and reporte.estado_revision != filtros.estado_revision:
        return False
    if filtros.desde and reporte.creado_en < datetime.fromisoformat(filtros.desde):
        return False
    if filtros.hasta and reporte.creado_en > datetime.fromisoformat(filtros.hasta):
        return False
    if filtros.q and filtros.q.lower() not in reporte.mensaje_anonimizado.lower():
        return False
    return True


def aplicar_correccion(
    reporte: ReporteEstructurado, correccion: dict[str, object]
) -> ReporteEstructurado:
    """Aplica una corrección parcial de triaje sobre compuerta/naturaleza/ubicación.

    Args:
        reporte: Reporte original.
        correccion: Dict plano; cada llave debe pertenecer a exactamente una
            de las secciones compuerta/naturaleza/ubicacion (ver
            `PATCH /reportes/{id}` en docs/CONTRATOS_SISTEMA.md).

    Returns:
        Una copia del reporte con la sección correspondiente actualizada.

    Raises:
        ValueError: Si alguna llave no pertenece a ninguna sección conocida.

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
            continue
        nuevo = actual.model_copy(update=cambios_seccion)
        actualizado = actualizado.model_copy(update={seccion: nuevo})

    desconocidas = set(correccion) - conocidas
    if desconocidas:
        raise ValueError(f"campos de corrección desconocidos: {sorted(desconocidas)}")
    return actualizado


def _a_resumen(reporte: ReporteEstructurado) -> ReporteResumen:
    """Proyecta un ReporteEstructurado a la forma resumida de listado.

    Args:
        reporte: Reporte completo.

    Returns:
        La versión resumida (sin mensaje ni precisión de ubicación).

    """
    return ReporteResumen(
        id=reporte.id,
        tipo_evento=reporte.naturaleza.tipo_evento if reporte.naturaleza else None,
        servicio_de_respuesta=(
            reporte.naturaleza.servicio_de_respuesta if reporte.naturaleza else []
        ),
        comuna=reporte.ubicacion.comuna if reporte.ubicacion else None,
        barrio=reporte.ubicacion.barrio if reporte.ubicacion else None,
        temporalidad=reporte.compuerta.temporalidad,
        intencion=reporte.compuerta.intencion,
        estado_revision=reporte.estado_revision,
        nivel_granularidad=reporte.ubicacion.nivel_granularidad if reporte.ubicacion else None,
        creado_en=reporte.creado_en,
    )


class ClienteReportesSimulado:
    """Implementación de `ClienteReportes` con datos de ejemplo en memoria."""

    def __init__(self, reportes: list[ReporteEstructurado] | None = None) -> None:
        """Inicializa el cliente con un dataset propio o el de ejemplo por defecto.

        Args:
            reportes: Dataset a usar; si no se da, se usan los reportes de
                ejemplo del módulo.

        """
        self._reportes: list[ReporteEstructurado] = (
            list(reportes) if reportes is not None else reportes_de_ejemplo()
        )

    def listar(self, filtros: FiltrosReportes) -> PaginaReportes:
        """Ver `ClienteReportes.listar`."""
        filtrados = [r for r in self._reportes if coincide_con_filtros(r, filtros)]
        ordenados = sorted(filtrados, key=lambda r: r.creado_en, reverse=True)
        inicio = (filtros.pagina - 1) * filtros.tamano_pagina
        pagina = ordenados[inicio : inicio + filtros.tamano_pagina]
        return PaginaReportes(
            total=len(filtrados),
            pagina=filtros.pagina,
            tamano_pagina=filtros.tamano_pagina,
            resultados=[_a_resumen(r) for r in pagina],
        )

    def obtener(self, id_reporte: str) -> ReporteEstructurado:
        """Ver `ClienteReportes.obtener`."""
        for reporte in self._reportes:
            if reporte.id == id_reporte:
                return reporte
        raise KeyError(f"reporte no encontrado: {id_reporte}")

    def actualizar(
        self, id_reporte: str, estado_revision: str, correccion: dict[str, object] | None = None
    ) -> ReporteEstructurado:
        """Ver `ClienteReportes.actualizar`."""
        original = self.obtener(id_reporte)
        actualizado = original.model_copy(update={"estado_revision": estado_revision})
        if correccion:
            actualizado = aplicar_correccion(actualizado, correccion)
        self._reportes = [actualizado if r.id == id_reporte else r for r in self._reportes]
        return actualizado

    def resumen(self, desde: str | None = None, hasta: str | None = None) -> ResumenReportes:
        """Ver `ClienteReportes.resumen`."""
        filtros = FiltrosReportes(desde=desde, hasta=hasta, tamano_pagina=len(self._reportes) or 1)
        en_rango = [r for r in self._reportes if coincide_con_filtros(r, filtros)]
        pendientes = sum(1 for r in en_rango if r.estado_revision == "pendiente")
        por_tipo: dict[str, int] = {}
        por_comuna: dict[str, int] = {}
        por_accionable = {"accionable": 0, "no_accionable": 0}
        por_temporalidad: dict[str, int] = {}
        por_intencion: dict[str, int] = {}
        por_servicio: dict[str, int] = {}
        por_granularidad: dict[str, int] = {}
        for reporte in en_rango:
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
            if reporte.naturaleza:
                clave = reporte.naturaleza.tipo_evento
                por_tipo[clave] = por_tipo.get(clave, 0) + 1
                for codigo in reporte.naturaleza.servicio_de_respuesta:
                    por_servicio[codigo] = por_servicio.get(codigo, 0) + 1
            if reporte.ubicacion:
                if reporte.ubicacion.comuna:
                    clave_comuna = reporte.ubicacion.comuna
                    por_comuna[clave_comuna] = por_comuna.get(clave_comuna, 0) + 1
                clave_granularidad = reporte.ubicacion.nivel_granularidad
                por_granularidad[clave_granularidad] = (
                    por_granularidad.get(clave_granularidad, 0) + 1
                )
        return ResumenReportes(
            total=len(en_rango),
            pendientes=pendientes,
            revisados=len(en_rango) - pendientes,
            por_tipo_evento=por_tipo,
            por_comuna=por_comuna,
            por_accionable=por_accionable,
            por_temporalidad=por_temporalidad,
            por_intencion=por_intencion,
            por_servicio_de_respuesta=por_servicio,
            por_nivel_granularidad=por_granularidad,
        )


def cliente_simulado_por_defecto() -> ClienteReportes:
    """Crea el cliente simulado usado por defecto cuando no hay BFF_URL.

    Returns:
        Un ClienteReportesSimulado con el dataset de ejemplo.

    """
    return ClienteReportesSimulado()

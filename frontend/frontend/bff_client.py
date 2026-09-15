"""Cliente hacia BFF y el contrato que las páginas del tablero consumen.

`ClienteReportes` es la interfaz real (ver `docs/CONTRATOS_SISTEMA.md`,
sección BFF): las páginas Streamlit programan contra ella, nunca contra
`BFFClient` directamente, así que pueden correr igual con datos simulados
(`frontend.reportes_mock.ClienteReportesSimulado`) mientras BFF no exponga
`/reportes`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

import httpx
from sirena_schema.schema import ReporteEstructurado


@dataclass(frozen=True)
class FiltrosReportes:
    """Filtros soportados por `GET /reportes` (ver docs/CONTRATOS_SISTEMA.md)."""

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
    tamano_pagina: int = 20

    def como_query_params(self) -> dict[str, str | int | list[str]]:
        """Convierte los filtros activos en query params para la petición HTTP.

        Returns:
            Diccionario con `pagina`/`tamano_pagina` siempre presentes, más
            solo los filtros que tienen un valor definido.

        """
        params: dict[str, str | int | list[str]] = {
            "pagina": self.pagina,
            "tamano_pagina": self.tamano_pagina,
        }
        if self.tipo_evento:
            params["tipo_evento"] = self.tipo_evento
        if self.servicio_de_respuesta:
            params["servicio_de_respuesta"] = self.servicio_de_respuesta
        campos_simples = (
            "comuna",
            "barrio",
            "temporalidad",
            "intencion",
            "estado_revision",
            "nivel_granularidad",
            "desde",
            "hasta",
            "q",
        )
        for campo in campos_simples:
            valor = getattr(self, campo)
            if valor:
                params[campo] = valor
        if self.accionable is not None:
            # Bool explícito: "if self.accionable" descartaría accionable=False.
            params["accionable"] = "true" if self.accionable else "false"
        return params


@dataclass(frozen=True)
class ReporteResumen:
    """Fila de la versión resumida de `GET /reportes`.

    Forma asumida a partir de `docs/CONTRATOS_SISTEMA.md`: incluye todo lo de
    `ReporteEstructurado` salvo `mensaje_anonimizado` y `punto_referencia`.
    `lat`/`lon` son **propuestos** (ver el contrato) — mientras el campo no
    esté confirmado, `BFFClient` los deja en `None` si BFF no los manda.

    """

    id: str
    tipo_evento: str | None
    servicio_de_respuesta: list[str]
    comuna: str | None
    barrio: str | None
    temporalidad: str
    intencion: str
    estado_revision: str
    nivel_granularidad: str | None
    creado_en: datetime
    lat: float | None = None
    lon: float | None = None


@dataclass(frozen=True)
class PaginaReportes:
    """Respuesta paginada de `GET /reportes` (versión resumida)."""

    total: int
    pagina: int
    tamano_pagina: int
    resultados: list[ReporteResumen]


@dataclass(frozen=True)
class ResumenReportes:
    """Respuesta de `GET /reportes/resumen` (ver docs/CONTRATOS_SISTEMA.md).

    `por_tipo_evento`, `por_comuna` y `por_nivel_granularidad` solo cuentan
    reportes accionables (`naturaleza`/`ubicacion` no son `None`);
    `por_temporalidad` y `por_intencion` cuentan todos, porque `compuerta`
    siempre existe. `por_servicio_de_respuesta` es multietiqueta: la suma de
    sus valores puede superar `total`.
    """

    total: int
    pendientes: int
    revisados: int
    por_tipo_evento: dict[str, int]
    por_comuna: dict[str, int]
    por_accionable: dict[str, int]
    por_temporalidad: dict[str, int]
    por_intencion: dict[str, int]
    por_servicio_de_respuesta: dict[str, int]
    por_nivel_granularidad: dict[str, int]


class ClienteReportes(Protocol):
    """Interfaz que consumen las páginas del tablero para hablar con `/reportes`."""

    def listar(self, filtros: FiltrosReportes) -> PaginaReportes:
        """Lista reportes (versión resumida) según los filtros dados."""
        ...

    def obtener(self, id_reporte: str) -> ReporteEstructurado:
        """Obtiene el reporte completo, con mensaje y ubicación detallada."""
        ...

    def actualizar(
        self, id_reporte: str, estado_revision: str, correccion: dict[str, object] | None = None
    ) -> ReporteEstructurado:
        """Aplica un PATCH de triaje (cambio de estado y/o corrección de campos)."""
        ...

    def resumen(self, desde: str | None = None, hasta: str | None = None) -> ResumenReportes:
        """Obtiene los agregados para las tarjetas de KPI del tablero."""
        ...


class ErrorBFF(RuntimeError):
    """Error de negocio devuelto por BFF (404, 422, 503, etc.)."""

    def __init__(self, status_code: int, detalle: str) -> None:
        """Guarda el código de estado HTTP y el detalle del error.

        Args:
            status_code: Código de estado HTTP devuelto por BFF.
            detalle: Cuerpo o mensaje de error asociado a la respuesta.

        """
        super().__init__(f"BFF respondió {status_code}: {detalle}")
        self.status_code = status_code
        self.detalle = detalle


def _resumen_desde_json(datos: dict[str, object]) -> ReporteResumen:
    """Construye un ReporteResumen a partir del JSON de un resultado de listado.

    Args:
        datos: Un elemento de la lista `resultados` de `GET /reportes`.

    Returns:
        El resultado tipado como ReporteResumen.

    """
    return ReporteResumen(
        id=datos["id"],
        tipo_evento=datos.get("tipo_evento"),
        servicio_de_respuesta=list(datos.get("servicio_de_respuesta", [])),
        comuna=datos.get("comuna"),
        barrio=datos.get("barrio"),
        temporalidad=datos["temporalidad"],
        intencion=datos["intencion"],
        estado_revision=datos["estado_revision"],
        nivel_granularidad=datos.get("nivel_granularidad"),
        creado_en=datetime.fromisoformat(str(datos["creado_en"]).replace("Z", "+00:00")),
        lat=datos.get("lat"),
        lon=datos.get("lon"),
    )


class BFFClient:
    """Cliente HTTP real hacia BFF; implementa `ClienteReportes`."""

    def __init__(self, base_url: str, cliente_http: httpx.Client | None = None) -> None:
        """Crea el cliente apuntando a la URL base de BFF.

        Args:
            base_url: URL base de BFF (ej. "http://bff:8000", ver `BFF_URL`
                en docker-compose.yml).
            cliente_http: Cliente httpx a reutilizar (usado en pruebas con
                `httpx.MockTransport`); si no se da, se crea uno propio.

        """
        self._http = cliente_http or httpx.Client(base_url=base_url, timeout=10.0)

    def listar(self, filtros: FiltrosReportes) -> PaginaReportes:
        """Ver `ClienteReportes.listar`."""
        respuesta = self._http.get("/reportes", params=filtros.como_query_params())
        _lanzar_si_error(respuesta)
        cuerpo = respuesta.json()
        return PaginaReportes(
            total=cuerpo["total"],
            pagina=cuerpo["pagina"],
            tamano_pagina=cuerpo["tamano_pagina"],
            resultados=[_resumen_desde_json(item) for item in cuerpo["resultados"]],
        )

    def obtener(self, id_reporte: str) -> ReporteEstructurado:
        """Ver `ClienteReportes.obtener`."""
        respuesta = self._http.get(f"/reportes/{id_reporte}")
        _lanzar_si_error(respuesta)
        return ReporteEstructurado.model_validate(respuesta.json())

    def actualizar(
        self, id_reporte: str, estado_revision: str, correccion: dict[str, object] | None = None
    ) -> ReporteEstructurado:
        """Ver `ClienteReportes.actualizar`."""
        cuerpo: dict[str, object] = {"estado_revision": estado_revision}
        if correccion:
            cuerpo["correccion"] = correccion
        respuesta = self._http.patch(f"/reportes/{id_reporte}", json=cuerpo)
        _lanzar_si_error(respuesta)
        return ReporteEstructurado.model_validate(respuesta.json())

    def resumen(self, desde: str | None = None, hasta: str | None = None) -> ResumenReportes:
        """Ver `ClienteReportes.resumen`."""
        params: dict[str, str] = {}
        if desde:
            params["desde"] = desde
        if hasta:
            params["hasta"] = hasta
        respuesta = self._http.get("/reportes/resumen", params=params)
        _lanzar_si_error(respuesta)
        cuerpo = respuesta.json()
        return ResumenReportes(
            total=cuerpo["total"],
            pendientes=cuerpo["pendientes"],
            revisados=cuerpo["revisados"],
            por_tipo_evento=dict(cuerpo.get("por_tipo_evento", {})),
            por_comuna=dict(cuerpo.get("por_comuna", {})),
            por_accionable=dict(cuerpo.get("por_accionable", {})),
            por_temporalidad=dict(cuerpo.get("por_temporalidad", {})),
            por_intencion=dict(cuerpo.get("por_intencion", {})),
            por_servicio_de_respuesta=dict(cuerpo.get("por_servicio_de_respuesta", {})),
            por_nivel_granularidad=dict(cuerpo.get("por_nivel_granularidad", {})),
        )


def _lanzar_si_error(respuesta: httpx.Response) -> None:
    """Traduce una respuesta HTTP de error de BFF en ErrorBFF.

    Args:
        respuesta: Respuesta HTTP recibida de BFF.

    Raises:
        ErrorBFF: Si el código de estado es 4xx o 5xx.

    """
    if respuesta.status_code >= 400:
        raise ErrorBFF(respuesta.status_code, respuesta.text)

"""Lógica de la pantalla Resumen, separada de `pages/2_Resumen.py`.

Mismo motivo que `frontend.bandeja`: los archivos de página de Streamlit,
con prefijo numérico, no son módulos Python importables por pytest.
"""

from __future__ import annotations

import plotly.graph_objects as go

from frontend.bff_client import ResumenReportes
from frontend.theme import (
    COLOR_ACCENT_PASTEL,
    ETIQUETA_GRANULARIDAD,
    ETIQUETA_INTENCION,
    ETIQUETA_SERVICIO,
    ETIQUETA_TEMPORALIDAD,
    ETIQUETA_TIPO_EVENTO,
)

_LAYOUT_BASE: dict[str, object] = {
    "margin": {"l": 4, "r": 24, "t": 8, "b": 4},
    "showlegend": False,
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "xaxis": {"visible": False},
    "font": {"family": "IBM Plex Sans, system-ui, sans-serif", "size": 13},
}

# Relleno translúcido del área bajo la línea de tendencia — mismo azul
# pastel que el resto de Resumen (COLOR_ACCENT_PASTEL = #7C93BF), con alfa.
_COLOR_TENDENCIA_AREA = "rgba(124,147,191,0.25)"


def calcular_tasa_revision(resumen: ResumenReportes) -> float:
    """Calcula el porcentaje de reportes revisados sobre el total.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.

    Returns:
        El porcentaje (0-100) redondeado a un decimal; 0.0 si `total` es 0.

    """
    if resumen.total == 0:
        return 0.0
    return round(resumen.revisados / resumen.total * 100, 1)


def calcular_tasa_accionable(resumen: ResumenReportes) -> float:
    """Calcula el porcentaje de reportes accionables sobre el total clasificado.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.

    Returns:
        El porcentaje (0-100) redondeado a un decimal; 0.0 si no hay reportes.

    """
    accionables = resumen.por_accionable.get("accionable", 0)
    no_accionables = resumen.por_accionable.get("no_accionable", 0)
    total = accionables + no_accionables
    if total == 0:
        return 0.0
    return round(accionables / total * 100, 1)


def _barra_horizontal(pares: list[tuple[str, int]], color: str = COLOR_ACCENT_PASTEL) -> go.Figure:
    """Arma una barra horizontal genérica, con valor directo al final de cada barra.

    Todos los gráficos de Resumen comparten el mismo color (pedido de
    diseño): no encodean identidad categórica por color, las barras ya se
    distinguen por su etiqueta en el eje.

    Args:
        pares: Lista de `(etiqueta, conteo)` en el orden en que deben quedar
            dibujadas (Plotly ubica el primer elemento abajo).
        color: Color de todas las barras.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    etiquetas = [etiqueta for etiqueta, _ in pares]
    conteos = [conteo for _, conteo in pares]
    figura = go.Figure(
        go.Bar(
            x=conteos,
            y=etiquetas,
            orientation="h",
            marker_color=color,
            text=conteos,
            textposition="outside",
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    figura.update_layout(**_LAYOUT_BASE)
    return figura


def _pares_ascendentes(conteos: dict[str, int], etiquetas: dict[str, str]) -> list[tuple[str, int]]:
    """Convierte un `dict[código, conteo]` en pares `(etiqueta, conteo)` orden ascendente.

    Orden ascendente porque Plotly dibuja barras horizontales de abajo hacia
    arriba: así la categoría con más reportes queda arriba.

    Args:
        conteos: Conteo por código (ej. `resumen.por_temporalidad`).
        etiquetas: Diccionario de etiquetas legibles por código.

    Returns:
        Pares `(etiqueta, conteo)` con conteo > 0, en orden ascendente.

    """
    items = sorted(
        ((clave, conteo) for clave, conteo in conteos.items() if conteo > 0),
        key=lambda item: item[1],
    )
    return [(etiquetas.get(clave, clave), conteo) for clave, conteo in items]


def construir_grafico_tipo_evento(resumen: ResumenReportes) -> go.Figure:
    """Arma la barra horizontal de reportes por tipo_evento.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    return _barra_horizontal(_pares_ascendentes(resumen.por_tipo_evento, ETIQUETA_TIPO_EVENTO))


def construir_grafico_comuna(resumen: ResumenReportes, top_n: int = 6) -> go.Figure:
    """Arma la barra horizontal de las comunas con más reportes.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.
        top_n: Cantidad máxima de comunas a mostrar.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    items = sorted(resumen.por_comuna.items(), key=lambda item: item[1], reverse=True)[:top_n]
    items.reverse()
    return _barra_horizontal(items)


def construir_grafico_temporalidad(resumen: ResumenReportes) -> go.Figure:
    """Arma la barra horizontal de reportes por temporalidad.

    Incluye reportes no accionables: `compuerta` siempre existe, a
    diferencia de `naturaleza`/`ubicacion`.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    return _barra_horizontal(_pares_ascendentes(resumen.por_temporalidad, ETIQUETA_TEMPORALIDAD))


def construir_grafico_intencion(resumen: ResumenReportes) -> go.Figure:
    """Arma la barra horizontal de reportes por intención.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    return _barra_horizontal(_pares_ascendentes(resumen.por_intencion, ETIQUETA_INTENCION))


def construir_grafico_servicio(resumen: ResumenReportes, top_n: int = 8) -> go.Figure:
    """Arma la barra horizontal de los servicios de respuesta más solicitados.

    `servicio_de_respuesta` es multietiqueta: un mismo reporte puede sumar a
    varios servicios, así que la suma de las barras puede superar el total.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.
        top_n: Cantidad máxima de servicios a mostrar.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    items = sorted(
        resumen.por_servicio_de_respuesta.items(), key=lambda item: item[1], reverse=True
    )[:top_n]
    items.reverse()
    pares = [(ETIQUETA_SERVICIO.get(codigo, codigo), conteo) for codigo, conteo in items]
    return _barra_horizontal(pares)


def construir_grafico_granularidad(resumen: ResumenReportes) -> go.Figure:
    """Arma la barra horizontal de reportes por nivel de granularidad geográfica.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    return _barra_horizontal(
        _pares_ascendentes(resumen.por_nivel_granularidad, ETIQUETA_GRANULARIDAD)
    )


def construir_grafico_tendencia(resumen: ResumenReportes) -> go.Figure:
    """Arma la línea de tendencia de reportes por día.

    A diferencia de las demás, esta es una serie temporal, no una
    distribución por categoría: usa línea + área en vez de barras
    horizontales, con las fechas en orden en el eje X.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    dias = sorted(resumen.por_dia)
    conteos = [resumen.por_dia[dia] for dia in dias]
    figura = go.Figure(
        go.Scatter(
            x=dias,
            y=conteos,
            mode="lines+markers+text",
            line={"color": COLOR_ACCENT_PASTEL, "width": 2},
            marker={"color": COLOR_ACCENT_PASTEL, "size": 6},
            fill="tozeroy",
            fillcolor=_COLOR_TENDENCIA_AREA,
            text=conteos,
            textposition="top center",
            hovertemplate="%{x}: %{y}<extra></extra>",
        )
    )
    figura.update_layout(
        margin={"l": 4, "r": 16, "t": 24, "b": 4},
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis={"visible": False},
        xaxis={"type": "category"},
        font={"family": "IBM Plex Sans, system-ui, sans-serif", "size": 13},
    )
    return figura

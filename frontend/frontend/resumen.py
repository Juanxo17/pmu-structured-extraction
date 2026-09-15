"""Lógica de la pantalla Resumen, separada de `pages/2_Resumen.py`.

Mismo motivo que `frontend.bandeja`: los archivos de página de Streamlit,
con prefijo numérico, no son módulos Python importables por pytest.
"""

from __future__ import annotations

import plotly.graph_objects as go

from frontend.bff_client import ResumenReportes
from frontend.theme import COLOR_ACCENT, COLOR_TIPO_EVENTO, ETIQUETA_TIPO_EVENTO

_LAYOUT_BASE: dict[str, object] = {
    "margin": {"l": 4, "r": 24, "t": 8, "b": 4},
    "showlegend": False,
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "xaxis": {"visible": False},
    "font": {"family": "IBM Plex Sans, system-ui, sans-serif", "size": 13},
}


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


def construir_grafico_tipo_evento(resumen: ResumenReportes) -> go.Figure:
    """Arma la barra horizontal de reportes por tipo_evento.

    El color de cada barra sigue a la categoría (`COLOR_TIPO_EVENTO`), no a
    su posición en el ranking — así una categoría no cambia de color cuando
    otra sube o baja de conteo.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    items = sorted(
        ((tipo, conteo) for tipo, conteo in resumen.por_tipo_evento.items() if conteo > 0),
        key=lambda item: item[1],
    )
    etiquetas = [ETIQUETA_TIPO_EVENTO.get(tipo, tipo) for tipo, _ in items]
    conteos = [conteo for _, conteo in items]
    colores = [COLOR_TIPO_EVENTO.get(tipo, "#79847E") for tipo, _ in items]

    figura = go.Figure(
        go.Bar(
            x=conteos,
            y=etiquetas,
            orientation="h",
            marker_color=colores,
            text=conteos,
            textposition="outside",
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    figura.update_layout(**_LAYOUT_BASE)
    return figura


def construir_grafico_comuna(resumen: ResumenReportes, top_n: int = 6) -> go.Figure:
    """Arma la barra horizontal de las comunas con más reportes.

    Es un ranking de magnitud, no de identidad categórica, por eso usa un
    solo hue (`COLOR_ACCENT`) en vez de la paleta categórica de tipo_evento.

    Args:
        resumen: Agregados de `GET /reportes/resumen`.
        top_n: Cantidad máxima de comunas a mostrar.

    Returns:
        Una figura de Plotly lista para `st.plotly_chart`.

    """
    items = sorted(resumen.por_comuna.items(), key=lambda item: item[1], reverse=True)[:top_n]
    items.reverse()
    etiquetas = [comuna for comuna, _ in items]
    conteos = [conteo for _, conteo in items]

    figura = go.Figure(
        go.Bar(
            x=conteos,
            y=etiquetas,
            orientation="h",
            marker_color=COLOR_ACCENT,
            text=conteos,
            textposition="outside",
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    figura.update_layout(**_LAYOUT_BASE)
    return figura

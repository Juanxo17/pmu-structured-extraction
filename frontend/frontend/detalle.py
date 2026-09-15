"""Lógica de la pantalla Detalle, separada de `pages/3_Detalle.py`.

Mismo motivo que `frontend.bandeja`/`frontend.resumen`: los archivos de
página de Streamlit, con prefijo numérico, no son módulos Python
importables por pytest.
"""

from __future__ import annotations

import folium


def construir_correccion(
    tipo_evento: str | None,
    temporalidad: str | None,
    intencion: str | None,
    comuna: str | None,
) -> dict[str, str]:
    """Arma el dict de `correccion` para `PATCH /reportes/{id}` con los campos definidos.

    Mismas llaves que espera `aplicar_correccion` en `reportes_mock.py`
    (`tipo_evento` → naturaleza, `temporalidad`/`intencion` → compuerta,
    `comuna` → ubicación — ver docs/CONTRATOS_SISTEMA.md).

    Args:
        tipo_evento: Corrección de `naturaleza.tipo_evento`, o None si no cambió.
        temporalidad: Corrección de `compuerta.temporalidad`, o None si no cambió.
        intencion: Corrección de `compuerta.intencion`, o None si no cambió.
        comuna: Corrección de `ubicacion.comuna`, o None si no cambió.

    Returns:
        Un dict solo con los campos que sí tienen valor.

    """
    valores = {
        "tipo_evento": tipo_evento,
        "temporalidad": temporalidad,
        "intencion": intencion,
        "comuna": comuna,
    }
    return {campo: valor for campo, valor in valores.items() if valor}


def construir_mapa_punto(punto: tuple[float, float], color: str, etiqueta: str) -> folium.Map:
    """Arma un mapa con un único marcador, para el detalle de un reporte.

    Args:
        punto: Coordenada `(lat, lon)` a marcar.
        color: Color del marcador (mismo criterio que `bandeja.construir_mapa`).
        etiqueta: Texto del tooltip del marcador.

    Returns:
        Un `folium.Map` centrado en el punto, con un único `CircleMarker`.

    """
    mapa = folium.Map(location=punto, zoom_start=14, tiles="OpenStreetMap")
    folium.CircleMarker(
        location=punto,
        radius=8,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        tooltip=etiqueta,
    ).add_to(mapa)
    return mapa

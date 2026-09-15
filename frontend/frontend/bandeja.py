"""Lógica de la pantalla Bandeja, separada de `pages/1_Bandeja.py`.

Se separa para poder probarla con pytest normal: los archivos de página de
Streamlit, con prefijo numérico, no son módulos Python importables.
"""

from __future__ import annotations

import os
from typing import Any

import folium
import pandas as pd
from st_aggrid import GridOptionsBuilder

from frontend.bff_client import BFFClient, ClienteReportes, ReporteResumen
from frontend.comunas import centroide
from frontend.reportes_mock import ClienteReportesSimulado
from frontend.theme import (
    COLOR_MUTED,
    COLOR_TIPO_EVENTO,
    ETIQUETA_ESTADO,
    ETIQUETA_INTENCION,
    ETIQUETA_SERVICIO,
    ETIQUETA_TEMPORALIDAD,
    ETIQUETA_TIPO_EVENTO,
    ICONO_ESTADO,
    ICONO_TIPO_EVENTO,
)

_CENTRO_CALI = (3.4516, -76.5320)


def usa_datos_de_ejemplo() -> bool:
    """Indica si el tablero está corriendo contra datos de ejemplo en vez de BFF real.

    Returns:
        True si la variable de entorno `BFF_URL` no está definida.

    """
    return not os.environ.get("BFF_URL")


def elegir_cliente() -> ClienteReportes:
    """Elige el cliente real o simulado según la variable de entorno `BFF_URL`.

    Returns:
        `BFFClient` si `BFF_URL` está definida (ver docker-compose.yml);
        `ClienteReportesSimulado` con datos de ejemplo en cualquier otro caso,
        para poder desarrollar sin que BFF exista todavía.

    """
    if usa_datos_de_ejemplo():
        return ClienteReportesSimulado()
    return BFFClient(base_url=os.environ["BFF_URL"])


def construir_filas_grid(resultados: list[ReporteResumen]) -> list[dict[str, Any]]:
    """Convierte resultados resumidos en filas listas para mostrar en la tabla.

    Args:
        resultados: Resultados de `ClienteReportes.listar`.

    Returns:
        Una lista de dicts con etiquetas y colores ya resueltos, para que la
        tabla no tenga que conocer la ontología ni la paleta.

    """
    filas = []
    for r in resultados:
        icono_estado = ICONO_ESTADO.get(r.estado_revision, "⚪")
        etiqueta_estado = ETIQUETA_ESTADO.get(r.estado_revision, r.estado_revision)
        icono_tipo = ICONO_TIPO_EVENTO.get(r.tipo_evento or "", "⚪")
        etiqueta_tipo = ETIQUETA_TIPO_EVENTO.get(r.tipo_evento or "", "—")
        filas.append(
            {
                "id": r.id,
                "estado_revision": r.estado_revision,
                "estado_label": f"{icono_estado} {etiqueta_estado}",
                "tipo_evento_label": f"{icono_tipo} {etiqueta_tipo}",
                "servicios": ", ".join(
                    ETIQUETA_SERVICIO.get(codigo, codigo) for codigo in r.servicio_de_respuesta
                ),
                "ubicacion": f"{r.comuna or '—'} · {r.barrio or '—'}",
                "intencion": ETIQUETA_INTENCION.get(r.intencion, r.intencion),
                "temporalidad": ETIQUETA_TEMPORALIDAD.get(r.temporalidad, r.temporalidad),
                "recibido": r.creado_en,
            }
        )
    return filas


def construir_filas_exportacion(resultados: list[ReporteResumen]) -> list[dict[str, Any]]:
    """Convierte resultados resumidos en filas para exportar (sin emoji).

    A diferencia de `construir_filas_grid`, estas filas son para abrirse en
    Excel/hojas de cálculo, no para pintarse en pantalla: usan nombres
    legibles completos pero sin el ícono decorativo.

    Args:
        resultados: Resultados de `ClienteReportes.listar`.

    Returns:
        Una lista de dicts lista para convertir a `pandas.DataFrame`.

    """
    filas = []
    for r in resultados:
        filas.append(
            {
                "id": r.id,
                "estado": ETIQUETA_ESTADO.get(r.estado_revision, r.estado_revision),
                "tipo_evento": ETIQUETA_TIPO_EVENTO.get(r.tipo_evento or "", "—"),
                "servicios": ", ".join(
                    ETIQUETA_SERVICIO.get(codigo, codigo) for codigo in r.servicio_de_respuesta
                ),
                "comuna": r.comuna or "—",
                "barrio": r.barrio or "—",
                "temporalidad": ETIQUETA_TEMPORALIDAD.get(r.temporalidad, r.temporalidad),
                "intencion": ETIQUETA_INTENCION.get(r.intencion, r.intencion),
                "recibido": r.creado_en.isoformat(),
            }
        )
    return filas


def exportar_csv(resultados: list[ReporteResumen]) -> bytes:
    """Serializa los resultados de la Bandeja como CSV, listo para descargar.

    Args:
        resultados: Resultados de `ClienteReportes.listar`.

    Returns:
        El CSV en bytes, con BOM UTF-8 para que Excel muestre bien las tildes.

    """
    filas = pd.DataFrame(construir_filas_exportacion(resultados))
    return filas.to_csv(index=False).encode("utf-8-sig")


def construir_grid_options(filas: pd.DataFrame) -> dict[str, Any]:
    """Arma las gridOptions de AgGrid: columnas, orden por defecto y selección de fila.

    Args:
        filas: DataFrame construido a partir de `construir_filas_grid`.

    Returns:
        El diccionario de gridOptions listo para pasarle a `AgGrid`.

    """
    constructor = GridOptionsBuilder.from_dataframe(filas)
    constructor.configure_default_column(sortable=True, filter=False, resizable=True)
    constructor.configure_selection(selection_mode="single", use_checkbox=False)
    constructor.configure_column("id", hide=True)
    constructor.configure_column("estado_revision", hide=True)
    constructor.configure_column("estado_label", header_name="Estado")
    constructor.configure_column("tipo_evento_label", header_name="Tipo de evento")
    constructor.configure_column("servicios", header_name="Servicios")
    constructor.configure_column("ubicacion", header_name="Ubicación")
    constructor.configure_column("intencion", header_name="Intención")
    constructor.configure_column("temporalidad", header_name="Temporalidad")
    constructor.configure_column(
        "recibido", header_name="Recibido", sort="desc", type=["dateColumnFilter"]
    )
    opciones = constructor.build()
    opciones["autoSizeStrategy"] = {"type": "fitGridWidth"}
    return opciones


def ubicar_en_mapa(reporte: ReporteResumen) -> tuple[float, float] | None:
    """Resuelve dónde plantar el punto de un reporte en el mapa.

    Usa la coordenada exacta (`lat`/`lon`, propuesta — ver
    docs/CONTRATOS_SISTEMA.md) cuando BFF ya la manda; si no, cae al
    centroide local de la comuna (ver `frontend.comunas`), la misma
    aproximación que se usaba mientras el campo no existía.

    Args:
        reporte: Resultado de `ClienteReportes.listar`.

    Returns:
        Una tupla `(lat, lon)`, o `None` si no hay forma de ubicar el reporte
        (sin coordenada exacta y sin comuna conocida).

    """
    if reporte.lat is not None and reporte.lon is not None:
        return (reporte.lat, reporte.lon)
    return centroide(reporte.comuna)


def construir_mapa(resultados: list[ReporteResumen]) -> folium.Map:
    """Arma el mapa de la Bandeja con un punto por resultado ubicable.

    Args:
        resultados: Resultados de `ClienteReportes.listar`.

    Returns:
        Un `folium.Map` centrado en Cali con los marcadores agregados.

    """
    mapa = folium.Map(location=_CENTRO_CALI, zoom_start=12, tiles="OpenStreetMap")
    for r in resultados:
        es_exacta = r.lat is not None and r.lon is not None
        punto = ubicar_en_mapa(r)
        if punto is None:
            continue
        color = COLOR_TIPO_EVENTO.get(r.tipo_evento or "", COLOR_MUTED)
        etiqueta = ETIQUETA_TIPO_EVENTO.get(r.tipo_evento or "", r.tipo_evento or "—")
        precision = "ubicación exacta" if es_exacta else "ubicación aproximada por comuna"
        folium.CircleMarker(
            location=punto,
            radius=7 if es_exacta else 6,
            color=color,
            weight=1 if r.estado_revision == "pendiente" else 2,
            dash_array="4,3" if r.estado_revision == "pendiente" else None,
            fill=True,
            fill_color=color,
            fill_opacity=0.9 if es_exacta else 0.6,
            tooltip=r.id,
            popup=folium.Popup(
                f"<b>{etiqueta}</b><br>{r.comuna or '—'} · {r.barrio or '—'}"
                f"<br><small>{precision}</small>",
                max_width=220,
            ),
        ).add_to(mapa)
    return mapa


def fila_seleccionada_de(grid_response: Any) -> dict[str, Any] | None:
    """Extrae la primera fila seleccionada de la respuesta de `AgGrid`.

    Acepta tanto la forma antigua (dict con `selected_rows` como lista) como
    la forma más reciente (`selected_rows` como DataFrame), sin acoplar el
    resto del código a un formato específico de `streamlit-aggrid`.

    Args:
        grid_response: Valor devuelto por `AgGrid(...)`.

    Returns:
        La primera fila seleccionada como dict, o None si no hay selección.

    """
    seleccionadas = getattr(grid_response, "selected_rows", None)
    if seleccionadas is None and isinstance(grid_response, dict):
        seleccionadas = grid_response.get("selected_rows")

    if seleccionadas is None:
        return None
    if hasattr(seleccionadas, "to_dict"):
        registros = seleccionadas.to_dict("records")
        return registros[0] if registros else None
    if isinstance(seleccionadas, list) and seleccionadas:
        return seleccionadas[0]
    return None

"""Lógica de la pantalla Bandeja, separada de `pages/1_Bandeja.py`.

Se separa para poder probarla con pytest normal: los archivos de página de
Streamlit, con prefijo numérico, no son módulos Python importables.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import folium
import pandas as pd
from st_aggrid import GridOptionsBuilder

from frontend.bff_client import ClienteReportes, FiltrosReportes, ReporteResumen
from frontend.comunas import ubicar_en_mapa
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

# Tope de páginas al traer "todo lo filtrado" (listar_todo) — protección
# contra un filtro roto que devuelva un total absurdo y dispare cientos de
# peticiones; con tamano_pagina=100 (el máximo del contrato) esto cubre
# hasta 10.000 reportes, muy por encima de cualquier filtro real.
_TOPE_PAGINAS_LISTAR_TODO = 100


def calcular_total_paginas(total: int, tamano_pagina: int) -> int:
    """Calcula cuántas páginas hacen falta para cubrir `total` resultados.

    Args:
        total: Cantidad de resultados que cumplen el filtro.
        tamano_pagina: Tamaño de página en uso.

    Returns:
        El total de páginas, mínimo 1 (para no mostrar "página 1 de 0"
        cuando no hay resultados).

    """
    if total <= 0 or tamano_pagina <= 0:
        return 1
    return -(-total // tamano_pagina)  # división entera hacia arriba


def listar_todo(
    cliente: ClienteReportes, filtros: FiltrosReportes, tamano_pagina: int = 100
) -> list[ReporteResumen]:
    """Trae todos los resultados que cumplen un filtro, sin importar la paginación.

    Usado por `exportar_csv`: el CSV debe cubrir todo lo filtrado, no solo la
    página que el operador tiene visible en la tabla.

    Args:
        cliente: Cliente de reportes en uso.
        filtros: Filtros activos (se ignoran `filtros.pagina`/`tamano_pagina`).
        tamano_pagina: Tamaño de página a usar en cada petición (el máximo
            que admite el contrato es 100).

    Returns:
        Todos los resultados que cumplen el filtro, en el orden en que los
        devuelve el cliente.

    """
    resultados: list[ReporteResumen] = []
    pagina_actual = 1
    while pagina_actual <= _TOPE_PAGINAS_LISTAR_TODO:
        pagina = cliente.listar(replace(filtros, pagina=pagina_actual, tamano_pagina=tamano_pagina))
        resultados.extend(pagina.resultados)
        if len(resultados) >= pagina.total or not pagina.resultados:
            break
        pagina_actual += 1
    return resultados


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
        punto = ubicar_en_mapa(r.lat, r.lon, r.comuna)
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

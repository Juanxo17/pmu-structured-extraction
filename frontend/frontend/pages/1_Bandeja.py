"""Bandeja de reportes: tabla filtrable + mapa, primera pantalla del tablero.

Toda la lógica de transformación vive en `frontend.bandeja` para poder
probarla con pytest normal; este archivo solo arma los widgets y llama a
esas funciones (los archivos de página de Streamlit no son módulos Python
importables por el prefijo numérico).
"""

import pandas as pd
import streamlit as st
from sirena_schema.ontologia import ONTOLOGIA
from st_aggrid import AgGrid
from streamlit_folium import st_folium

from frontend.bandeja import (
    construir_filas_grid,
    construir_grid_options,
    construir_mapa,
    elegir_cliente,
    fila_seleccionada_de,
)
from frontend.bff_client import ErrorBFF, FiltrosReportes
from frontend.comunas import COMUNAS_CONOCIDAS
from frontend.theme import ETIQUETA_TIPO_EVENTO, inyectar_tema


def _leer_filtros() -> FiltrosReportes:
    """Renderiza la barra de filtros y arma los `FiltrosReportes` resultantes.

    Returns:
        Los filtros según lo que el operador haya seleccionado.

    """
    col_tipo, col_comuna, col_estado = st.columns(3)
    with col_tipo:
        tipos = st.multiselect(
            "Tipo de evento",
            options=sorted(ONTOLOGIA.tipos_evento),
            format_func=lambda t: ETIQUETA_TIPO_EVENTO.get(t, t),
        )
    with col_comuna:
        comuna = st.selectbox("Comuna", options=["Todas", *COMUNAS_CONOCIDAS])
    with col_estado:
        estado = st.segmented_control(
            "Estado", options=["Todos", "Pendientes", "Revisados"], default="Todos"
        )

    col_desde, col_hasta, col_q = st.columns([1, 1, 2])
    with col_desde:
        fecha_desde = st.date_input("Desde", value=None)
    with col_hasta:
        fecha_hasta = st.date_input("Hasta", value=None)
    with col_q:
        q = st.text_input("Buscar", placeholder="texto del mensaje…")

    estado_revision = {"Pendientes": "pendiente", "Revisados": "revisado"}.get(estado)
    return FiltrosReportes(
        tipo_evento=tipos,
        comuna=None if comuna == "Todas" else comuna,
        estado_revision=estado_revision,
        desde=fecha_desde.isoformat() if fecha_desde else None,
        hasta=fecha_hasta.isoformat() if fecha_hasta else None,
        q=q or None,
        tamano_pagina=50,
    )


def _mostrar_kpis(cliente) -> None:
    """Muestra las tarjetas de KPI usando `GET /reportes/resumen`, sin filtrar.

    Van antes de la barra de filtros a propósito: son el histórico completo y
    no cambian con lo que el operador filtre en la tabla de abajo.

    Args:
        cliente: Cliente de reportes en uso (real o simulado).

    """
    resumen = cliente.resumen()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", resumen.total)
    col2.metric("Pendientes", resumen.pendientes)
    col3.metric("Revisados", resumen.revisados)


def _mostrar_vista_previa(cliente, id_reporte: str) -> None:
    """Muestra un resumen del reporte seleccionado en la tabla.

    Llama a `ClienteReportes.obtener` porque el listado resumido no trae el
    mensaje ni la ubicación completa. La pantalla de Detalle (con el
    formulario de triaje completo) queda para la siguiente iteración.

    Args:
        cliente: Cliente de reportes en uso.
        id_reporte: Id del reporte seleccionado en la tabla.

    """
    try:
        reporte = cliente.obtener(id_reporte)
    except (KeyError, ErrorBFF) as error:
        st.warning(f"No se pudo cargar el detalle de {id_reporte}: {error}")
        return

    with st.expander(f"Vista previa · {reporte.id}", expanded=True):
        if reporte.naturaleza:
            st.write(f"**Tipo de evento:** {reporte.naturaleza.tipo_evento}")
            st.write(f"**Servicios:** {', '.join(reporte.naturaleza.servicio_de_respuesta)}")
        if reporte.ubicacion:
            st.write(
                f"**Ubicación:** {reporte.ubicacion.comuna or '—'} · "
                f"{reporte.ubicacion.barrio or '—'}"
            )
        st.write(f"**Mensaje:** {reporte.mensaje_anonimizado}")
        st.caption("Formulario de triaje completo: próxima iteración (pantalla Detalle).")


def main() -> None:
    """Renderiza la pantalla completa de la Bandeja."""
    inyectar_tema()
    st.title("Bandeja de reportes")

    cliente = elegir_cliente()
    _mostrar_kpis(cliente)
    filtros = _leer_filtros()

    try:
        pagina = cliente.listar(filtros)
    except ErrorBFF as error:
        st.error(f"BFF respondió con un error: {error}")
        return

    if not pagina.resultados:
        st.info("No hay reportes con estos filtros.")
        return

    col_tabla, col_mapa = st.columns([1.5, 1])
    with col_tabla:
        filas = pd.DataFrame(construir_filas_grid(pagina.resultados))
        grid_options = construir_grid_options(filas)
        respuesta_grid = AgGrid(
            filas,
            gridOptions=grid_options,
            height=420,
            theme="alpine",
        )
        fila = fila_seleccionada_de(respuesta_grid)
        if fila:
            _mostrar_vista_previa(cliente, fila["id"])

    with col_mapa:
        st.caption(
            "⚠ Mapa con centroides por comuna (mock local) — "
            "lat/lon en el listado resumido es un campo propuesto, "
            "pendiente de confirmar con CRUD."
        )
        st_folium(construir_mapa(pagina.resultados), width=None, height=420)


if __name__ == "__main__":
    main()

"""Bandeja de reportes: tabla filtrable + mapa, primera pantalla del tablero.

Toda la lógica de transformación vive en `frontend.bandeja` para poder
probarla con pytest normal; este archivo solo arma los widgets y llama a
esas funciones (los archivos de página de Streamlit no son módulos Python
importables por el prefijo numérico).
"""

from dataclasses import replace

import pandas as pd
import streamlit as st
from sirena_schema.ontologia import ONTOLOGIA
from st_aggrid import AgGrid
from streamlit_folium import st_folium

from frontend.bandeja import (
    calcular_total_paginas,
    construir_filas_grid,
    construir_grid_options,
    construir_mapa,
    exportar_csv,
    fila_seleccionada_de,
    listar_todo,
)
from frontend.bff_client import ErrorBFF, FiltrosReportes
from frontend.cliente import cliente_de_sesion, usa_datos_de_ejemplo
from frontend.comunas import COMUNAS_CONOCIDAS
from frontend.theme import (
    ETIQUETA_SERVICIO,
    ETIQUETA_TIPO_EVENTO,
    inyectar_tema,
    mostrar_metrica,
    renderizar_pie_sidebar,
)

_TAMANO_PAGINA = 50


def _leer_filtros() -> FiltrosReportes:
    """Renderiza la barra de filtros (con contorno) y arma los `FiltrosReportes`.

    Returns:
        Los filtros según lo que el operador haya seleccionado.

    """
    with st.container(border=True):
        col_tipo, col_comuna = st.columns(2)
        with col_tipo:
            tipos = st.multiselect(
                "Tipo de evento",
                options=sorted(ONTOLOGIA.tipos_evento),
                format_func=lambda t: ETIQUETA_TIPO_EVENTO.get(t, t),
            )
        with col_comuna:
            comuna = st.selectbox("Comuna", options=["Todas", *COMUNAS_CONOCIDAS])

        col_estado, col_accionable = st.columns(2)
        with col_estado:
            estado = st.segmented_control(
                "Estado", options=["Todos", "Pendientes", "Revisados"], default="Todos"
            )
        with col_accionable:
            accionable = st.segmented_control(
                "Accionable",
                options=["Todos", "Accionables", "No accionables"],
                default="Todos",
            )

        col_desde, col_hasta, col_q = st.columns([1, 1, 2])
        with col_desde:
            fecha_desde = st.date_input("Desde", value=None)
        with col_hasta:
            fecha_hasta = st.date_input("Hasta", value=None)
        with col_q:
            q = st.text_input("Buscar", placeholder="texto del mensaje…")

    estado_revision = {"Pendientes": "pendiente", "Revisados": "revisado"}.get(estado)
    es_accionable = {"Accionables": True, "No accionables": False}.get(accionable)
    return FiltrosReportes(
        tipo_evento=tipos,
        comuna=None if comuna == "Todas" else comuna,
        estado_revision=estado_revision,
        accionable=es_accionable,
        desde=fecha_desde.isoformat() if fecha_desde else None,
        hasta=fecha_hasta.isoformat() if fecha_hasta else None,
        q=q or None,
        tamano_pagina=_TAMANO_PAGINA,
    )


def _leer_pagina_actual(filtros_sin_pagina: FiltrosReportes) -> int:
    """Lee la página actual de `session_state`, reseteándola a 1 si cambió el filtro.

    Args:
        filtros_sin_pagina: Filtros leídos del panel (siempre con `pagina=1`,
            el valor por defecto de `_leer_filtros`), usados solo para
            detectar si el operador cambió algún filtro desde el último rerun.

    Returns:
        El número de página a pedir.

    """
    if st.session_state.get("bandeja_filtros_previos") != filtros_sin_pagina:
        st.session_state["bandeja_pagina"] = 1
    st.session_state["bandeja_filtros_previos"] = filtros_sin_pagina
    return st.session_state.get("bandeja_pagina", 1)


def _mostrar_paginador(pagina_actual: int, total: int) -> None:
    """Muestra los controles de Anterior/Siguiente y la posición actual.

    Args:
        pagina_actual: Página que se está mostrando.
        total: Total de reportes que cumplen el filtro (no solo la página).

    """
    total_paginas = calcular_total_paginas(total, _TAMANO_PAGINA)
    col_anterior, col_info, col_siguiente = st.columns([1, 2, 1])
    with col_anterior:
        if st.button("← Anterior", disabled=pagina_actual <= 1, key="bandeja_pagina_anterior"):
            st.session_state["bandeja_pagina"] = pagina_actual - 1
            st.rerun()
    with col_info:
        st.markdown(
            f"<p style='text-align:center'>Página {pagina_actual} de {total_paginas} "
            f"· {total} reportes en total</p>",
            unsafe_allow_html=True,
        )
    with col_siguiente:
        if st.button(
            "Siguiente →", disabled=pagina_actual >= total_paginas, key="bandeja_pagina_siguiente"
        ):
            st.session_state["bandeja_pagina"] = pagina_actual + 1
            st.rerun()


def _mostrar_kpis(cliente) -> None:
    """Muestra las tarjetas de KPI usando `GET /reportes/resumen`, sin filtrar.

    Van antes de la barra de filtros a propósito: son el histórico completo y
    no cambian con lo que el operador filtre en la tabla de abajo.

    Args:
        cliente: Cliente de reportes en uso (real o simulado).

    """
    resumen = cliente.resumen()
    col1, col2, col3 = st.columns(3)
    mostrar_metrica(col1, "Total", resumen.total)
    mostrar_metrica(col2, "Pendientes", resumen.pendientes)
    mostrar_metrica(col3, "Revisados", resumen.revisados)


def _mostrar_vista_previa(cliente, id_reporte: str) -> None:
    """Muestra un resumen del reporte seleccionado en la tabla.

    Llama a `ClienteReportes.obtener` porque el listado resumido no trae el
    mensaje ni la ubicación completa. El botón "Ver detalle completo" lleva
    a la pantalla de Detalle, con el formulario de triaje.

    Args:
        cliente: Cliente de reportes en uso.
        id_reporte: Id del reporte seleccionado en la tabla.

    """
    try:
        reporte = cliente.obtener(id_reporte)
    except (KeyError, ErrorBFF):
        st.warning("No se pudo cargar el detalle de este reporte. Intenta de nuevo.")
        return

    with st.expander("Vista previa del reporte", expanded=True):
        if reporte.naturaleza:
            tipo = ETIQUETA_TIPO_EVENTO.get(reporte.naturaleza.tipo_evento, "—")
            st.write(f"**Tipo de evento:** {tipo}")
            servicios = ", ".join(
                ETIQUETA_SERVICIO.get(codigo, codigo)
                for codigo in reporte.naturaleza.servicio_de_respuesta
            )
            st.write(f"**Servicios:** {servicios}")
        if reporte.ubicacion:
            st.write(
                f"**Ubicación:** {reporte.ubicacion.comuna or '—'} · "
                f"{reporte.ubicacion.barrio or '—'}"
            )
        st.write(f"**Mensaje:** {reporte.mensaje_anonimizado}")
        if st.button("Ver detalle completo →", key=f"detalle_{reporte.id}"):
            st.session_state["reporte_seleccionado_id"] = reporte.id
            st.switch_page("pages/3_Detalle.py")


def main() -> None:
    """Renderiza la pantalla completa de la Bandeja."""
    inyectar_tema()
    renderizar_pie_sidebar(modo_demo=usa_datos_de_ejemplo())
    # Reserva el lugar del encabezado arriba de todo; se llena más abajo, una
    # vez que ya hay resultados con los que armar el botón de exportar.
    encabezado = st.container()

    cliente = cliente_de_sesion()
    _mostrar_kpis(cliente)
    filtros_sin_pagina = _leer_filtros()
    pagina_actual = _leer_pagina_actual(filtros_sin_pagina)
    filtros = replace(filtros_sin_pagina, pagina=pagina_actual)

    try:
        pagina = cliente.listar(filtros)
    except ErrorBFF:
        with encabezado:
            st.title("Bandeja de reportes")
        st.error("No se pudieron cargar los reportes en este momento. Intenta de nuevo más tarde.")
        return

    with encabezado:
        col_titulo, col_exportar = st.columns([3, 1])
        col_titulo.title("Bandeja de reportes")
        # Trae *todo* lo filtrado (no solo esta página) para que el CSV
        # coincida con el conteo del filtro, no con lo visible en pantalla.
        # Esto pide todas las páginas en cada rerun — aceptable para un botón
        # de exportar, que no se acciona en cada interacción del operador.
        col_exportar.download_button(
            "Exportar CSV",
            data=exportar_csv(listar_todo(cliente, filtros_sin_pagina)),
            file_name="reportes_sirena.csv",
            mime="text/csv",
        )

    if not pagina.resultados:
        st.info("No hay reportes con estos filtros.")
        return

    col_tabla, col_previa = st.columns([1.5, 1])
    with col_tabla:
        filas = pd.DataFrame(construir_filas_grid(pagina.resultados))
        grid_options = construir_grid_options(filas)
        respuesta_grid = AgGrid(
            filas,
            gridOptions=grid_options,
            height=420,
        )
        fila = fila_seleccionada_de(respuesta_grid)

    _mostrar_paginador(pagina_actual, pagina.total)

    with col_previa:
        if fila:
            _mostrar_vista_previa(cliente, fila["id"])
        else:
            st.caption("Selecciona un reporte en la tabla para ver su vista previa.")

    st.caption("Ubicación exacta cuando está disponible; si no, aproximada por comuna.")
    st_folium(construir_mapa(pagina.resultados), width=None, height=420)


if __name__ == "__main__":
    main()

"""Detalle de un reporte: formulario de triaje completo, tercera pantalla del tablero.

Toda la lógica vive en `frontend.detalle` para poder probarla con pytest
normal (ver `frontend/frontend/pages/1_Bandeja.py` para el mismo patrón).
"""

import streamlit as st
from streamlit_folium import st_folium

from frontend.cliente import cliente_de_sesion, usa_datos_de_ejemplo
from frontend.bff_client import ErrorBFF
from frontend.comunas import ubicar_en_mapa
from frontend.detalle import construir_correccion, construir_mapa_punto
from frontend.theme import (
    COLOR_ESTADO,
    COLOR_ESTADO_FONDO,
    COLOR_TIPO_EVENTO,
    ETIQUETA_ESTADO,
    ETIQUETA_INTENCION,
    ETIQUETA_SERVICIO,
    ETIQUETA_TEMPORALIDAD,
    ETIQUETA_TIPO_EVENTO,
    inyectar_tema,
    renderizar_pie_sidebar,
)

_VOLVER_A_LA_BANDEJA = "pages/1_Bandeja.py"


def _volver_a_la_bandeja() -> None:
    """Muestra el enlace de regreso a la Bandeja."""
    st.page_link(_VOLVER_A_LA_BANDEJA, label="← Volver a la bandeja", icon="📥")


def _mostrar_encabezado(reporte) -> None:
    """Muestra el id, la píldora de estado y los chips de temporalidad/intención.

    Args:
        reporte: Reporte completo obtenido de `ClienteReportes.obtener`.

    """
    color = COLOR_ESTADO.get(reporte.estado_revision, "#4B5652")
    fondo = COLOR_ESTADO_FONDO.get(reporte.estado_revision, "#EFF3EE")
    etiqueta_estado = ETIQUETA_ESTADO.get(reporte.estado_revision, reporte.estado_revision)
    temporalidad = ETIQUETA_TEMPORALIDAD.get(
        reporte.compuerta.temporalidad, reporte.compuerta.temporalidad
    )
    intencion = ETIQUETA_INTENCION.get(reporte.compuerta.intencion, reporte.compuerta.intencion)
    st.markdown(
        f"`{reporte.id}` &nbsp; "
        f'<span class="sirena-estado-pill" style="background:{fondo};color:{color}">'
        f"{etiqueta_estado}</span> &nbsp; {temporalidad} · {intencion}",
        unsafe_allow_html=True,
    )


def _mostrar_naturaleza_y_ubicacion(reporte) -> None:
    """Muestra las cards de Naturaleza y Ubicación, cuando el reporte es accionable.

    Args:
        reporte: Reporte completo obtenido de `ClienteReportes.obtener`.

    """
    if reporte.naturaleza:
        with st.container(border=True):
            st.subheader("Naturaleza")
            tipo = ETIQUETA_TIPO_EVENTO.get(reporte.naturaleza.tipo_evento, "—")
            st.write(f"**Tipo de evento:** {tipo}")
            servicios = ", ".join(
                ETIQUETA_SERVICIO.get(codigo, codigo)
                for codigo in reporte.naturaleza.servicio_de_respuesta
            )
            st.write(f"**Servicios de respuesta:** {servicios or '—'}")

    if reporte.ubicacion:
        with st.container(border=True):
            st.subheader("Ubicación")
            st.write(f"**Texto literal:** {reporte.ubicacion.ubicacion_texto_literal}")
            st.write(f"**Comuna:** {reporte.ubicacion.comuna or '—'}")
            st.write(f"**Barrio:** {reporte.ubicacion.barrio or '—'}")
            st.write(f"**Punto de referencia:** {reporte.ubicacion.punto_referencia or '—'}")
            st.write(f"**Granularidad:** {reporte.ubicacion.nivel_granularidad}")

            punto = ubicar_en_mapa(
                reporte.ubicacion.lat, reporte.ubicacion.lon, reporte.ubicacion.comuna
            )
            if punto is not None:
                tipo = reporte.naturaleza.tipo_evento if reporte.naturaleza else None
                color = COLOR_TIPO_EVENTO.get(tipo, "#79847E")
                etiqueta = ETIQUETA_TIPO_EVENTO.get(tipo, reporte.id)
                st_folium(construir_mapa_punto(punto, color, etiqueta), width=None, height=260)


def _mostrar_mensaje(reporte) -> None:
    """Muestra el mensaje anonimizado como cita.

    Args:
        reporte: Reporte completo obtenido de `ClienteReportes.obtener`.

    """
    with st.container(border=True):
        st.subheader("Mensaje")
        st.markdown(f"> {reporte.mensaje_anonimizado}")


def _mostrar_triaje(cliente, reporte) -> None:
    """Muestra los controles de triaje: marcar revisado y corregir campos.

    Args:
        cliente: Cliente de reportes en uso.
        reporte: Reporte completo obtenido de `ClienteReportes.obtener`.

    """
    with st.container(border=True):
        st.subheader("Triaje")

        nuevo_estado = "revisado" if reporte.estado_revision == "pendiente" else "pendiente"
        etiqueta_boton = (
            "Marcar como revisado"
            if reporte.estado_revision == "pendiente"
            else "Marcar como pendiente"
        )
        if st.button(etiqueta_boton, type="primary"):
            cliente.actualizar(reporte.id, estado_revision=nuevo_estado)
            st.success("Estado actualizado.")
            st.rerun()

        st.divider()

        with st.form("form_correccion"):
            corr_tipo = None
            if reporte.naturaleza:
                corr_tipo = st.selectbox(
                    "Corregir tipo de evento",
                    options=list(ETIQUETA_TIPO_EVENTO),
                    index=list(ETIQUETA_TIPO_EVENTO).index(reporte.naturaleza.tipo_evento),
                    format_func=lambda t: ETIQUETA_TIPO_EVENTO.get(t, t),
                )

            corr_temporalidad = st.selectbox(
                "Corregir temporalidad",
                options=list(ETIQUETA_TEMPORALIDAD),
                index=list(ETIQUETA_TEMPORALIDAD).index(reporte.compuerta.temporalidad),
                format_func=lambda t: ETIQUETA_TEMPORALIDAD.get(t, t),
            )
            corr_intencion = st.selectbox(
                "Corregir intención",
                options=list(ETIQUETA_INTENCION),
                index=list(ETIQUETA_INTENCION).index(reporte.compuerta.intencion),
                format_func=lambda t: ETIQUETA_INTENCION.get(t, t),
            )

            corr_comuna = None
            if reporte.ubicacion:
                corr_comuna = st.text_input("Corregir comuna", value=reporte.ubicacion.comuna or "")

            if st.form_submit_button("Guardar corrección"):
                correccion = construir_correccion(
                    corr_tipo, corr_temporalidad, corr_intencion, corr_comuna
                )
                cliente.actualizar(
                    reporte.id, estado_revision=reporte.estado_revision, correccion=correccion
                )
                st.success("Corrección guardada.")
                st.rerun()


def main() -> None:
    """Renderiza la pantalla completa de Detalle."""
    inyectar_tema()
    renderizar_pie_sidebar(modo_demo=usa_datos_de_ejemplo())

    id_reporte = st.session_state.get("reporte_seleccionado_id")
    if not id_reporte:
        st.title("Detalle del reporte")
        st.info("Selecciona un reporte desde la Bandeja para ver su detalle.")
        _volver_a_la_bandeja()
        return

    cliente = cliente_de_sesion()
    try:
        reporte = cliente.obtener(id_reporte)
    except (KeyError, ErrorBFF):
        st.title("Detalle del reporte")
        st.warning("No se pudo cargar este reporte. Puede que ya no esté disponible.")
        _volver_a_la_bandeja()
        return

    _volver_a_la_bandeja()
    st.title("Detalle del reporte")
    _mostrar_encabezado(reporte)
    st.write("")

    col_izquierda, col_derecha = st.columns(2)
    with col_izquierda:
        _mostrar_naturaleza_y_ubicacion(reporte)
    with col_derecha:
        _mostrar_mensaje(reporte)
        _mostrar_triaje(cliente, reporte)


if __name__ == "__main__":
    main()

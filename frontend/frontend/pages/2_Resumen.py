"""Resumen operativo: KPIs y gráficos descriptivos, segunda pantalla del tablero.

Toda la lógica de gráficos vive en `frontend.resumen` para poder probarla con
pytest normal (ver `frontend/frontend/pages/1_Bandeja.py` para el mismo patrón).
"""

import streamlit as st

from frontend.cliente import cliente_de_sesion, usa_datos_de_ejemplo
from frontend.resumen import (
    calcular_tasa_accionable,
    calcular_tasa_revision,
    construir_grafico_comuna,
    construir_grafico_granularidad,
    construir_grafico_intencion,
    construir_grafico_servicio,
    construir_grafico_temporalidad,
    construir_grafico_tendencia,
    construir_grafico_tipo_evento,
)
from frontend.theme import inyectar_tema, mostrar_metrica, renderizar_pie_sidebar


def _leer_rango_fechas() -> tuple[str | None, str | None]:
    """Renderiza los selectores de fecha y los convierte a ISO 8601.

    Returns:
        Una tupla `(desde, hasta)`, cada uno `None` si el operador no lo fijó.

    """
    col_desde, col_hasta = st.columns(2)
    with col_desde:
        fecha_desde = st.date_input("Desde", value=None)
    with col_hasta:
        fecha_hasta = st.date_input("Hasta", value=None)
    return (
        fecha_desde.isoformat() if fecha_desde else None,
        fecha_hasta.isoformat() if fecha_hasta else None,
    )


def main() -> None:
    """Renderiza la pantalla completa de Resumen."""
    inyectar_tema()
    renderizar_pie_sidebar(modo_demo=usa_datos_de_ejemplo())
    st.title("Resumen operativo")

    cliente = cliente_de_sesion()
    desde, hasta = _leer_rango_fechas()
    resumen = cliente.resumen(desde=desde, hasta=hasta)

    col1, col2, col3, col4 = st.columns(4)
    mostrar_metrica(col1, "Total", resumen.total)
    mostrar_metrica(col2, "Pendientes", resumen.pendientes)
    mostrar_metrica(col3, "Revisados", resumen.revisados)
    mostrar_metrica(col4, "Tasa de revisión", f"{calcular_tasa_revision(resumen):.1f}%")

    if resumen.total == 0:
        st.info("No hay reportes en este rango de fechas.")
        return

    col5, col6, col7 = st.columns(3)
    mostrar_metrica(col5, "Accionables", resumen.por_accionable.get("accionable", 0))
    mostrar_metrica(col6, "No accionables", resumen.por_accionable.get("no_accionable", 0))
    mostrar_metrica(col7, "Tasa de accionabilidad", f"{calcular_tasa_accionable(resumen):.1f}%")

    col_tipo, col_comuna = st.columns(2)
    with col_tipo, st.container(border=True):
        st.subheader("Reportes por tipo de evento")
        st.plotly_chart(construir_grafico_tipo_evento(resumen), width="stretch")
    with col_comuna, st.container(border=True):
        st.subheader("Reportes por comuna")
        st.plotly_chart(construir_grafico_comuna(resumen), width="stretch")

    col_temp, col_intencion = st.columns(2)
    with col_temp, st.container(border=True):
        st.subheader("Reportes por temporalidad")
        st.plotly_chart(construir_grafico_temporalidad(resumen), width="stretch")
    with col_intencion, st.container(border=True):
        st.subheader("Reportes por intención")
        st.plotly_chart(construir_grafico_intencion(resumen), width="stretch")

    col_servicio, col_granularidad = st.columns(2)
    with col_servicio, st.container(border=True):
        st.subheader("Servicios de respuesta más solicitados")
        st.plotly_chart(construir_grafico_servicio(resumen), width="stretch")
    with col_granularidad, st.container(border=True):
        st.subheader("Precisión de la ubicación")
        st.plotly_chart(construir_grafico_granularidad(resumen), width="stretch")

    with st.container(border=True):
        st.subheader("Tendencia de reportes por día")
        st.plotly_chart(construir_grafico_tendencia(resumen), width="stretch")


if __name__ == "__main__":
    main()

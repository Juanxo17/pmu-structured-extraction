"""Resumen operativo: KPIs y gráficos descriptivos, segunda pantalla del tablero.

Toda la lógica de gráficos vive en `frontend.resumen` para poder probarla con
pytest normal (ver `frontend/frontend/pages/1_Bandeja.py` para el mismo patrón).
"""

import streamlit as st

from frontend.bandeja import elegir_cliente, usa_datos_de_ejemplo
from frontend.resumen import (
    calcular_tasa_revision,
    construir_grafico_comuna,
    construir_grafico_tipo_evento,
)
from frontend.theme import inyectar_tema, renderizar_pie_sidebar


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

    cliente = elegir_cliente()
    desde, hasta = _leer_rango_fechas()
    resumen = cliente.resumen(desde=desde, hasta=hasta)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", resumen.total)
    col2.metric("Pendientes", resumen.pendientes)
    col3.metric("Revisados", resumen.revisados)
    col4.metric("Tasa de revisión", f"{calcular_tasa_revision(resumen):.1f}%")

    if resumen.total == 0:
        st.info("No hay reportes en este rango de fechas.")
        return

    col_tipo, col_comuna = st.columns(2)
    with col_tipo:
        st.subheader("Reportes por tipo de evento")
        st.plotly_chart(construir_grafico_tipo_evento(resumen), use_container_width=True)
    with col_comuna:
        st.subheader("Reportes por comuna")
        st.plotly_chart(construir_grafico_comuna(resumen), use_container_width=True)

    st.caption("Próximamente: tendencia de reportes por día.")


if __name__ == "__main__":
    main()

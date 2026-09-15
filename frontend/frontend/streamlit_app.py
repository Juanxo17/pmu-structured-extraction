"""Tablero de operador — consume BFF vía HTTP, punto de entrada de Streamlit."""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="SIRENA — Tablero de operador", layout="wide")

_LOGO = Path(__file__).parent / "assets" / "logo_sirena.svg"
st.logo(str(_LOGO))

paginas = [
    st.Page("pages/1_Bandeja.py", title="Bandeja", icon="📥", default=True),
    st.Page("pages/2_Resumen.py", title="Resumen", icon="📊"),
]

st.navigation(paginas).run()

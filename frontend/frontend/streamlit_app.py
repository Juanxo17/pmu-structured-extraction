"""Tablero de operador — consume BFF vía HTTP, punto de entrada de Streamlit."""

import streamlit as st

st.set_page_config(page_title="SIRENA — Tablero de operador", layout="wide")

paginas = [
    st.Page("pages/1_Bandeja.py", title="Bandeja", icon="📥", default=True),
]

st.navigation(paginas).run()

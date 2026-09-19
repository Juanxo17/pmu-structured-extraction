"""Selección del `ClienteReportes` a usar: real (BFF) o simulado.

Vive separado de `frontend.bandeja` a propósito: Resumen y Detalle también
necesitan elegir cliente, y no tiene sentido que dependan del módulo de la
Bandeja para eso — es una decisión transversal a las tres pantallas, no algo
propio de la tabla/mapa de la Bandeja.
"""

from __future__ import annotations

import os

import streamlit as st

from frontend.bff_client import BFFClient, ClienteReportes
from frontend.reportes_mock import ClienteReportesSimulado


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


def cliente_de_sesion() -> ClienteReportes:
    """Como `elegir_cliente`, pero reutiliza el mismo cliente simulado entre reruns.

    Streamlit vuelve a ejecutar todo el script en cada interacción; sin este
    cacheo, cada rerun crearía un `ClienteReportesSimulado` nuevo (dataset de
    ejemplo fresco) y cualquier cambio de triaje hecho en la sesión se
    perdería de inmediato. No aplica a `BFFClient`: CRUD ya persiste de
    verdad, así que ese caso se resuelve tal cual con `elegir_cliente`.

    Returns:
        El cliente a usar, estable durante toda la sesión del navegador
        cuando es simulado.

    """
    if not usa_datos_de_ejemplo():
        return elegir_cliente()
    if "cliente_simulado" not in st.session_state:
        st.session_state["cliente_simulado"] = elegir_cliente()
    return st.session_state["cliente_simulado"]

"""Paleta, etiquetas y estilos compartidos por las páginas del tablero.

Los colores y la tipografía replican el mockup de diseño aprobado para SIRENA
(validado con el validador de paletas colorblind-safe del skill de dataviz).
Las etiquetas legibles de tipo_evento/servicio_de_respuesta, en cambio, no se
inventan acá: se leen de `config/ontologia.yaml` (fuente única del vocabulario
del dominio, ver AGENTS.md) a través de `sirena_schema.ontologia.ONTOLOGIA`.
"""

from __future__ import annotations

import streamlit as st
from sirena_schema.ontologia import ONTOLOGIA

COLOR_TIPO_EVENTO: dict[str, str] = {
    "sismo": "#5C56C6",
    "movimiento_en_masa": "#9C5A1E",
    "inundacion_subita": "#1E74BD",
    "inundacion_lenta": "#159E77",
    "incendio_cobertura_vegetal": "#B8691C",
    "incendio_estructural": "#A02D63",
    "aglomeracion_publico": "#9C8A2E",
    "salud_ambiental": "#7A4FA6",
}

ETIQUETA_TIPO_EVENTO: dict[str, str] = ONTOLOGIA.nombres_tipo_evento
ETIQUETA_SERVICIO: dict[str, str] = ONTOLOGIA.nombres_servicio_de_respuesta

# `streamlit-aggrid` no soporta de forma confiable un cellRenderer que
# inyecte HTML/DOM (ver commit que reemplazó ese intento): un string se
# muestra como texto plano y un nodo DOM real revienta con "React error #31".
# Por eso el color de tipo_evento se muestra como texto plano con un emoji de
# círculo, no como un `<span>` coloreado.
ICONO_TIPO_EVENTO: dict[str, str] = {
    "sismo": "🟣",
    "movimiento_en_masa": "🟤",
    "inundacion_subita": "🔵",
    "inundacion_lenta": "🟢",
    "incendio_cobertura_vegetal": "🟠",
    "incendio_estructural": "🔴",
    "aglomeracion_publico": "🟡",
    "salud_ambiental": "⚫",
}

ICONO_ESTADO: dict[str, str] = {
    "pendiente": "🟠",
    "revisado": "🟢",
}

ETIQUETA_TEMPORALIDAD: dict[str, str] = {
    "ocurriendo_ahora": "Ocurriendo ahora",
    "ya_ocurrio": "Ya ocurrió",
    "riesgo_previsto": "Riesgo previsto",
    "referencia_noticia": "Referencia noticia",
}

ETIQUETA_INTENCION: dict[str, str] = {
    "solicita_ayuda": "Solicita ayuda",
    "reporta_terceros": "Reporta terceros",
    "ofrece_ayuda": "Ofrece ayuda",
    "solicita_informacion": "Solicita información",
}

ETIQUETA_ESTADO: dict[str, str] = {
    "pendiente": "Pendiente",
    "revisado": "Revisado",
}

ETIQUETA_ACCIONABLE: dict[str, str] = {
    "accionable": "Accionables",
    "no_accionable": "No accionables",
}

ETIQUETA_GRANULARIDAD: dict[str, str] = {
    "exacta": "Exacta",
    "barrio": "Barrio",
    "comuna": "Comuna",
    "ciudad": "Ciudad",
    "indeterminada": "Indeterminada",
}

COLOR_ESTADO: dict[str, str] = {
    "pendiente": "#9A6512",
    "revisado": "#25714A",
}

COLOR_ESTADO_FONDO: dict[str, str] = {
    "pendiente": "#F6ECD9",
    "revisado": "#E1EEE5",
}

# Acento de marca (navy del mockup) — para elementos de magnitud/UI que no
# son identidad categórica, como las barras de "reportes por comuna".
COLOR_ACCENT = "#123C6B"

# Gris neutro — para indicadores de calidad de dato (ej. granularidad de la
# ubicación), a propósito distinto del acento de marca y de la paleta
# categórica, para que no se lean como "más contenido" sino como "meta-dato".
COLOR_MUTED = "#79847E"

# Variantes pasteles — solo para los gráficos de la pantalla Resumen (pedido
# explícito de diseño para esa pantalla). Cada hue se revalidó con el
# validador de paletas colorblind-safe del skill de dataviz (banda de
# luminosidad, piso de croma, separación CVD); el WARN de contraste vs. fondo
# que queda es aceptable porque cada barra siempre lleva su valor como texto
# plano al lado, no depende del color para leerse.
COLOR_TIPO_EVENTO_PASTEL: dict[str, str] = {
    "sismo": "#8F82D9",
    "movimiento_en_masa": "#C08840",
    "inundacion_subita": "#5B9FD4",
    "inundacion_lenta": "#3FBE7F",
    "incendio_cobertura_vegetal": "#DE9840",
    "incendio_estructural": "#CC5E8C",
    "aglomeracion_publico": "#BDA83E",
    "salud_ambiental": "#A57FC7",
}

COLOR_ACCENT_PASTEL = "#7C93BF"
COLOR_MUTED_PASTEL = "#ADB5AC"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: "IBM Plex Sans", system-ui, sans-serif; }
h1, h2, h3, [data-testid="stMetricLabel"] { font-family: "Archivo", system-ui, sans-serif; }
[data-testid="stMetricValue"] { font-family: "IBM Plex Mono", ui-monospace, monospace; }

.sirena-estado-pill {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 600; padding: 3px 9px; border-radius: 999px;
}
.sirena-caveat {
  font-size: 12.5px; border: 1px dashed #9A6512; background: #F6ECD9;
  border-radius: 8px; padding: 8px 12px; color: #4B5652;
}
</style>
"""


def inyectar_tema() -> None:
    """Inyecta la hoja de estilos compartida (tipografía, ajustes de KPI) en la página."""
    st.markdown(_CSS, unsafe_allow_html=True)


def mostrar_metrica(columna, etiqueta: str, valor: object) -> None:
    """Muestra un `st.metric` dentro de una tarjeta con contorno, como en el mockup.

    Args:
        columna: Columna de Streamlit donde va la tarjeta.
        etiqueta: Título de la métrica.
        valor: Valor a mostrar (número o texto ya formateado).

    """
    with columna, st.container(border=True):
        st.metric(etiqueta, valor)


def renderizar_pie_sidebar(modo_demo: bool = False) -> None:
    """Muestra la nota de pie del sidebar, debajo del menú de navegación.

    Se llama desde cada página (mismo patrón que `inyectar_tema`) porque el
    menú de páginas de `st.navigation` ya ocupa la parte de arriba del
    sidebar — lo que agregue cada página aquí queda debajo de ese menú.

    El texto está pensado para el operador que usa el tablero, no para quien
    lo programa: nada de nombres de variables de entorno, clases o archivos
    de contrato — solo un aviso de que los datos son de ejemplo, cuando
    aplica.

    Args:
        modo_demo: True si el tablero está mostrando datos de ejemplo en vez
            de reportes reales.

    """
    st.sidebar.divider()
    if modo_demo:
        st.sidebar.caption(
            "🧪 Datos de ejemplo — este tablero aún no está conectado a reportes reales."
        )

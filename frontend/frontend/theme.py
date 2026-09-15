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

COLOR_ESTADO: dict[str, str] = {
    "pendiente": "#9A6512",
    "revisado": "#25714A",
}

COLOR_ESTADO_FONDO: dict[str, str] = {
    "pendiente": "#F6ECD9",
    "revisado": "#E1EEE5",
}

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

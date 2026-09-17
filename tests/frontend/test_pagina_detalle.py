"""Pruebas de humo de la página Detalle, con el harness oficial de Streamlit."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

_RAIZ_REPO = Path(__file__).resolve().parents[2]
_RUTA_ENTRYPOINT = _RAIZ_REPO / "frontend" / "frontend" / "streamlit_app.py"
_ID_REPORTE_DE_EJEMPLO = "rpt_2b9d77e4"


def _ir_a_detalle(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Carga el entrypoint y navega a Detalle, sin BFF_URL (modo demo).

    `st.page_link` (el enlace de "volver a la bandeja") solo resuelve contra
    páginas registradas por `st.navigation` — por eso el AppTest arranca
    desde `streamlit_app.py` y no directamente desde `pages/3_Detalle.py`.

    Args:
        monkeypatch: Fixture de pytest para variables de entorno.

    Returns:
        El AppTest, ya parado en la pantalla Detalle (todavía sin `reporte_seleccionado_id`).

    """
    monkeypatch.delenv("BFF_URL", raising=False)
    app = AppTest.from_file(str(_RUTA_ENTRYPOINT))
    app.run()
    return app.switch_page("pages/3_Detalle.py")


class TestPaginaDetalle:
    """Pruebas de las distintas formas de entrar a la pantalla Detalle."""

    def test_sin_seleccion_muestra_aviso_y_no_revienta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sin un reporte seleccionado, invita a volver a la Bandeja, sin excepción."""
        # Arrange
        app = _ir_a_detalle(monkeypatch)

        # Act
        app.run()

        # Assert
        assert not app.exception
        assert len(app.info) == 1

    def test_con_seleccion_valida_muestra_el_reporte(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Con un id existente en session_state, carga el reporte sin excepción."""
        # Arrange
        app = _ir_a_detalle(monkeypatch)
        app.session_state["reporte_seleccionado_id"] = _ID_REPORTE_DE_EJEMPLO

        # Act
        app.run()

        # Assert
        assert not app.exception
        assert len(app.warning) == 0

    def test_con_seleccion_inexistente_muestra_advertencia(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Con un id que ya no existe, avisa en vez de reventar."""
        # Arrange
        app = _ir_a_detalle(monkeypatch)
        app.session_state["reporte_seleccionado_id"] = "rpt_no_existe"

        # Act
        app.run()

        # Assert
        assert not app.exception
        assert len(app.warning) == 1

    def test_marcar_como_revisado_persiste_en_la_sesion(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """El cambio de estado sobrevive a un segundo rerun (cliente_de_sesion)."""
        # Arrange
        app = _ir_a_detalle(monkeypatch)
        app.session_state["reporte_seleccionado_id"] = _ID_REPORTE_DE_EJEMPLO
        app.run()
        boton = next(b for b in app.button if "marcar como revisado" in b.label.lower())

        # Act
        boton.click().run()

        # Assert
        assert not app.exception
        cliente = app.session_state["cliente_simulado"]
        assert cliente.obtener(_ID_REPORTE_DE_EJEMPLO).estado_revision == "revisado"

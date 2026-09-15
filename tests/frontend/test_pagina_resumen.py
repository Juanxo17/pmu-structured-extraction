"""Pruebas de humo de la página Resumen, con el harness oficial de Streamlit."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

_RAIZ_REPO = Path(__file__).resolve().parents[2]
_RUTA_PAGINA = _RAIZ_REPO / "frontend" / "frontend" / "pages" / "2_Resumen.py"


class TestPaginaResumen:
    """La página debe cargar sin BFF_URL y mostrar los KPIs del cliente simulado."""

    def test_carga_sin_bff_url_y_muestra_los_kpis(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sin BFF, la página arranca con datos de ejemplo y sin excepciones."""
        # Arrange
        monkeypatch.delenv("BFF_URL", raising=False)
        app = AppTest.from_file(str(_RUTA_PAGINA))

        # Act
        app.run()

        # Assert
        assert not app.exception
        assert len(app.metric) == 7
        assert app.title[0].value == "Resumen operativo"

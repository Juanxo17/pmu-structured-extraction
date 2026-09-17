"""Pruebas de las funciones puras de la pantalla Detalle (frontend.detalle)."""

import folium

from frontend.detalle import construir_correccion, construir_mapa_punto


class TestConstruirCorreccion:
    """Pruebas de construir_correccion."""

    def test_incluye_solo_los_campos_definidos(self) -> None:
        """Un campo en None (sin cambios) no aparece en el dict de corrección."""
        # Arrange / Act
        correccion = construir_correccion(
            tipo_evento="sismo", temporalidad=None, intencion=None, comuna=None
        )

        # Assert
        assert correccion == {"tipo_evento": "sismo"}

    def test_incluye_varios_campos_a_la_vez(self) -> None:
        """Compuerta y ubicación se pueden corregir en la misma llamada."""
        # Arrange / Act
        correccion = construir_correccion(
            tipo_evento=None,
            temporalidad="riesgo_previsto",
            intencion="solicita_informacion",
            comuna="Comuna 3",
        )

        # Assert
        assert correccion == {
            "temporalidad": "riesgo_previsto",
            "intencion": "solicita_informacion",
            "comuna": "Comuna 3",
        }

    def test_devuelve_dict_vacio_sin_ningun_campo(self) -> None:
        """Sin ningún campo definido, no hay nada que corregir."""
        # Arrange / Act / Assert
        assert construir_correccion(None, None, None, None) == {}


class TestConstruirMapaPunto:
    """Pruebas de construir_mapa_punto."""

    def test_agrega_un_unico_marcador_en_el_punto_dado(self) -> None:
        """El mapa trae exactamente un CircleMarker, en la coordenada dada."""
        # Arrange / Act
        mapa = construir_mapa_punto((3.45, -76.53), "#5C56C6", "Sismo")

        # Assert
        marcadores = [
            hijo for hijo in mapa._children.values() if isinstance(hijo, folium.CircleMarker)
        ]
        assert len(marcadores) == 1
        assert marcadores[0].location == [3.45, -76.53]

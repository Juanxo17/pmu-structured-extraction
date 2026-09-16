"""Pruebas de la normalizacion de texto del servicio Geo."""

from geo.normalizacion import normalizar


class TestNormalizar:
    """Pruebas de la normalizacion para busqueda insensible a acentos."""

    def test_minusculas_y_sin_tildes(self) -> None:
        """Convierte a minusculas y elimina acentos."""
        resultado = normalizar("El Vergél")
        assert resultado == "el vergel"

    def test_elimina_puntuacion_y_espacios_repetidos(self) -> None:
        """Sustituye puntuacion y colapsa espacios multiples."""
        resultado = normalizar("  Barrio, El   Diamante.  ")
        assert resultado == "barrio el diamante"

    def test_conserva_digitos(self) -> None:
        """Conserva los digitos para patrones como comuna 13."""
        resultado = normalizar("Comuna 13")
        assert resultado == "comuna 13"

    def test_texto_vacio_queda_vacio(self) -> None:
        """Una cadena vacia produce una cadena vacia."""
        assert normalizar("") == ""

    def test_solo_signos_queda_vacio(self) -> None:
        """Un texto de solo signos se normaliza a vacio."""
        assert normalizar("???.!!!") == ""

    def test_n_unica_se_descompone(self) -> None:
        """La enie se equipara a la ene sin tilde."""
        assert normalizar("Ñandú") == "nandu"

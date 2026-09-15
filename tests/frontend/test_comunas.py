"""Pruebas de los centroides de comuna usados por el mapa de la Bandeja."""

from frontend.comunas import COMUNAS_CONOCIDAS, centroide


class TestCentroideComuna:
    """Pruebas de frontend.comunas.centroide."""

    def test_devuelve_coordenadas_dentro_de_cali_para_comuna_conocida(self) -> None:
        """El centroide de una comuna conocida cae dentro del área de Cali."""
        # Arrange / Act
        punto = centroide("Comuna 20")

        # Assert
        assert punto is not None
        lat, lon = punto
        assert 3.30 < lat < 3.55
        assert -76.60 < lon < -76.45

    def test_devuelve_none_para_comuna_desconocida(self) -> None:
        """Una comuna fuera de la tabla local devuelve None, nunca inventa un punto."""
        # Arrange / Act / Assert
        assert centroide("Comuna 99") is None

    def test_devuelve_none_si_la_comuna_es_none(self) -> None:
        """Una ubicación sin comuna resuelta no rompe el llamado."""
        # Arrange / Act / Assert
        assert centroide(None) is None

    def test_comunas_conocidas_esta_ordenada_y_sin_duplicados(self) -> None:
        """La lista usada para poblar el filtro de comuna es estable y única."""
        # Arrange / Act / Assert
        assert COMUNAS_CONOCIDAS == sorted(set(COMUNAS_CONOCIDAS))

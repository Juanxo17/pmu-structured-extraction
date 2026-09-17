"""Pruebas de los centroides de comuna usados por los mapas del tablero."""

from frontend.comunas import COMUNAS_CONOCIDAS, centroide, ubicar_en_mapa


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

    def test_comunas_conocidas_esta_ordenada_numericamente_y_sin_duplicados(self) -> None:
        """Ordena 1..22, no alfabéticamente ("Comuna 10" antes que "Comuna 2")."""
        # Arrange / Act / Assert
        assert len(COMUNAS_CONOCIDAS) == len(set(COMUNAS_CONOCIDAS))
        assert COMUNAS_CONOCIDAS == sorted(COMUNAS_CONOCIDAS, key=lambda c: int(c.split()[-1]))
        assert COMUNAS_CONOCIDAS[:3] == ["Comuna 1", "Comuna 2", "Comuna 3"]
        assert COMUNAS_CONOCIDAS[-1] == "Comuna 22"

    def test_cubre_las_22_comunas_de_cali(self) -> None:
        """Ya no se limita a las 9 que traía el dataset de ejemplo original."""
        # Arrange / Act / Assert
        assert len(COMUNAS_CONOCIDAS) == 22
        assert all(centroide(f"Comuna {n}") is not None for n in range(1, 23))


class TestUbicarEnMapa:
    """Pruebas de la resolución híbrida de coordenadas para los mapas."""

    def test_usa_la_coordenada_exacta_cuando_esta_presente(self) -> None:
        """Con lat/lon dados, se usan tal cual, sin tocar el centroide."""
        # Arrange / Act
        punto = ubicar_en_mapa(3.4531, -76.5424, "Comuna inexistente")

        # Assert
        assert punto == (3.4531, -76.5424)

    def test_cae_al_centroide_de_comuna_sin_coordenada_exacta(self) -> None:
        """Sin lat/lon, se aproxima con el centroide local de la comuna."""
        # Arrange / Act
        punto = ubicar_en_mapa(None, None, "Comuna 20")

        # Assert
        assert punto == centroide("Comuna 20")

    def test_devuelve_none_sin_coordenada_exacta_ni_comuna_conocida(self) -> None:
        """Sin ninguna de las dos fuentes, no hay dónde plantar el punto."""
        # Arrange / Act / Assert
        assert ubicar_en_mapa(None, None, "Comuna inexistente") is None

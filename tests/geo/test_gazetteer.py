"""Pruebas del catalogo determinista de Cali."""

from geo.gazetteer import Gazetteer
from geo.normalizacion import normalizar


class TestGazetteerCarga:
    """Pruebas de la carga y el contenido del gazetteer."""

    def test_carga_las_22_comunas(self) -> None:
        """El catalogo contiene las 22 comunas de Cali."""
        gazetteer = Gazetteer()
        assert len(gazetteer.comunas) == 22

    def test_carga_barrios_y_sectores(self) -> None:
        """El catalogo contiene los barrios y sectores del IDESC."""
        gazetteer = Gazetteer()
        assert len(gazetteer.barrios) > 320

    def test_comuna_devuelve_nombre_canonico(self) -> None:
        """El nombre canonico no lleva cero a la izquierda."""
        gazetteer = Gazetteer()
        assert gazetteer.comuna(13).nombre == "Comuna 13"
        assert gazetteer.comuna(3).nombre == "Comuna 3"

    def test_comuna_desconocida_es_none(self) -> None:
        """Codigos fuera de rango no producen comuna."""
        gazetteer = Gazetteer()
        assert gazetteer.comuna(0) is None
        assert gazetteer.comuna(23) is None

    def test_centroides_estan_en_rango_de_cali(self) -> None:
        """Los centroides quedan dentro de la caja de Cali."""
        gazetteer = Gazetteer()
        for comuna in gazetteer.comunas.values():
            assert 3.3 <= comuna.lat <= 3.55
            assert -76.6 <= comuna.lon <= -76.4


class TestGazetteerBusqueda:
    """Pruebas de los indices de busqueda del gazetteer."""

    def test_barrios_en_texto_detecta_palabra_completa(self) -> None:
        """Detecta el barrio solo si aparece como palabra completa."""
        gazetteer = Gazetteer()
        barrios = gazetteer.barrios_en_texto("el vergel")
        assert [barrio.nombre for barrio in barrios] == ["El Vergel"]

    def test_barrios_en_texto_no_detecta_fragmento(self) -> None:
        """Un prefijo aislado no debe coincidir con un barrio distinto."""
        gazetteer = Gazetteer()
        assert gazetteer.barrios_en_texto("vergeles") == []

    def test_comunas_por_numero_evita_duplicados(self) -> None:
        """La mencion repetida de una comuna no duplica el resultado."""
        gazetteer = Gazetteer()
        comunas = gazetteer.comunas_por_numero("comuna 03 y comuna 3")
        assert [comuna.nombre for comuna in comunas] == ["Comuna 3"]

    def test_comunas_por_numero_ignora_no_adyacente(self) -> None:
        """La marca exige la palabra comuna pegada al numero."""
        gazetteer = Gazetteer()
        assert gazetteer.comunas_por_numero("comuna del 13") == []

    def test_menciona_ciudad_reconoce_cali(self) -> None:
        """La palabra cali activa el nivel ciudad."""
        gazetteer = Gazetteer()
        assert gazetteer.menciona_ciudad("santiago de cali")
        assert gazetteer.menciona_ciudad("california") is False
        assert gazetteer.menciona_ciudad(normalizar("CALI"))

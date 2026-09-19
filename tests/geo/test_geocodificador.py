"""Pruebas del geocodificador determinista del servicio Geo."""

import pytest

from geo.gazetteer import Barrio, Comuna, Gazetteer
from geo.geocodificador import Geocodificador
from geo.nominatim import ResultadoExterno, ResolverExterno


class ExternoFalso(ResolverExterno):
    """Resolutor externo de prueba con respuesta programable."""

    def __init__(self, respuesta: ResultadoExterno | None) -> None:
        self._respuesta = respuesta
        self.llamadas: list[str] = []

    def geocodificar(self, texto: str) -> ResultadoExterno | None:
        self.llamadas.append(texto)
        return self._respuesta


@pytest.fixture
def gazetteer() -> Gazetteer:
    """Gazetteer real con los datos del IDESC."""
    return Gazetteer()


class GazetteerFijo:
    """Gazetteer de prueba que devuelve candidatos prefijados."""

    def __init__(self, barrios: list[Barrio]) -> None:
        self._barrios = barrios

    def barrios_en_texto(self, texto_norm: str) -> list[Barrio]:
        return self._barrios

    def comuna(self, codigo: int) -> Comuna:
        return Comuna(codigo=codigo, lat=3.4, lon=-76.5)

    def comunas_por_numero(self, texto_norm: str) -> list[Comuna]:
        return []

    def menciona_ciudad(self, texto_norm: str) -> bool:
        return False


class TestResolucionPorGazetteer:
    """Pruebas del camino rapido determinista (sin red)."""

    def test_resuelve_barrio_con_nombre_completo(self, gazetteer: Gazetteer) -> None:
        """Un barrio mencionado por su nombre se resuelve a nivel barrio."""
        geocodificador = Geocodificador(gazetteer, ExternoFalso(None))

        resultado = geocodificador.resolver("El Vergel")

        assert resultado.barrio == "El Vergel"
        assert resultado.comuna == "Comuna 13"
        assert resultado.nivel_granularidad == "barrio"
        assert resultado.lat is not None
        assert resultado.lon is not None

    def test_normaliza_acentos_y_mayusculas(self, gazetteer: Gazetteer) -> None:
        """La busqueda ignora tildes y mayusculas."""
        geocodificador = Geocodificador(gazetteer, ExternoFalso(None))

        resultado = geocodificador.resolver("oído JSON en EL VERGÉL")

        assert resultado.barrio == "El Vergel"

    def test_prioriza_barrio_sobre_comuna(self, gazetteer: Gazetteer) -> None:
        """El barrio gana cuando el texto menciona ambos niveles."""
        geocodificador = Geocodificador(gazetteer, ExternoFalso(None))

        resultado = geocodificador.resolver("incendio entre El Vergel y la comuna 3")

        assert resultado.barrio == "El Vergel"
        assert resultado.comuna == "Comuna 13"

    def test_resuelve_solo_comuna(self, gazetteer: Gazetteer) -> None:
        """Una comuna explicita se resuelve a nivel comuna."""
        geocodificador = Geocodificador(gazetteer, ExternoFalso(None))

        resultado = geocodificador.resolver("desagüe obstruido en comuna 15")

        assert resultado.barrio is None
        assert resultado.comuna == "Comuna 15"
        assert resultado.nivel_granularidad == "comuna"

    def test_resuelve_ciudad(self, gazetteer: Gazetteer) -> None:
        """Mencionar Cali sin barrio ni comuna resuelve a nivel ciudad."""
        geocodificador = Geocodificador(gazetteer, ExternoFalso(None))

        resultado = geocodificador.resolver("humo en el centro de Cali")

        assert resultado.barrio is None
        assert resultado.comuna is None
        assert resultado.nivel_granularidad == "ciudad"
        assert resultado.lat is not None

    def test_usa_el_punto_de_referencia(self, gazetteer: Gazetteer) -> None:
        """El barrio puede venir en el punto de referencia."""
        geocodificador = Geocodificador(gazetteer, ExternoFalso(None))

        resultado = geocodificador.resolver("falla eléctrica", punto_referencia="El Vergel")

        assert resultado.barrio == "El Vergel"

    def test_elige_el_barrio_mas_especifico(self, gazetteer: Gazetteer) -> None:
        """Con varios candidatos gana el nombre mas largo."""
        geocodificador = Geocodificador(gazetteer, ExternoFalso(None))

        resultado = geocodificador.resolver("choque entre El Vergel y Rodrigo Lara Bonilla")

        assert resultado.barrio == "Rodrigo Lara Bonilla"

    def test_desempata_empate_de_longitud_de_forma_determinista(self) -> None:
        """Candidatos de igual longitud: gana el lexicograficamente menor."""
        candidatos = [
            Barrio(
                codigo=1,
                nombre="Bombona",
                comuna_codigo=1,
                categoria="barrio",
                lat=3.4,
                lon=-76.5,
            ),
            Barrio(
                codigo=2,
                nombre="Alborada",
                comuna_codigo=2,
                categoria="barrio",
                lat=3.45,
                lon=-76.52,
            ),
        ]
        geocodificador = Geocodificador(GazetteerFijo(candidatos), externo=None)

        resultado = geocodificador.resolver("Bombona Alborada")

        assert resultado.barrio == "Alborada"


class TestResolucionPorExterno:
    """Pruebas del respaldo externo (simulado, sin red)."""

    def test_usar_externo_sin_inventar(self, gazetteer: Gazetteer) -> None:
        """El externo puede complementar datos que el gazetteer no tiene."""
        respuesta = ResultadoExterno(lat=3.44, lon=-76.51, barrio="La Flora", comuna="Comuna 2")
        geocodificador = Geocodificador(gazetteer, ExternoFalso(respuesta))

        resultado = geocodificador.resolver("portal del norte")

        assert resultado.nivel_granularidad == "exacta"
        assert resultado.barrio == "La Flora"
        assert resultado.comuna == "Comuna 2"
        assert resultado.lat == 3.44

    def test_externo_sin_comuna_deja_comuna_vacia(self, gazetteer: Gazetteer) -> None:
        """La comuna queda vacia si el externo no la reporta."""
        respuesta = ResultadoExterno(lat=3.44, lon=-76.51, barrio="La Flora")
        geocodificador = Geocodificador(gazetteer, ExternoFalso(respuesta))

        resultado = geocodificador.resolver("portal del norte")

        assert resultado.comuna is None
        assert resultado.nivel_granularidad == "exacta"

    def test_sin_datos_del_externo_es_indeterminada(self, gazetteer: Gazetteer) -> None:
        """Sin datos del gazetteer ni del externo no se inventa nada."""
        geocodificador = Geocodificador(gazetteer, ExternoFalso(None))

        resultado = geocodificador.resolver("entre la casa de la esquina y el árbol")

        assert resultado.barrio is None
        assert resultado.comuna is None
        assert resultado.nivel_granularidad == "indeterminada"
        assert resultado.lat is None
        assert resultado.lon is None

    def test_sin_externo_no_consume_red(self, gazetteer: Gazetteer) -> None:
        """Sin respaldo externo, el texto desconocido es indeterminado."""
        geocodificador = Geocodificador(gazetteer, externo=None)

        resultado = geocodificador.resolver("nombre de un lugar lejano")

        assert resultado.nivel_granularidad == "indeterminada"


class TestCasosFrontera:
    """Pruebas de entradas vacias o degeneradas."""

    def test_texto_vacio_es_indeterminada(self, gazetteer: Gazetteer) -> None:
        """Un bloque de ubicacion vacio no dispara llamadas al externo."""
        externo = ExternoFalso(None)
        geocodificador = Geocodificador(gazetteer, externo)

        resultado = geocodificador.resolver("")

        assert resultado.nivel_granularidad == "indeterminada"
        assert externo.llamadas == []

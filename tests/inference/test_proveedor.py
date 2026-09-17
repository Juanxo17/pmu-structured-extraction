"""Pruebas del proveedor del LLM y sus reintentos."""

import logging
from collections.abc import Callable

import httpx
import pytest
from groq import APIStatusError, RateLimitError

from inference import proveedor


class RespuestaSimulada:
    """Hace las veces de la respuesta del cliente de Groq.

    Attributes:
        choices: Lista con una unica eleccion cuyo mensaje trae el contenido.

    """

    class _Mensaje:
        """Contenido de una eleccion."""

        def __init__(self, contenido: str) -> None:
            self.content = contenido

    class _Eleccion:
        """Eleccion unica de la respuesta."""

        def __init__(self, contenido: str) -> None:
            self.message = RespuestaSimulada._Mensaje(contenido)

    def __init__(self, contenido: str) -> None:
        self.choices = [RespuestaSimulada._Eleccion(contenido)]


class ClienteSimulado:
    """Cliente de Groq falso que desencola comportamientos por llamada.

    Cada elemento de ``comportamientos`` es un callable que devuelve una
    respuesta o lanza una excepcion de API; se consume de a uno por llamada
    a ``create``.

    Attributes:
        llamadas: Cantidad de veces que se invoco ``create``.

    """

    class _Completions:
        """Acceso anidado a chat.completions de la API."""

        def __init__(self, cliente: "ClienteSimulado") -> None:
            self._cliente = cliente

        def create(self, **_kwargs) -> RespuestaSimulada:
            """Consume el siguiente comportamiento y lo ejecuta."""
            self._cliente.llamadas += 1
            comportamiento = self._cliente._comportamientos.pop(0)
            return comportamiento()

    class _Chat:
        """Acceso a la propiedad chat del cliente."""

        def __init__(self, cliente: "ClienteSimulado") -> None:
            self.completions = cliente._Completions(cliente)

    def __init__(self, *comportamientos: Callable[[], object]) -> None:
        self._comportamientos = list(comportamientos)
        self.llamadas = 0

    @property
    def chat(self) -> "ClienteSimulado._Chat":
        """Devuelve el acceso anidado a completions."""
        return ClienteSimulado._Chat(self)


def _error_api(status_code: int, cabeceras: dict[str, str] | None = None):
    """Construye una excepcion de API de Groq con el estado indicado.

    Args:
        status_code: Codigo de estado HTTP del error.
        cabeceras: Cabeceras de la respuesta, como Retry-After.

    Returns:
        Una excepcion RateLimitError (429) o APIStatusError (demas estados).

    """
    peticion = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    respuesta = httpx.Response(status_code, request=peticion, headers=cabeceras or {})
    if status_code == 429:
        return RateLimitError("cuota excedida", response=respuesta, body=None)
    return APIStatusError("error de API", response=respuesta, body=None)


def _devolver(contenido: str) -> Callable[[], RespuestaSimulada]:
    """Devuelve un comportamiento que entrega una respuesta simulada.

    Args:
        contenido: Texto que devuelve la respuesta simulada.

    Returns:
        Callable que produce una RespuestaSimulada con el contenido.

    """
    return lambda: RespuestaSimulada(contenido)


def _levantar_error(
    status_code: int, cabeceras: dict[str, str] | None = None
) -> Callable[[], object]:
    """Devuelve un comportamiento que lanza un error de API de Groq.

    Args:
        status_code: Codigo de estado HTTP del error.
        cabeceras: Cabeceras de la respuesta, como Retry-After.

    Returns:
        Callable que lanza una excepcion RateLimitError (429) o APIStatusError.

    """

    def lanzar() -> object:
        raise _error_api(status_code, cabeceras)

    return lanzar


def _proveedor(comportamiento_cliente: ClienteSimulado, **kwargs) -> proveedor.ProveedorGroq:
    """Construye un ProveedorGroq sin red ni esperas reales.

    Args:
        comportamiento_cliente: Cliente falso que se inyecta al proveedor.
        **kwargs: Argumentos del constructor de ProveedorGroq.

    Returns:
        ProveedorGroq configurado con el cliente simulado.

    """
    kwargs.setdefault("jitter_max", 0.0)
    cliente = proveedor.ProveedorGroq(api_key="clave-de-prueba", **kwargs)
    cliente._cliente = comportamiento_cliente
    return cliente


class TestProveedor:
    """Pruebas del cliente base del proveedor."""

    def test_usa_clave_y_modelo_entregados(self) -> None:
        """El constructor conserva la clave y el modelo si se entregan."""
        # Arrange
        cliente = proveedor.ProveedorGroq(
            api_key="clave-de-prueba", modelo="llama-3.3-70b-versatile"
        )

        # Act & Assert
        assert cliente._api_key == "clave-de-prueba"
        assert cliente._modelo == "llama-3.3-70b-versatile"

    def test_temperatura_por_defecto_es_cero(self) -> None:
        """La temperatura por defecto es 0 para salidas deterministas."""
        # Arrange
        cliente = proveedor.ProveedorGroq(api_key="clave-de-prueba")

        # Act & Assert
        assert cliente.temperatura == 0.0

    def test_falla_sin_clave_de_api(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Construir el proveedor sin clave lanza ValueError."""
        # Arrange
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        # Act & Assert
        with pytest.raises(ValueError):
            proveedor.ProveedorGroq(api_key=None, modelo="x")

    def test_lee_configuracion_de_entorno(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Los reintentos se configuran con variables de entorno."""
        # Arrange
        monkeypatch.setenv("INFERENCE_INTENTOS_LLM", "5")
        monkeypatch.setenv("INFERENCE_ESPERA_BASE", "2.0")
        monkeypatch.setenv("INFERENCE_JITTER_MAX", "0.7")

        # Act
        cliente = proveedor.ProveedorGroq(api_key="clave-de-prueba")

        # Assert
        assert cliente.intentos == 5
        assert cliente.espera_base == 2.0
        assert cliente.jitter_max == 0.7

    def test_argumentos_anulan_configuracion_de_entorno(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Los argumentos del constructor ganan sobre las variables de entorno."""
        # Arrange
        monkeypatch.setenv("INFERENCE_INTENTOS_LLM", "5")
        monkeypatch.setenv("INFERENCE_ESPERA_BASE", "2.0")

        # Act
        cliente = proveedor.ProveedorGroq(api_key="clave-de-prueba", intentos=1, espera_base=0.0)

        # Assert
        assert cliente.intentos == 1
        assert cliente.espera_base == 0.0

    def test_entrega_contenido_devuelto_por_el_cliente(self) -> None:
        """completar devuelve el texto crudo de la primera eleccion."""
        # Arrange
        cliente = _proveedor(ClienteSimulado(_devolver("reporte")))
        cliente.intentos = 1

        # Act
        resultado = cliente.completar("sistema", "usuario")

        # Assert
        assert resultado == "reporte"

    def test_contenido_vacio_se_devuelve_como_cadena(self) -> None:
        """Un contenido vacio no rompe la entrega."""
        # Arrange
        cliente = _proveedor(ClienteSimulado(_devolver("")))
        cliente.intentos = 1

        # Act
        resultado = cliente.completar("sistema", "usuario")

        # Assert
        assert resultado == ""


class TestReintentos:
    """Pruebas del reintento ante errores transitorios de la API."""

    def test_reintenta_error_429_y_exitos_en_segunda_llamada(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un 429 no agota el intento; la segunda llamada sale bien."""
        # Arrange
        simulado = ClienteSimulado(_levantar_error(429), _devolver("reporte"))
        cliente = _proveedor(simulado, intentos=2)
        esperas: list[float] = []
        monkeypatch.setattr(proveedor.time, "sleep", esperas.append)

        # Act
        resultado = cliente.completar("sistema", "usuario")

        # Assert
        assert resultado == "reporte"
        assert simulado.llamadas == 2
        assert esperas == [1.0]

    def test_reintenta_error_5xx_con_retroceso_exponencial(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dos 500 consecutivos generan esperas de 1s y 2s (backoff)."""
        # Arrange
        simulado = ClienteSimulado(_levantar_error(500), _levantar_error(500), _devolver("reporte"))
        cliente = _proveedor(simulado, intentos=3)
        esperas: list[float] = []
        monkeypatch.setattr(proveedor.time, "sleep", esperas.append)

        # Act
        resultado = cliente.completar("sistema", "usuario")

        # Assert
        assert resultado == "reporte"
        assert simulado.llamadas == 3
        assert esperas == [1.0, 2.0]

    def test_respeta_cabecera_retry_after_del_proveedor(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """La cabecera Retry-After reemplaza el retroceso exponencial."""
        # Arrange
        simulado = ClienteSimulado(
            _levantar_error(429, {"retry-after": "2.5"}), _devolver("reporte")
        )
        cliente = _proveedor(simulado, intentos=2)
        esperas: list[float] = []
        monkeypatch.setattr(proveedor.time, "sleep", esperas.append)

        # Act
        resultado = cliente.completar("sistema", "usuario")

        # Assert
        assert resultado == "reporte"
        assert esperas == [2.5]

    def test_agota_intentos_y_relanza_el_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Si todos los intentos fallan, se propaga el ultimo error."""
        # Arrange
        simulado = ClienteSimulado(_levantar_error(429), _levantar_error(429))
        cliente = _proveedor(simulado, intentos=2)
        monkeypatch.setattr(proveedor.time, "sleep", lambda _: None)

        # Act & Assert
        with pytest.raises(RateLimitError):
            cliente.completar("sistema", "usuario")
        assert simulado.llamadas == 2

    def test_no_reintenta_error_no_transitorio(self) -> None:
        """Un 401 no admite reintento y se propaga de inmediato."""
        # Arrange
        simulado = ClienteSimulado(_levantar_error(401))
        cliente = _proveedor(simulado, intentos=3)

        # Act & Assert
        with pytest.raises(APIStatusError):
            cliente.completar("sistema", "usuario")
        assert simulado.llamadas == 1

    def test_aplica_jitter_a_la_espera(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """El jitter agrega una variacion aleatoria a la espera."""
        # Arrange
        simulado = ClienteSimulado(_levantar_error(500), _devolver("reporte"))
        cliente = _proveedor(simulado, intentos=2, jitter_max=0.5)
        esperas: list[float] = []
        monkeypatch.setattr(proveedor.time, "sleep", esperas.append)

        # Act
        resultado = cliente.completar("sistema", "usuario")

        # Assert
        assert resultado == "reporte"
        assert 1.0 <= esperas[0] <= 1.5


class TestLoggingProveedor:
    """Pruebas del registro de llamadas exitosas y fallidas."""

    def test_registra_error_definitivo(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Un error definitivo se registra como error."""
        # Arrange
        simulado = ClienteSimulado(_levantar_error(401))
        cliente = _proveedor(simulado, intentos=3)
        monkeypatch.setattr(proveedor.time, "sleep", lambda _: None)

        # Act
        with caplog.at_level(logging.ERROR, logger="inference.proveedor"):
            with pytest.raises(APIStatusError):
                cliente.completar("sistema", "usuario")

        # Assert
        assert any("HTTP 401" in r.getMessage() for r in caplog.records)

    def test_registra_reintento(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Un error transitorio se registra como advertencia."""
        # Arrange
        simulado = ClienteSimulado(_levantar_error(429), _devolver("reporte"))
        cliente = _proveedor(simulado, intentos=2)
        monkeypatch.setattr(proveedor.time, "sleep", lambda _: None)

        # Act & Assert
        with caplog.at_level(logging.WARNING, logger="inference.proveedor"):
            resultado = cliente.completar("sistema", "usuario")
        assert resultado == "reporte"
        assert any("reintento" in r.getMessage() for r in caplog.records)

    def test_registra_exito_en_primer_intento(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Una llamada exitosa se registra como informacion."""
        # Arrange
        simulado = ClienteSimulado(_devolver("reporte"))
        cliente = _proveedor(simulado, intentos=3)
        monkeypatch.setattr(proveedor.time, "sleep", lambda _: None)

        # Act
        with caplog.at_level(logging.INFO, logger="inference.proveedor"):
            cliente.completar("sistema", "usuario")

        # Assert
        assert any("exitosa" in r.getMessage() for r in caplog.records)

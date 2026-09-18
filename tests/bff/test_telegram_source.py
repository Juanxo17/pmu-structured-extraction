"""Pruebas de la fuente de mensajes de Telegram.

Las llamadas HTTP a la API de Telegram y a BFF se simulan con un cliente
falso (mismo espiritu que los `monkeypatch` usados en el resto del
proyecto) -- no se toca la red real en ninguna prueba.
"""

import asyncio

import httpx
import pytest

from bff import telegram_source
from bff.telegram_source import _a_mensaje_entrante, _enviar_a_bff, _leer_actualizaciones


def _ejecutar(coroutine):
    """Corre una corrutina en un test sincrono (sin pytest-asyncio)."""
    return asyncio.run(coroutine)


class _RespuestaFalsa:
    """Respuesta HTTP falsa, con solo lo que estas pruebas necesitan."""

    def __init__(self, json_data: dict | None = None, status_code: int = 200) -> None:
        self._json_data = json_data
        self.status_code = status_code
        self.text = "detalle del error simulado"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error simulado", request=None, response=self)  # type: ignore[arg-type]

    def json(self) -> dict:
        return self._json_data


class _ClienteFalso:
    """Cliente HTTP falso: registra las peticiones que recibe."""

    def __init__(self, resultado_get: list | None = None, status_post: int = 200) -> None:
        self._resultado_get = resultado_get if resultado_get is not None else []
        self._status_post = status_post
        self.peticiones_get: list[tuple[str, dict]] = []
        self.peticiones_post: list[tuple[str, dict]] = []

    async def get(self, url: str, params: dict, timeout: float) -> _RespuestaFalsa:  # noqa: ARG002
        self.peticiones_get.append((url, params))
        return _RespuestaFalsa(json_data={"ok": True, "result": self._resultado_get})

    async def post(self, url: str, json: dict) -> _RespuestaFalsa:
        self.peticiones_post.append((url, json))
        return _RespuestaFalsa(status_code=self._status_post)


class TestAMensajeEntrante:
    """Pruebas de _a_mensaje_entrante."""

    def test_mensaje_de_texto_se_traduce_correctamente(self) -> None:
        """Un mensaje de texto normal se traduce a todos los campos del contrato."""
        # Arrange
        actualizacion = {
            "update_id": 100,
            "message": {
                "message_id": 42,
                "from": {"id": 555, "is_bot": False, "first_name": "Ana"},
                "chat": {"id": 555, "type": "private"},
                "date": 1758000000,
                "text": "Hay un incendio en el cerro, cerca a la 26",
            },
        }

        # Act
        resultado = _a_mensaje_entrante(actualizacion)

        # Assert
        assert resultado == {
            "fuente": "telegram",
            "id_externo": "555_42",
            "texto": "Hay un incendio en el cerro, cerca a la 26",
            "marca_temporal_origen": "2025-09-16T05:20:00+00:00",
            "autor_id_telegram": "555",
        }

    def test_id_externo_combina_chat_y_mensaje_para_ser_unico(self) -> None:
        """message_id de Telegram solo es unico por chat -- se combina con chat_id."""
        # Arrange
        actualizacion = {
            "update_id": 101,
            "message": {
                "message_id": 1,
                "from": {"id": 9, "is_bot": False},
                "chat": {"id": 777, "type": "private"},
                "date": 1758000000,
                "text": "hola",
            },
        }

        # Act
        resultado = _a_mensaje_entrante(actualizacion)

        # Assert
        assert resultado["id_externo"] == "777_1"

    def test_actualizacion_sin_mensaje_se_descarta(self) -> None:
        """Una actualizacion de otro tipo (ej. edicion de mensaje) retorna None."""
        # Arrange
        actualizacion = {"update_id": 102, "edited_message": {"message_id": 1}}

        # Act
        resultado = _a_mensaje_entrante(actualizacion)

        # Assert
        assert resultado is None

    def test_mensaje_sin_texto_se_descarta(self) -> None:
        """Un mensaje sin campo 'text' (ej. una foto) retorna None."""
        # Arrange
        actualizacion = {
            "update_id": 103,
            "message": {
                "message_id": 2,
                "from": {"id": 1, "is_bot": False},
                "chat": {"id": 1, "type": "private"},
                "date": 1758000000,
                "photo": [{"file_id": "abc"}],
            },
        }

        # Act
        resultado = _a_mensaje_entrante(actualizacion)

        # Assert
        assert resultado is None


class TestLeerActualizaciones:
    """Pruebas de _leer_actualizaciones (llamada a GET /getUpdates de Telegram)."""

    def test_primera_llamada_no_envia_offset(self) -> None:
        """Sin offset previo (None), no se envia el parametro 'offset'."""
        # Arrange
        cliente = _ClienteFalso(resultado_get=[])

        # Act
        _ejecutar(_leer_actualizaciones(cliente, "token-falso", offset=None))

        # Assert
        _url, parametros = cliente.peticiones_get[0]
        assert "offset" not in parametros

    def test_llamadas_siguientes_envian_el_offset(self) -> None:
        """Con un offset conocido, se envia tal cual en los parametros."""
        # Arrange
        cliente = _ClienteFalso(resultado_get=[])

        # Act
        _ejecutar(_leer_actualizaciones(cliente, "token-falso", offset=555))

        # Assert
        _url, parametros = cliente.peticiones_get[0]
        assert parametros["offset"] == 555

    def test_retorna_las_actualizaciones_de_telegram(self) -> None:
        """El resultado de Telegram se retorna tal cual (lista de actualizaciones)."""
        # Arrange
        actualizaciones_simuladas = [{"update_id": 1}, {"update_id": 2}]
        cliente = _ClienteFalso(resultado_get=actualizaciones_simuladas)

        # Act
        resultado = _ejecutar(_leer_actualizaciones(cliente, "token-falso", offset=None))

        # Assert
        assert resultado == actualizaciones_simuladas


class TestEnviarABff:
    """Pruebas de _enviar_a_bff (llamada a POST /mensajes de BFF)."""

    def test_envia_el_mensaje_tal_cual_a_bff(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """El mensaje ya traducido se reenvia sin modificarlo."""
        # Arrange
        monkeypatch.setattr(telegram_source, "_url_bff", lambda: "http://bff-falso")
        cliente = _ClienteFalso(status_post=202)
        mensaje = {
            "fuente": "telegram",
            "id_externo": "1_1",
            "texto": "prueba",
            "marca_temporal_origen": "2026-09-17T10:00:00+00:00",
            "autor_id_telegram": "1",
        }

        # Act
        _ejecutar(_enviar_a_bff(cliente, mensaje))

        # Assert
        url, cuerpo_enviado = cliente.peticiones_post[0]
        assert url == "http://bff-falso/mensajes"
        assert cuerpo_enviado == mensaje

    def test_un_error_de_bff_no_lanza_excepcion(self, capsys: pytest.CaptureFixture) -> None:
        """Si BFF responde 409/503, se registra en consola pero no se propaga el error."""
        # Arrange
        cliente = _ClienteFalso(status_post=409)
        mensaje = {
            "fuente": "telegram",
            "id_externo": "1_1",
            "texto": "prueba",
            "marca_temporal_origen": "2026-09-17T10:00:00+00:00",
            "autor_id_telegram": "1",
        }

        # Act
        _ejecutar(_enviar_a_bff(cliente, mensaje))

        # Assert
        assert "409" in capsys.readouterr().out


class TestTokenBot:
    """Pruebas de _token_bot (lectura de la variable de entorno)."""

    def test_lee_el_token_del_entorno(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Si la variable esta definida, se retorna su valor."""
        # Arrange
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token-de-prueba")

        # Act
        resultado = telegram_source._token_bot()

        # Assert
        assert resultado == "token-de-prueba"

    def test_falla_claramente_si_falta_la_variable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sin la variable definida, se lanza un error explicito (no un fallo silencioso)."""
        # Arrange
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        # El .env real del repo no debe repoblar la variable que acabamos de
        # borrar -- de lo contrario esta prueba dependeria del filesystem.
        monkeypatch.setattr(telegram_source, "load_dotenv", lambda: None)

        # Act / Assert
        with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
            telegram_source._token_bot()

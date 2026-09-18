"""Fuente de mensajes de Telegram para BFF.

Programa independiente (no es parte del servidor FastAPI de `bff.main`):
consulta periodicamente la API de Telegram mediante *long polling*
(`GET /getUpdates`) y, por cada mensaje de texto nuevo que un ciudadano le
escriba al bot, lo traduce al contrato de `POST /mensajes` (ver
docs/CONTRATOS_SISTEMA.md, seccion 1) y lo reenvia a BFF. Se ejecuta como su
propio proceso (`make run-telegram-source`), en paralelo a `make run-bff`.

Solo se procesan mensajes de texto: fotos, stickers, mensajes editados u
otros tipos de actualizacion se descartan sin tratarlos como error, ya que
el contrato de SIRENA no contempla adjuntos en esta version.
"""

import asyncio
import os
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

_INTERVALO_LARGO_POLLING_SEGUNDOS = 30.0


def _token_bot() -> str:
    """Lee el token del bot de Telegram desde el entorno.

    Antes de leer la variable, carga el `.env` de la raiz del repo (si
    existe) mediante `load_dotenv`, que no sobreescribe una variable ya
    definida en el entorno -- asi un valor exportado a mano sigue teniendo
    prioridad sobre el `.env`.

    Returns:
        El token entregado por BotFather al crear el bot.

    Raises:
        RuntimeError: si la variable de entorno no esta definida.

    """
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Falta la variable de entorno TELEGRAM_BOT_TOKEN "
            "(el token que entrega BotFather al crear el bot)"
        )
    return token


def _url_bff() -> str:
    """Lee la URL de BFF desde el entorno, con default para desarrollo local.

    Returns:
        La URL base del servicio BFF.

    """
    return os.environ.get("BFF_URL", "http://localhost:8000")


def _url_api_telegram(token: str) -> str:
    """Construye la URL base de la API de Telegram para este bot.

    Args:
        token: Token del bot entregado por BotFather.

    Returns:
        URL base para llamar a los metodos de la API de Telegram.

    """
    return f"https://api.telegram.org/bot{token}"


def _a_mensaje_entrante(actualizacion: dict) -> dict | None:
    """Traduce una actualizacion cruda de Telegram al contrato de POST /mensajes.

    `id_externo` combina el id del chat con el id del mensaje
    (`"{chat_id}_{message_id}"`) porque `message_id` de Telegram solo es
    unico dentro de un mismo chat, no globalmente -- la combinacion si lo es.

    Args:
        actualizacion: Un elemento de la lista `result` de GET /getUpdates.

    Returns:
        Un dict listo para enviar como cuerpo de POST /mensajes, o None si
        esta actualizacion no es un mensaje de texto que debamos procesar
        (ej. una foto, un sticker, o la edicion de un mensaje existente).

    """
    mensaje = actualizacion.get("message")
    if mensaje is None or "text" not in mensaje:
        return None

    chat_id = mensaje["chat"]["id"]
    message_id = mensaje["message_id"]
    autor_id = mensaje["from"]["id"]
    marca_temporal = datetime.fromtimestamp(mensaje["date"], tz=timezone.utc)

    return {
        "fuente": "telegram",
        "id_externo": f"{chat_id}_{message_id}",
        "texto": mensaje["text"],
        "marca_temporal_origen": marca_temporal.isoformat(),
        "autor_id_telegram": str(autor_id),
    }


async def _leer_actualizaciones(
    cliente: httpx.AsyncClient, token: str, offset: int | None
) -> list[dict]:
    """Consulta a Telegram las actualizaciones nuevas desde `offset`.

    Usa *long polling*: la peticion a Telegram queda abierta hasta
    `_INTERVALO_LARGO_POLLING_SEGUNDOS` esperando a que llegue un mensaje
    nuevo, en vez de preguntar en un bucle ajustado sin esperar respuesta
    -- mas eficiente y es el patron que la propia documentacion de Telegram
    recomienda para bots que no usan webhook.

    Args:
        cliente: Cliente HTTP reutilizado entre llamadas.
        token: Token del bot.
        offset: `update_id` desde el cual pedir actualizaciones nuevas
            (None en la primera llamada, para no arrastrar mensajes viejos
            que ya estaban pendientes antes de que este programa arrancara).

    Returns:
        La lista de actualizaciones nuevas (puede estar vacia si no llego
        nada durante la espera).

    """
    parametros: dict[str, int] = {"timeout": int(_INTERVALO_LARGO_POLLING_SEGUNDOS)}
    if offset is not None:
        parametros["offset"] = offset

    respuesta = await cliente.get(
        f"{_url_api_telegram(token)}/getUpdates",
        params=parametros,
        timeout=_INTERVALO_LARGO_POLLING_SEGUNDOS + 5.0,
    )
    respuesta.raise_for_status()
    return respuesta.json()["result"]


async def _enviar_a_bff(cliente: httpx.AsyncClient, mensaje: dict) -> None:
    """Reenvia un mensaje ya traducido a POST /mensajes de BFF.

    Los errores de BFF (400/409/503) se registran en consola pero no
    detienen el bucle principal -- un mensaje problematico no debe tumbar
    la fuente completa; el resto de mensajes debe seguir procesandose.

    Args:
        cliente: Cliente HTTP reutilizado entre llamadas.
        mensaje: Cuerpo ya en el formato de POST /mensajes.

    """
    respuesta = await cliente.post(f"{_url_bff()}/mensajes", json=mensaje)
    if respuesta.status_code >= 400:
        print(
            f"BFF rechazo el mensaje {mensaje['id_externo']}: "
            f"{respuesta.status_code} {respuesta.text}"
        )


async def ejecutar() -> None:
    """Bucle principal: escucha Telegram y reenvia cada mensaje a BFF.

    Corre indefinidamente (se detiene con Ctrl+C) -- no es un servicio
    FastAPI como los demas, es un proceso de fondo que alimenta a BFF con
    mensajes reales de ciudadanos.

    """
    token = _token_bot()
    offset: int | None = None

    async with httpx.AsyncClient() as cliente:
        print("Fuente de Telegram activa, esperando mensajes...")
        while True:
            actualizaciones = await _leer_actualizaciones(cliente, token, offset)
            for actualizacion in actualizaciones:
                offset = actualizacion["update_id"] + 1
                mensaje = _a_mensaje_entrante(actualizacion)
                if mensaje is not None:
                    print(f"Mensaje recibido de Telegram: {mensaje['texto']!r}")
                    await _enviar_a_bff(cliente, mensaje)


if __name__ == "__main__":
    asyncio.run(ejecutar())

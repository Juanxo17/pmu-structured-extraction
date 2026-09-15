"""Orquestador del pipeline de dos etapas.

Coordina, para un mensaje ciudadano, el flujo completo descrito en
docs/CONTRATOS_SISTEMA.md (seccion 3): anonimizacion -> compuerta
(Inference) -> extraccion (Inference, solo si el mensaje es accionable) ->
resolucion geografica (Geo) -> persistencia (CRUD).

La deteccion de duplicados depende de la normalizacion geografica
determinista (que a su vez depende de este mismo orquestador ya construido),
asi que no esta implementada todavia -- se agrega en una iteracion
posterior sin cambiar la forma de esta funcion. El parametro `mensaje_id`
ya se recibe hoy para no tener que cambiar la firma cuando esa deteccion
se agregue.

Motivos de descarte (valores fijos, no texto libre improvisado en cada
punto del codigo -- asi se puede filtrar o contar descartes por causa):
- "no_accionable": la compuerta de Inference determino que el mensaje no
  amerita estructurarse.
- "fallo_validacion_extraccion": Inference agoto sus reintentos internos y
  la salida del modelo nunca conformo al esquema esperado (responde 422).
"""

import hashlib
import os

import httpx

from process.anonimizacion import anonimizar_texto

MOTIVO_NO_ACCIONABLE = "no_accionable"
MOTIVO_FALLO_VALIDACION_EXTRACCION = "fallo_validacion_extraccion"


def _url_inference() -> str:
    """Lee la URL de Inference desde el entorno, con default para desarrollo local.

    Returns:
        La URL base del servicio Inference.

    """
    return os.environ.get("INFERENCE_URL", "http://localhost:8003")


def _url_geo() -> str:
    """Lee la URL de Geo desde el entorno, con default para desarrollo local.

    Returns:
        La URL base del servicio Geo.

    """
    return os.environ.get("GEO_URL", "http://localhost:8004")


def _url_crud() -> str:
    """Lee la URL de CRUD desde el entorno, con default para desarrollo local.

    Returns:
        La URL base del servicio CRUD.

    """
    return os.environ.get("CRUD_URL", "http://localhost:8001")


def _anonimizar_autor(autor_id_telegram: str) -> str:
    """Pseudonimiza el ID de autor de Telegram.

    A diferencia del texto del mensaje (supresion con marcador fijo, ver
    anonimizacion.py), aqui se necesita un pseudonimo *consistente*: el
    mismo autor debe producir siempre el mismo `autor_anonimizado_id`, para
    que el operador pueda notar "varios reportes de la misma persona" sin
    conocer su identidad real. Un hash criptografico logra eso: mismo
    input, siempre el mismo output, y no es reversible hacia el ID original.

    Args:
        autor_id_telegram: ID de la cuenta de Telegram que envio el mensaje.

    Returns:
        Un pseudonimo estable derivado de ese ID.

    """
    return hashlib.sha256(autor_id_telegram.encode()).hexdigest()[:16]


async def _llamar_compuerta(cliente: httpx.AsyncClient, texto: str) -> dict:
    """Llama a Inference para clasificar si el mensaje es accionable.

    Args:
        cliente: Cliente HTTP async reutilizado para todo el pipeline.
        texto: Texto ya anonimizado.

    Returns:
        El JSON de respuesta (campos de Compuerta).

    """
    respuesta = await cliente.post(f"{_url_inference()}/compuerta", json={"texto": texto})
    respuesta.raise_for_status()
    return respuesta.json()


async def _llamar_extraccion(cliente: httpx.AsyncClient, texto: str) -> dict | None:
    """Llama a Inference para extraer naturaleza y ubicacion del mensaje.

    Args:
        cliente: Cliente HTTP async reutilizado para todo el pipeline.
        texto: Texto ya anonimizado.

    Returns:
        El JSON de respuesta (naturaleza y ubicacion), o None si Inference
        agoto sus reintentos de validacion (422).

    """
    respuesta = await cliente.post(f"{_url_inference()}/extraccion", json={"texto": texto})
    if respuesta.status_code == 422:
        return None
    respuesta.raise_for_status()
    return respuesta.json()


async def _llamar_geo(
    cliente: httpx.AsyncClient, ubicacion_texto_literal: str, punto_referencia: str | None
) -> dict:
    """Llama a Geo para resolver barrio/comuna a partir del texto de ubicacion.

    Args:
        cliente: Cliente HTTP async reutilizado para todo el pipeline.
        ubicacion_texto_literal: Texto de ubicacion tal como lo extrajo Inference.
        punto_referencia: Punto de referencia adicional, si Inference lo extrajo.

    Returns:
        El JSON de respuesta (barrio, comuna, nivel_granularidad).

    """
    respuesta = await cliente.post(
        f"{_url_geo()}/resolver",
        json={
            "ubicacion_texto_literal": ubicacion_texto_literal,
            "punto_referencia": punto_referencia,
        },
    )
    respuesta.raise_for_status()
    return respuesta.json()


async def _persistir_reporte(cliente: httpx.AsyncClient, reporte: dict) -> dict:
    """Llama a CRUD para persistir el reporte estructurado final.

    Args:
        cliente: Cliente HTTP async reutilizado para todo el pipeline.
        reporte: ReporteEstructurado sin id ni creado_en (los asigna CRUD).

    Returns:
        El JSON de respuesta: el ReporteEstructurado completo, con id y creado_en.

    """
    respuesta = await cliente.post(f"{_url_crud()}/reportes", json=reporte)
    respuesta.raise_for_status()
    return respuesta.json()


async def procesar_mensaje(
    mensaje_id: str,
    texto_crudo: str,
    fuente: str,
    id_externo: str,
    autor_id_telegram: str,
) -> dict:
    """Orquesta el pipeline completo para un mensaje ciudadano.

    Args:
        mensaje_id: Identificador interno de esta llamada (reservado para
            la deteccion de duplicados, todavia no implementada).
        texto_crudo: Texto del mensaje tal como llego de la fuente.
        fuente: Plataforma de origen (ej. "telegram"), ya validada por BFF.
        id_externo: ID del mensaje en la plataforma de origen.
        autor_id_telegram: ID de la cuenta que envio el mensaje.

    Returns:
        `{"estado": "estructurado", "reporte": ReporteEstructurado}` si el
        mensaje se proceso completo, o `{"estado": "descartado", "motivo": str}`
        si no era accionable o si Inference no logro validar su extraccion.

    """
    texto_anonimizado = anonimizar_texto(texto_crudo)
    autor_anonimizado_id = _anonimizar_autor(autor_id_telegram)

    async with httpx.AsyncClient() as cliente:
        compuerta = await _llamar_compuerta(cliente, texto_anonimizado)

        if not compuerta["es_reporte_accionable"]:
            return {"estado": "descartado", "motivo": MOTIVO_NO_ACCIONABLE}

        extraccion = await _llamar_extraccion(cliente, texto_anonimizado)
        if extraccion is None:
            return {"estado": "descartado", "motivo": MOTIVO_FALLO_VALIDACION_EXTRACCION}

        naturaleza = extraccion["naturaleza"]
        ubicacion_extraida = extraccion["ubicacion"]

        geo = await _llamar_geo(
            cliente,
            ubicacion_extraida["ubicacion_texto_literal"],
            ubicacion_extraida.get("punto_referencia"),
        )

        ubicacion = {
            "ubicacion_texto_literal": ubicacion_extraida["ubicacion_texto_literal"],
            "punto_referencia": ubicacion_extraida.get("punto_referencia"),
            "barrio": geo["barrio"],
            "comuna": geo["comuna"],
            "nivel_granularidad": geo["nivel_granularidad"],
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
        }

        reporte_sin_id = {
            "fuente": fuente,
            "id_externo": id_externo,
            "autor_anonimizado_id": autor_anonimizado_id,
            "mensaje_anonimizado": texto_anonimizado,
            "estado_revision": "pendiente",
            "compuerta": compuerta,
            "naturaleza": naturaleza,
            "ubicacion": ubicacion,
        }

        reporte_persistido = await _persistir_reporte(cliente, reporte_sin_id)

    return {"estado": "estructurado", "reporte": reporte_persistido}
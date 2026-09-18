"""Orquestador del pipeline de dos etapas.

Coordina, para un mensaje ciudadano, el flujo completo descrito en
docs/CONTRATOS_SISTEMA.md (seccion 3): anonimizacion -> compuerta
(Inference) -> extraccion (Inference, solo si el mensaje es accionable) ->
resolucion geografica (Geo) -> deteccion basica de posible duplicado ->
persistencia (CRUD).

La deteccion de posible duplicado NUNCA descarta el mensaje: reportes
distintos de personas distintas sobre el mismo evento real son corroboracion
que refuerza la importancia del evento, no ruido. El mensaje se sigue
procesando y persistiendo igual; lo unico que cambia es que la respuesta
puede incluir `motivo=MOTIVO_DUPLICADO` junto al reporte ya guardado -- una
senal para el operador humano, no una decision automatica de descarte.

"Descarte" no significa "no se guarda": un mensaje descartado se persiste
igual (con `naturaleza`/`ubicacion` en `None`), solo que la respuesta trae
`estado="descartado"` en vez de `"estructurado"` -- filtrarlo de la bandeja
por defecto es responsabilidad del frontend (campo `accionable`), no de
Process, para que un operador pueda revisar manualmente lo que el modelo
descarto y detectar falsos negativos.

Motivos de descarte (valores fijos, no texto libre improvisado en cada
punto del codigo -- asi se puede filtrar o contar descartes por causa):
- "no_accionable": la compuerta de Inference determino que el mensaje no
  amerita estructurarse.
- "fallo_validacion_extraccion": Inference agoto sus reintentos internos y
  la salida del modelo nunca conformo al esquema esperado (responde 422).

`MOTIVO_DUPLICADO` no es un motivo de descarte (el mensaje si se persiste),
pero comparte la misma taxonomia de valores fijos por la misma razon: poder
filtrar o contar casos por causa sin depender de texto libre.
"""

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx

from process.anonimizacion import anonimizar_texto

MOTIVO_NO_ACCIONABLE = "no_accionable"
MOTIVO_FALLO_VALIDACION_EXTRACCION = "fallo_validacion_extraccion"
MOTIVO_DUPLICADO = "duplicado"

_VENTANA_POSIBLE_DUPLICADO_MINUTOS = 15


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
        reporte: ReporteEstructurado completo, con `id` (uuid4) y `creado_en`
            (momento de persistencia) ya asignados por Process -- CRUD no
            genera estos campos, solo los guarda tal como llegan.

    Returns:
        El JSON de respuesta: el ReporteEstructurado tal como quedo persistido.

    """
    respuesta = await cliente.post(f"{_url_crud()}/reportes", json=reporte)
    respuesta.raise_for_status()
    return respuesta.json()


def _misma_ubicacion(barrio_nuevo: str | None, candidato: dict) -> bool:
    """Compara la ubicacion de un reporte candidato con la del reporte nuevo.

    Usa `barrio` para mayor precision cuando AMBOS reportes lo tienen
    resuelto. Si a cualquiera de los dos le falta (Geo solo alcanzo a
    resolver `comuna`), se considera la misma ubicacion igual -- el
    candidato ya viene filtrado por `comuna` desde CRUD (ver
    `_buscar_posible_duplicado`), asi que la comuna ya coincide.

    Args:
        barrio_nuevo: Barrio ya resuelto por Geo para el reporte nuevo
            (None si Geo no llego a ese nivel de precision).
        candidato: Reporte existente devuelto por CRUD.

    Returns:
        True si ambos reportes se consideran la misma ubicacion.

    """
    barrio_candidato = candidato["barrio"]
    if barrio_nuevo is not None and barrio_candidato is not None:
        return barrio_nuevo == barrio_candidato
    return True


def _dentro_de_la_ventana(creado_en_candidato: str, ahora: datetime) -> bool:
    """Verifica si `creado_en` del candidato cae dentro de la ventana de duplicado.

    Se usa `creado_en` (momento en que CRUD persistio el candidato) como
    aproximacion del momento del evento, porque `marca_temporal_origen` del
    mensaje del ciudadano no llega hoy hasta Process (ver
    docs/CONTRATOS_SISTEMA.md, seccion 3).

    Args:
        creado_en_candidato: Marca de tiempo ISO 8601 que CRUD le asigno al candidato.
        ahora: Momento de referencia para el reporte nuevo -- todavia no
            tiene `creado_en` propio porque no se ha persistido.

    Returns:
        True si la diferencia absoluta con `ahora` no supera la ventana
        configurada (`_VENTANA_POSIBLE_DUPLICADO_MINUTOS`).

    """
    momento_candidato = datetime.fromisoformat(creado_en_candidato)
    if momento_candidato.tzinfo is None:
        momento_candidato = momento_candidato.replace(tzinfo=timezone.utc)
    return abs(ahora - momento_candidato) <= timedelta(minutes=_VENTANA_POSIBLE_DUPLICADO_MINUTOS)


async def _buscar_posible_duplicado(
    cliente: httpx.AsyncClient, tipo_evento: str, comuna: str | None, barrio: str | None
) -> bool:
    """Busca en CRUD si ya existe un reporte que se considere el mismo evento.

    Deteccion basica: nunca decide descartar el mensaje (ver el docstring
    del modulo) -- solo determina si la respuesta de `procesar_mensaje` debe
    incluir `motivo=MOTIVO_DUPLICADO` junto al reporte, que de todas formas
    se persiste igual que cualquier otro.

    Criterios (los tres deben cumplirse en algun reporte existente):
    1. Mismo `tipo_evento`.
    2. Misma ubicacion (ver `_misma_ubicacion`: `barrio` cuando ambos lo
       tienen, `comuna` como respaldo si a alguno le falta).
    3. `creado_en` dentro de la ventana de tiempo configurada (ver
       `_dentro_de_la_ventana`).

    Sin `comuna` resuelta (Geo no logro ubicar el mensaje en absoluto) no
    hay nada confiable con que comparar, asi que no se busca.

    Args:
        cliente: Cliente HTTP async reutilizado para todo el pipeline.
        tipo_evento: Tipo de evento ya extraido para el reporte nuevo.
        comuna: Comuna ya resuelta por Geo para el reporte nuevo.
        barrio: Barrio ya resuelto por Geo para el reporte nuevo (puede ser None).

    Returns:
        True si se encontro al menos un reporte existente que cumple los
        tres criterios.

    """
    if comuna is None:
        return False

    respuesta = await cliente.get(
        f"{_url_crud()}/reportes",
        params={"tipo_evento": tipo_evento, "comuna": comuna},
    )
    respuesta.raise_for_status()
    candidatos = respuesta.json()["resultados"]

    ahora = datetime.now(timezone.utc)
    return any(
        _misma_ubicacion(barrio, candidato) and _dentro_de_la_ventana(candidato["creado_en"], ahora)
        for candidato in candidatos
    )


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
            uso futuro; la deteccion de posible duplicado de esta version
            compara por tipo de evento, ubicacion y tiempo, no por este id).
        texto_crudo: Texto del mensaje tal como llego de la fuente.
        fuente: Plataforma de origen (ej. "telegram"), ya validada por BFF.
        id_externo: ID del mensaje en la plataforma de origen.
        autor_id_telegram: ID de la cuenta que envio el mensaje.

    Returns:
        `{"estado": "estructurado", "reporte": ReporteEstructurado}` si el
        mensaje se proceso completo (con `"motivo": MOTIVO_DUPLICADO`
        agregado si ademas se detecto un posible duplicado -- el reporte se
        persiste igual, esto es solo una senal para el operador), o
        `{"estado": "descartado", "motivo": str, "reporte": ReporteEstructurado}`
        si no era accionable o si Inference no logro validar su extraccion.
        En ambos casos el reporte se persiste: los mensajes no accionables o
        no estructurables no se filtran aqui, quedan en la bandeja con
        `naturaleza`/`ubicacion` en `None` (ver
        `ReporteEstructurado._normalizar_no_accionable`) para que el
        operador los descarte desde el frontend, que ya filtra por
        `accionable`.

    """
    texto_anonimizado = anonimizar_texto(texto_crudo)
    autor_anonimizado_id = _anonimizar_autor(autor_id_telegram)

    reporte_base = {
        "id": uuid.uuid4().hex,
        "fuente": fuente,
        "id_externo": id_externo,
        "autor_anonimizado_id": autor_anonimizado_id,
        "mensaje_anonimizado": texto_anonimizado,
        "estado_revision": "pendiente",
        "creado_en": datetime.now(timezone.utc).isoformat(),
    }

    async with httpx.AsyncClient() as cliente:
        compuerta = await _llamar_compuerta(cliente, texto_anonimizado)

        if not compuerta["es_reporte_accionable"]:
            reporte_persistido = await _persistir_reporte(
                cliente,
                {**reporte_base, "compuerta": compuerta, "naturaleza": None, "ubicacion": None},
            )
            return {
                "estado": "descartado",
                "motivo": MOTIVO_NO_ACCIONABLE,
                "reporte": reporte_persistido,
            }

        extraccion = await _llamar_extraccion(cliente, texto_anonimizado)
        if extraccion is None:
            reporte_persistido = await _persistir_reporte(
                cliente,
                {**reporte_base, "compuerta": compuerta, "naturaleza": None, "ubicacion": None},
            )
            return {
                "estado": "descartado",
                "motivo": MOTIVO_FALLO_VALIDACION_EXTRACCION,
                "reporte": reporte_persistido,
            }

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

        es_posible_duplicado = await _buscar_posible_duplicado(
            cliente, naturaleza["tipo_evento"], geo["comuna"], geo["barrio"]
        )

        reporte_persistido = await _persistir_reporte(
            cliente,
            {
                **reporte_base,
                "compuerta": compuerta,
                "naturaleza": naturaleza,
                "ubicacion": ubicacion,
            },
        )

    resultado = {"estado": "estructurado", "reporte": reporte_persistido}
    if es_posible_duplicado:
        resultado["motivo"] = MOTIVO_DUPLICADO
    return resultado

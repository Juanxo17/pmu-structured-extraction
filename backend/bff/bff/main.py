"""Punto de entrada FastAPI del servicio BFF.

BFF es un *gateway* puro (ver docs/CONTRATOS_SISTEMA.md, seccion 1): expone
`POST /mensajes` (recibe un reporte ciudadano y dispara el pipeline en
Process sin esperarlo) y reenvia el resto de endpoints directamente a CRUD,
sin logica de negocio propia.

Limitacion conocida: el contrato de `POST /mensajes` contempla un `503`
cuando el pipeline esta saturado (cuota de Groq agotada en Inference). Como
la llamada a Process se despacha en segundo plano (fire-and-forget) para no
bloquear la respuesta al cliente, BFF nunca espera el resultado del
pipeline y por lo tanto no puede saber si Inference esta saturado en el
momento de responder -- esa parte del 503 queda pendiente de resolver junto
con el equipo, cuando se defina como Inference/Process senalizan saturacion
hacia arriba en la cadena. Lo que si se verifica hoy es que Process mismo
este alcanzable (ver `_proceso_disponible`): un 503 aqui cubre "el pipeline
no esta arriba", no "el pipeline esta saturado" -- son dos causas distintas
del mismo status code, y solo la primera es verificable sin esperar el
pipeline completo.
"""

import os
from datetime import datetime
from typing import Literal

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

_TIMEOUT_CHEQUEO_SALUD_SEGUNDOS = 2.0

app = FastAPI(title="SIRENA - BFF")


class MensajeEntrante(BaseModel):
    """Cuerpo de la peticion POST /mensajes (ver docs/CONTRATOS_SISTEMA.md, seccion 1).

    `autor_id_telegram` no estaba en el contrato original de BFF, pero es
    necesario para que Process pueda pseudonimizar al autor (ver el
    contrato extendido de `POST /procesar` en Process) -- se agrega aqui
    por la misma razon: sin este campo, BFF no tendria nada que reenviarle
    a Process.
    """

    fuente: Literal["telegram"]
    id_externo: str
    texto: str
    marca_temporal_origen: datetime
    autor_id_telegram: str


def _url_crud() -> str:
    """Lee la URL de CRUD desde el entorno, con default para desarrollo local.

    Returns:
        La URL base del servicio CRUD.

    """
    return os.environ.get("CRUD_URL", "http://localhost:8001")


def _url_process() -> str:
    """Lee la URL de Process desde el entorno, con default para desarrollo local.

    Returns:
        La URL base del servicio Process.

    """
    return os.environ.get("PROCESS_URL", "http://localhost:8002")


async def _reenviar_get(
    ruta: str, parametros: dict[str, str] | list[tuple[str, str]]
) -> tuple[int, dict]:
    """Reenvia un GET a CRUD y retorna su status code y cuerpo, tal cual.

    Acepta tanto un dict como una lista de tuplas para `parametros` porque
    algunos filtros (ej. `servicio_de_respuesta`) son repetibles -- un dict
    de Python no puede tener la misma llave dos veces, asi que un query
    string como `?servicio_de_respuesta=bomberos&servicio_de_respuesta=policia`
    necesita representarse como lista de tuplas para no perder valores.

    Args:
        ruta: Ruta de CRUD a llamar (ej. "/reportes").
        parametros: Query params a reenviar.

    Returns:
        Una tupla (status_code, cuerpo_json) con la respuesta de CRUD sin modificar.

    """
    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.get(f"{_url_crud()}{ruta}", params=parametros)
    return respuesta.status_code, respuesta.json()


async def _reenviar_patch(ruta: str, cuerpo: dict) -> tuple[int, dict]:
    """Reenvia un PATCH a CRUD y retorna su status code y cuerpo, tal cual.

    Args:
        ruta: Ruta de CRUD a llamar (ej. "/reportes/abc123").
        cuerpo: Cuerpo JSON a reenviar.

    Returns:
        Una tupla (status_code, cuerpo_json) con la respuesta de CRUD sin modificar.

    """
    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.patch(f"{_url_crud()}{ruta}", json=cuerpo)
    return respuesta.status_code, respuesta.json()


async def _existe_duplicado(fuente: str, id_externo: str) -> bool:
    """Consulta a CRUD si ya existe un reporte con esta fuente + id_externo.

    Este es el chequeo de idempotencia de transporte (mismo mensaje
    reenviado, ej. por un reintento de Telegram) -- no tiene relacion con
    la deteccion de duplicados por contenido (T-17, pendiente), que es un
    problema distinto y deliberadamente separado (ver discusion en la
    bitacora del proyecto).

    Args:
        fuente: Plataforma de origen del mensaje.
        id_externo: ID del mensaje en esa plataforma.

    Returns:
        True si ya existe un reporte con esa combinacion fuente + id_externo.

    """
    _, cuerpo = await _reenviar_get("/reportes", {"fuente": fuente, "id_externo": id_externo})
    return cuerpo["total"] > 0


async def _proceso_disponible() -> bool:
    """Verifica que Process este alcanzable antes de aceptar el mensaje.

    Esta es la parte verificable hoy del `503` del contrato (ver
    limitacion conocida al inicio del modulo): no cubre que Inference este
    saturado (eso ocurre rio abajo, despues de que BFF ya respondio), pero
    si cubre que Process ni siquiera este arriba -- un timeout corto evita
    que este chequeo retrase la respuesta al cliente de forma perceptible.

    Returns:
        True si Process responde a su `/health` dentro del timeout.

    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_CHEQUEO_SALUD_SEGUNDOS) as cliente:
            respuesta = await cliente.get(f"{_url_process()}/health")
    except httpx.HTTPError:
        return False
    return respuesta.status_code == 200


async def _disparar_procesamiento(mensaje: MensajeEntrante) -> None:
    """Llama a Process para procesar el mensaje, sin que el cliente lo espere.

    Se ejecuta como tarea en segundo plano (ver BackgroundTasks en
    `recibir_mensaje`): FastAPI la corre despues de enviar el 202 al
    cliente, no antes. Si esta llamada falla, no hay forma de avisarle al
    cliente (ya recibio su 202) -- por eso el chequeo de duplicado y la
    validacion del cuerpo se hacen ANTES de responder, no aqui.

    Args:
        mensaje: El mensaje ya validado, listo para reenviar a Process.

    """
    async with httpx.AsyncClient() as cliente:
        await cliente.post(
            f"{_url_process()}/procesar",
            json={
                "mensaje_id": mensaje.id_externo,
                "texto_crudo": mensaje.texto,
                "fuente": mensaje.fuente,
                "id_externo": mensaje.id_externo,
                "autor_id_telegram": mensaje.autor_id_telegram,
            },
        )


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que el servicio esta activo.

    Returns:
        Estado del servicio.

    """
    return {"status": "ok"}


@app.post("/mensajes", status_code=202)
async def recibir_mensaje(peticion: Request, tareas_en_segundo_plano: BackgroundTasks) -> dict:
    """Recibe un mensaje ciudadano y dispara el pipeline en Process.

    No se usa el tipado automatico de FastAPI (`peticion: MensajeEntrante`)
    porque el contrato exige `400` cuando falta un campo obligatorio, y el
    422 automatico de FastAPI/Pydantic no coincide con eso -- se valida a
    mano para controlar el status code exacto.

    Args:
        peticion: La peticion HTTP cruda (para leer y validar el cuerpo a mano).
        tareas_en_segundo_plano: Mecanismo de FastAPI para ejecutar
            `_disparar_procesamiento` despues de responder al cliente.

    Returns:
        `{"id_mensaje": str, "estado": "recibido"}`.

    Raises:
        HTTPException: 400 si el cuerpo no es JSON valido o falta un campo
            obligatorio; 409 si `fuente` + `id_externo` ya fueron recibidos
            antes; 503 si Process no esta alcanzable.

    """
    try:
        cuerpo = await peticion.json()
        mensaje = MensajeEntrante.model_validate(cuerpo)
    except (ValueError, ValidationError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if await _existe_duplicado(mensaje.fuente, mensaje.id_externo):
        raise HTTPException(status_code=409, detail="mensaje ya recibido")

    if not await _proceso_disponible():
        raise HTTPException(status_code=503, detail="pipeline no disponible, intenta de nuevo")

    tareas_en_segundo_plano.add_task(_disparar_procesamiento, mensaje)
    return {"id_mensaje": mensaje.id_externo, "estado": "recibido"}


@app.get("/reportes")
async def listar_reportes(request: Request) -> JSONResponse:
    """Proxy directo hacia GET /reportes de CRUD (bandeja del tablero, T-22).

    Args:
        request: La peticion HTTP, de donde se toman los filtros/paginacion tal cual.

    Returns:
        La respuesta de CRUD, sin modificar.

    """
    status, cuerpo = await _reenviar_get("/reportes", list(request.query_params.multi_items()))
    return JSONResponse(status_code=status, content=cuerpo)


@app.get("/reportes/resumen")
async def resumen_reportes(request: Request) -> JSONResponse:
    """Proxy directo hacia GET /reportes/resumen de CRUD (tarjetas del encabezado).

    Args:
        request: La peticion HTTP, de donde se toman `desde`/`hasta` tal cual.

    Returns:
        La respuesta de CRUD, sin modificar.

    """
    status, cuerpo = await _reenviar_get(
        "/reportes/resumen", list(request.query_params.multi_items())
    )
    return JSONResponse(status_code=status, content=cuerpo)


@app.get("/reportes/{id_reporte}")
async def obtener_reporte(id_reporte: str) -> JSONResponse:
    """Proxy directo hacia GET /reportes/{id} de CRUD (vista de detalle, T-23).

    Args:
        id_reporte: ID del reporte a consultar.

    Returns:
        La respuesta de CRUD, sin modificar (200 o 404).

    """
    status, cuerpo = await _reenviar_get(f"/reportes/{id_reporte}", {})
    return JSONResponse(status_code=status, content=cuerpo)


@app.patch("/reportes/{id_reporte}")
async def corregir_reporte(id_reporte: str, request: Request) -> JSONResponse:
    """Proxy directo hacia PATCH /reportes/{id} de CRUD (triaje asistido).

    Args:
        id_reporte: ID del reporte a corregir.
        request: La peticion HTTP, de donde se toma el cuerpo tal cual.

    Returns:
        La respuesta de CRUD, sin modificar (200, 404 o 422).

    """
    cuerpo_peticion = await request.json()
    status, cuerpo = await _reenviar_patch(f"/reportes/{id_reporte}", cuerpo_peticion)
    return JSONResponse(status_code=status, content=cuerpo)

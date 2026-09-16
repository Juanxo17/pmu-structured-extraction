"""Instrucciones de sistema de las dos etapas de inferencia.

El vocabulario vigente se inyecta desde la ontologia (config/ontologia.yaml)
para que el modelo solo genere valores admitidos por el esquema compartido.
"""

from typing import get_args

from sirena_schema.ontologia import ONTOLOGIA
from sirena_schema.schema import Compuerta

_ETIQUETAS_SERVICIO = (
    "A Busqueda y Rescate, B Extincion de Incendios, "
    "C Telecomunicaciones para la comunidad, D Manejo de Materiales Peligrosos, "
    "E Seguridad y Convivencia, F Accesibilidad y Transporte, G Salud, "
    "H Agua Potable, I Asistencia Humanitaria, J Alojamientos Temporales, "
    "K Energia y Gas, L Saneamiento Basico, M Reencuentro Familiar, "
    "N Fauna Domestica, O Fauna Silvestre, R Manejo de Residuos Solidos"
)


def _valores_literal(campo: str) -> str:
    """Devuelve los valores admitidos por un campo Literal del esquema.

    Args:
        campo: Nombre del campo Literal de Compuerta.

    Returns:
        Valores separados por comas, en el orden del esquema.

    """
    anotacion = Compuerta.model_fields[campo].annotation
    valores: tuple[str, ...] = tuple(get_args(anotacion))
    return ", ".join(valores)


def sistema_compuerta() -> str:
    """Devuelve las instrucciones de sistema de la etapa de compuerta.

    Returns:
        Instrucciones que piden clasificar accionabilidad, temporalidad
        e intencion, enumerando los valores admitidos por el esquema.

    """
    temporalidades = _valores_literal("temporalidad")
    intenciones = _valores_literal("intencion")
    return (
        "Eres el primer filtro de un sistema de reportes ciudadanos de "
        "emergencia (SIRENA). Recibes el texto de un mensaje y decides si es "
        "un reporte accionable, su temporalidad y la intencion de quien escribe.\n\n"
        "Responde SOLO con un JSON valido, sin texto adicional, con la forma: "
        '{"es_reporte_accionable": true o false, "temporalidad": "...", '
        '"intencion": "..."}.\n\n'
        f"Valores permitidos para temporalidad: {temporalidades}.\n"
        f"Valores permitidos para intencion: {intenciones}.\n\n"
        "Criterios de clasificacion:\n"
        "- Un reporte accionable describe una emergencia vigente, en curso o "
        "imminente que puede requerir atencion de servicios de respuesta.\n"
        "- Un mensaje de apoyo, condolencias, noticia no urgente o que no "
        "describe una emergencia activa NO es accionable y sus otros campos "
        "se marcan sensatamente o se omite la extraccion.\n"
        "- riesgo_previsto: advierte de un peligro que puede ocurrir.\n"
        "- ya_ocurrio: describe hechos que ya pasaron, sin urgencia vigente.\n"
        "- solicita_ayuda: pide asistencia para si mismo o su comunidad.\n"
        "- reporta_terceros: informa sobre afectaciones de otras personas.\n"
        "- ofrece_ayuda: pone a disposicion recursos o ayuda.\n"
        "- solicita_informacion: pide datos o aclaraciones sin reportar una "
        "emergencia en curso."
    )


def sistema_extraccion() -> str:
    """Devuelve las instrucciones de sistema de la etapa de extraccion.

    Returns:
        Instrucciones que piden el JSON de naturaleza y ubicacion, con la
        ontologia vigente de tipo_evento y servicio_de_respuesta.

    """
    tipos = ", ".join(sorted(ONTOLOGIA.tipos_evento))
    return (
        "Eres el extractor de un sistema de reportes ciudadanos de emergencia "
        "(SIRENA). Recibes el texto de un mensaje ya clasificado como "
        "accionable y extraes la naturaleza del evento y su ubicacion.\n\n"
        "Responde SOLO con un JSON valido, sin texto adicional, con la forma: "
        '{"naturaleza": {"tipo_evento": "...", "servicio_de_respuesta": '
        '["..."]}, "ubicacion": {"ubicacion_texto_literal": "...", '
        '"barrio": null o "...", "comuna": null o "...", '
        '"punto_referencia": null o "...", "nivel_granularidad": "..."}}.\n\n'
        f"Valores permitidos para tipo_evento: {tipos}.\n"
        f"Codigos permitidos para servicio_de_respuesta (uno o mas): "
        f"{_ETIQUETAS_SERVICIO}.\n\n"
        "Reglas:\n"
        "- tipo_evento debe ser exactamente uno de los valores permitidos.\n"
        "- servicio_de_respuesta es una lista con los codigos de los servicios "
        "que el mensaje justifica; usa cero o mas, no inventes codigos.\n"
        "- Completa TODOS los campos de ubicacion que el mensaje aporte; "
        "si algo no se menciona, usa null.\n"
        "- nivel_granularidad describe cuanto se puede ubicar el evento: "
        "exacta si hay direccion o punto, barrio, comuna, ciudad si el "
        "mensaje solo nombra la ciudad, o indeterminada si no hay datos.\n"
        "- Las coordenadas no se piden aqui: solo texto y nombres de lugar."
    )
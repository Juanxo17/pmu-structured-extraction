"""Instrucciones de sistema de las dos etapas de inferencia.

El vocabulario vigente se inyecta desde la ontologia (config/ontologia.yaml)
para que el modelo solo genere valores admitidos por el esquema compartido.
"""

from typing import get_args

from sirena_schema.ontologia import ONTOLOGIA
from sirena_schema.schema import Compuerta

VERSION_PROMPTS = "1.1"

_NOMBRES_SERVICIO = {
    "A": "Busqueda y Rescate",
    "B": "Extincion de Incendios",
    "C": "Telecomunicaciones para la comunidad",
    "D": "Manejo de Materiales Peligrosos",
    "E": "Seguridad y Convivencia",
    "F": "Accesibilidad y Transporte",
    "G": "Salud",
    "H": "Agua Potable",
    "I": "Asistencia Humanitaria",
    "J": "Alojamientos Temporales",
    "K": "Energia y Gas",
    "L": "Saneamiento Basico",
    "M": "Reencuentro Familiar",
    "N": "Fauna Domestica",
    "O": "Fauna Silvestre",
    "R": "Manejo de Residuos Solidos",
}

_EJEMPLOS_COMPUERTA = (
    (
        "Hay una inundacion en la carrera 5 con 12, el agua ya cubre la calle "
        "y los carros no pueden pasar.",
        '{"es_reporte_accionable": true, "temporalidad": "ocurriendo_ahora", '
        '"intencion": "reporta_terceros"}',
    ),
    (
        "El rio Cauca esta creciendo y puede desbordarse esta noche, por favor preparense.",
        '{"es_reporte_accionable": true, "temporalidad": "riesgo_previsto", '
        '"intencion": "reporta_terceros"}',
    ),
    (
        "Saben a que hora pasa el bus en el barrio El Poblado?",
        '{"es_reporte_accionable": false, "temporalidad": "referencia_noticia", '
        '"intencion": "solicita_informacion"}',
    ),
)

_EJEMPLOS_EXTRACCION = (
    (
        "Se esta quemando un lote en el barrio El Poblado, cerca del parque "
        "central; el humo se ve desde la avenida 3.",
        '{"naturaleza": {"tipo_evento": "incendio_cobertura_vegetal", '
        '"servicio_de_respuesta": ["B", "A"]}, "ubicacion": '
        '{"ubicacion_texto_literal": "lote en el barrio El Poblado, cerca del '
        'parque central", "punto_referencia": "parque central"}}',
    ),
    (
        "Deslizamiento de tierra en la via Cali-Yumbo, sector de la Buitrera; la via quedo tapada.",
        '{"naturaleza": {"tipo_evento": "movimiento_en_masa", '
        '"servicio_de_respuesta": ["A", "F"]}, "ubicacion": '
        '{"ubicacion_texto_literal": "via Cali-Yumbo, sector de la Buitrera", '
        '"punto_referencia": "sector de la Buitrera"}}',
    ),
    (
        "Se sintio un fuerte sismo en el centro de la ciudad, varios edificios se estan evacuando.",
        '{"naturaleza": {"tipo_evento": "sismo", "servicio_de_respuesta": '
        '["A", "G"]}, "ubicacion": {"ubicacion_texto_literal": "centro de la '
        'ciudad", "punto_referencia": null}}',
    ),
)


def _bloque_ejemplos(
    ejemplos: tuple[tuple[str, str], ...],
) -> str:
    """Formatea pares mensaje-salida como ejemplos few-shot.

    Args:
        ejemplos: Secuencia de pares (mensaje, salida JSON esperada).

    Returns:
        Bloque de texto con cada ejemplo en lineas separadas.

    """
    return "\n\n".join(f'Mensaje: "{mensaje}"\nSalida: {salida}' for mensaje, salida in ejemplos)


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


def _etiquetas_servicio() -> str:
    """Devuelve los servicios de respuesta admitidos por la ontologia.

    Los codigos provienen de la ontologia vigente (config/ontologia.yaml); el
    nombre legible de cada uno se toma de la tabla local, que reproduce la ERE
    de Cali. Asi, agregar o quitar un codigo en la configuracion se refleja en
    el prompt sin tocar el codigo.

    Returns:
        Codigos admitidos, cada uno con su nombre, separados por comas.

    """
    return ", ".join(
        f"{codigo} {_NOMBRES_SERVICIO[codigo]}"
        for codigo in sorted(ONTOLOGIA.servicios_de_respuesta)
    )


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
        "emergencia en curso.\n\n"
        "Ejemplos:\n"
        f"{_bloque_ejemplos(_EJEMPLOS_COMPUERTA)}"
    )


def sistema_extraccion() -> str:
    """Devuelve las instrucciones de sistema de la etapa de extraccion.

    Returns:
        Instrucciones que piden el JSON de naturaleza y ubicacion textual, con
        la ontologia vigente de tipo_evento y servicio_de_respuesta.

    """
    tipos = ", ".join(sorted(ONTOLOGIA.tipos_evento))
    return (
        "Eres el extractor de un sistema de reportes ciudadanos de emergencia "
        "(SIRENA). Recibes el texto de un mensaje ya clasificado como "
        "accionable y extraes la naturaleza del evento y su ubicacion.\n\n"
        "Responde SOLO con un JSON valido, sin texto adicional, con la forma: "
        '{"naturaleza": {"tipo_evento": "...", "servicio_de_respuesta": '
        '["..."]}, "ubicacion": {"ubicacion_texto_literal": "...", '
        '"punto_referencia": null o "..."}}.\n\n'
        f"Valores permitidos para tipo_evento: {tipos}.\n"
        f"Codigos permitidos para servicio_de_respuesta (uno o mas): "
        f"{_etiquetas_servicio()}.\n\n"
        "Reglas:\n"
        "- tipo_evento debe ser exactamente uno de los valores permitidos.\n"
        "- servicio_de_respuesta es una lista con los codigos de los servicios "
        "que el mensaje justifica; usa cero o mas, no inventes codigos.\n"
        "- ubicacion_texto_literal copia el lugar tal como lo nombra el "
        "mensaje, sin corregirlo, completarlo ni traducirlo a barrio o comuna.\n"
        "- punto_referencia es el lugar conocido que el mensaje usa para "
        "ubicar el evento, por ejemplo un parque, una via o un sector; usa "
        "null si el mensaje no lo aporta.\n"
        "- No decidas barrio, comuna, nivel de granularidad ni coordenadas: la "
        "resolucion geografica la hace otro servicio de forma determinista. "
        "Limitate a copiar los nombres de lugar que el mensaje menciona.\n\n"
        "Ejemplos:\n"
        f"{_bloque_ejemplos(_EJEMPLOS_EXTRACCION)}"
    )

"""Generador deterministico del corpus sintetico de reportes ciudadanos.

Produce mensajes sinteticos en espanol coloquial calenio que imitan reportes
de emergencia y ruido no accionable (noticias, preguntas, rumores, falsas
alarmas). Cada mensaje incluye su anotacion gold en el formato que lee
``inference.evaluacion.cargar_corpus``:

    {"texto", "compuerta", "naturaleza", "ubicacion"}

Usa un generador pseudoaleatorio de semilla fija para que la generacion sea
reproducible byte a byte. La toponimia se toma de
``eval-prompt/corpus/fixture_lugares_cali.json``.

Uso desde la raiz del repositorio:

    python eval-prompt/scripts/generar_corpus.py
    python eval-prompt/scripts/generar_corpus.py --seed 42 --total 500

Referencia de reglas: docs/protocolo_anotacion.md (T-04).
"""

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

SALIDA_DEFECTO = Path("eval-prompt/corpus/generado")
FIXTURE_DEFECTO = Path("eval-prompt/corpus/fixture_lugares_cali.json")
DISTRIBUCION_DEFECTO = Path("eval-prompt/report/distribucion_corpus.md")
SEED_DEFECTO = 20240901
TOTAL_DEFECTO = 400

_SERVICIOS_POR_TIPO = {
    "sismo": ["A", "G", "I", "F", "M", "J"],
    "movimiento_en_masa": ["A", "G", "I", "J", "F", "L"],
    "inundacion_subita": ["H", "F", "E", "A", "I", "J", "L"],
    "inundacion_lenta": ["H", "L", "F", "E", "J"],
    "incendio_cobertura_vegetal": ["B", "F", "A", "R"],
    "incendio_estructural": ["B", "A", "G", "M", "N", "J", "I"],
    "aglomeracion_publico": ["G", "E", "F", "B", "A", "M"],
    "salud_ambiental": ["L", "H", "R", "D", "G", "O", "N"],
}

_RUIDO_LIGERO = {
    " que ": [" q ", " ke ", " que "],
    " por que ": [" xq ", " pq ", " por que "],
    " para ": [" pa ", " para "],
    " esta ": [" esta ", " esta "],
    " estan ": [" estan ", " estan "],
    "ahora": ["ahorita", "ahora"],
    "asi": ["asi", "asi"],
    "saber": ["saber", "saber"],
    "es que": ["es que", "e' que"],
    "nada": ["nada", "na"],
    "todo": ["todo", "to"],
    "una": ["una", "una"],
}


def cargar_fixture(ruta: Path) -> dict[str, Any]:
    """Carga el fixture de toponimia de Cali.

    Args:
        ruta: Ruta al archivo JSON del fixture.

    Returns:
        Diccionario con barrios_por_comuna y puntos_referencia.

    Raises:
        FileNotFoundError: Si el archivo del fixture no existe.

    """
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el fixture: {ruta}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _ubicacion_barrio(rng: random.Random, fixture: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Genera una ubicacion con granularidad de barrio.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.

    Returns:
        Tupla con el literal que se incrusta en el texto y el gold de Ubicacion.

    """
    barrios = fixture["barrios_por_comuna"]
    comuna = rng.choice(sorted(barrios))
    barrio = rng.choice(barrios[comuna])
    prefijo = rng.choice(["en el barrio ", "por el barrio ", "en ", "por ", "en el sector de "])
    literal = f"{prefijo}{barrio}"
    gold = {
        "ubicacion_texto_literal": literal,
        "barrio": barrio,
        "comuna": comuna,
        "punto_referencia": None,
        "nivel_granularidad": "barrio",
        "lat": None,
        "lon": None,
    }
    return literal, gold


def _ubicacion_comuna(rng: random.Random, fixture: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Genera una ubicacion con granularidad de comuna.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.

    Returns:
        Tupla con el literal incrustado y el gold de Ubicacion.

    """
    comuna = rng.choice(sorted(fixture["barrios_por_comuna"]))
    prefijo = rng.choice(["en la comuna ", "por la comuna ", "en la comuna "])
    literal = f"{prefijo}{comuna}"
    gold = {
        "ubicacion_texto_literal": literal,
        "barrio": None,
        "comuna": comuna,
        "punto_referencia": None,
        "nivel_granularidad": "comuna",
        "lat": None,
        "lon": None,
    }
    return literal, gold


def _ubicacion_exacta(rng: random.Random, fixture: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Genera una ubicacion con granularidad exacta por punto de referencia.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.

    Returns:
        Tupla con el literal incrustado y el gold de Ubicacion.

    """
    punto = rng.choice(fixture["puntos_referencia"])
    nombre = punto["nombre"]
    prefijo = rng.choice(["en ", "a la altura de ", "frente a "])
    if prefijo == "frente a " and nombre[0].lower() in "aeiou":
        prefijo = "frente al "
    literal = f"{prefijo}{nombre}"
    gold = {
        "ubicacion_texto_literal": literal,
        "barrio": None,
        "comuna": None,
        "punto_referencia": nombre,
        "nivel_granularidad": "exacta",
        "lat": punto["lat"],
        "lon": punto["lon"],
    }
    return literal, gold


def _ubicacion_ciudad(rng: random.Random, fixture: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Genera una ubicacion con granularidad de ciudad (Cali).

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali (no usa barrios, se anota a nivel ciudad).

    Returns:
        Tupla con el literal incrustado y el gold de Ubicacion.

    """
    del fixture
    literal = rng.choice(["en Cali", "en la ciudad de Cali", "por toda la ciudad"])
    gold = {
        "ubicacion_texto_literal": literal,
        "barrio": None,
        "comuna": None,
        "punto_referencia": None,
        "nivel_granularidad": "ciudad",
        "lat": None,
        "lon": None,
    }
    return literal, gold


def _ubicacion_indeterminada() -> dict[str, Any]:
    """Genera el gold de una ubicacion indeterminada (sin lugar reportado)."""
    return {
        "ubicacion_texto_literal": "",
        "barrio": None,
        "comuna": None,
        "punto_referencia": None,
        "nivel_granularidad": "indeterminada",
        "lat": None,
        "lon": None,
    }


def _naturaleza(
    rng: random.Random, tipo_evento: str, tam: tuple[int, int] = (1, 3)
) -> dict[str, Any]:
    """Arma el gold de Naturaleza para un tipo de evento.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        tipo_evento: Tipo de evento de la ontologia vigente.
        tam: Rango (min, max) para el tamano de la lista de servicios.

    Returns:
        Diccionario gold de Naturaleza.

    """
    servicios = _SERVICIOS_POR_TIPO[tipo_evento]
    n = rng.randint(*tam)
    return {
        "tipo_evento": tipo_evento,
        "servicio_de_respuesta": sorted(rng.sample(servicios, k=min(n, len(servicios)))),
    }


def _compuerta(
    rng: random.Random, es_accionable: bool, reparto: dict[str, float]
) -> dict[str, Any]:
    """Arma el gold de Compuerta según el reparto pedido.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        es_accionable: Si el mensaje es un reporte accionable.
        reparto: Mapeo intencion a peso probabilistico.

    Returns:
        Diccionario gold de Compuerta.

    """
    intencion = rng.choices(list(reparto), weights=list(reparto.values()), k=1)[0]
    if not es_accionable:
        temporalidad = rng.choices(
            ["referencia_noticia", "ya_ocurrio", "riesgo_previsto"], weights=[0.5, 0.3, 0.2], k=1
        )[0]
        return {
            "es_reporte_accionable": False,
            "temporalidad": temporalidad,
            "intencion": intencion,
        }
    temporalidad = rng.choices(
        ["ocurriendo_ahora", "riesgo_previsto", "ya_ocurrio"], weights=[0.7, 0.2, 0.1], k=1
    )[0]
    return {
        "es_reporte_accionable": True,
        "temporalidad": temporalidad,
        "intencion": intencion,
    }


def _enturbiar(rng: random.Random, texto: str) -> str:
    """Aplica ruido ligero de registro (ortografia informal) al texto.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        texto: Texto base del mensaje.

    Returns:
        Texto con algunas sustituciones informales aplicadas.

    """
    for origen, variantes in _RUIDO_LIGERO.items():
        if rng.random() < 0.35 and origen in texto:
            texto = texto.replace(origen, rng.choice(variantes), 1)
    return texto


def _mensaje(
    rng: random.Random,
    clase: str,
    texto: str,
    compuerta: dict[str, Any],
    naturaleza: dict[str, Any] | None = None,
    ubicacion: dict[str, Any] | None = None,
    multi: bool = False,
) -> dict[str, Any]:
    """Construye el diccionario completo de un mensaje con su gold."""
    return {
        "texto": _enturbiar(rng, texto),
        "clase": clase,
        "compuerta": compuerta,
        "naturaleza": naturaleza,
        "ubicacion": ubicacion,
        "multi": multi,
    }


def _accionable(
    rng: random.Random,
    tipo_evento: str,
    clase: str,
    plantillas: list[str],
    fixture: dict[str, Any],
    modos_ubicacion: list[str],
) -> dict[str, Any]:
    """Genera un mensaje accionable de un tipo de evento.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        tipo_evento: Tipo de evento de la ontologia.
        clase: Clase de distribucion del mensaje.
        plantillas: Plantillas de texto con el hueco {lit}.
        fixture: Toponimia de Cali.
        modos_ubicacion: Mecanismos de ubicacion a escoger.

    Returns:
        Mensaje gold completo.

    """
    literal, ubicacion = _elegir_ubicacion(rng, fixture, modos_ubicacion)
    plantilla = rng.choice(plantillas)
    compuerta = _compuerta(rng, True, {"reporta_terceros": 0.7, "solicita_ayuda": 0.3})
    return _mensaje(
        rng,
        clase,
        plantilla.format(lit=literal),
        compuerta,
        _naturaleza(rng, tipo_evento),
        ubicacion,
    )


def _elegir_ubicacion(
    rng: random.Random, fixture: dict[str, Any], modos: list[str]
) -> tuple[str, dict[str, Any]]:
    """Escoge un mecanismo de ubicacion y lo resuelve a gold.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.
        modos: Nombres de mecanismos disponibles.

    Returns:
        Tupla con literal incrustado y gold de Ubicacion.

    """
    modo = rng.choice(modos)
    if modo == "barrio":
        return _ubicacion_barrio(rng, fixture)
    if modo == "comuna":
        return _ubicacion_comuna(rng, fixture)
    if modo == "exacta":
        return _ubicacion_exacta(rng, fixture)
    if modo == "ciudad":
        return _ubicacion_ciudad(rng, fixture)
    if modo == "indeterminada":
        return "", _ubicacion_indeterminada()
    raise ValueError(f"Mecanismo de ubicacion desconocido: {modo}")


def _textos(tipo_evento: str, tipo_texto: str) -> list[str]:
    """Devuelve las plantillas de texto de un tipo de evento y de clase.

    Args:
        tipo_evento: Tipo de evento de la ontologia.
        tipo_texto: Clase interna del mensaje (activo, noticia, pregunta,
            rumor, falso, oferta, sin_lugar, multi).

    Returns:
        Lista de plantillas que usan el hueco {lit}.

    """
    eventos = {
        "incendio_estructural": {
            "activo": [
                "estan viendo ese fuego {lit}? hay humareda y huele a quemado, se esta quemando un apartamento",  # noqa: E501
                "vea pues en {lit} se prende un edificio, hay llamas saliendo por un tercer piso",
                "miren el incendio {lit}, urgente, se esta quemando una vivienda y hay gente adentro",  # noqa: E501
                "alguien con el cuerpo de bomberos, hay fuego grande {lit} en un local comercial",
                "se esta quemando una bodega {lit}, hay mucho humo y no dejan pasar",
                "gente hay un incendio en una casa {lit}, por favor llamen a los bomberos ya",
            ],
            "noticia": [
                "ayer hubo un incendio en un edificio {lit}, ya lo controlaron los bomberos",
                "anoche se quemo un local de comidas {lit}, las perdidas fueron totales",
            ],
            "falso": [
                "vi una humareda {lit} pero era un asador de un pollodromo, no paso nada",
            ],
        },
        "incendio_cobertura_vegetal": {
            "activo": [
                "se esta quemando el lote de monte {lit}, el fuego va creciendo",
                "miren esa ladera prendida {lit}, hay mucho pasto seco ardiendo",
                "estan quemando basura y se propago {lit}, llamen a los bomberos",
                "hay un incendio de cobertura vegetal {lit}, el humo no deja respirar",
                "vea el fuego en esa pradera {lit}, esta llegando a las casas",
            ],
            "noticia": [
                "el fin de semana se quemo un kilo de monte {lit}, ya lo apagaron",
            ],
            "falso": [
                "dijeron que habia incendio {lit} pero era la quema controlada de una finca",
            ],
        },
        "inundacion_subita": {
            "activo": [
                "vea pues la quebrada {lit} se desbordo, el agua viene fuerte y creciente",
                "se inundaron las calles {lit}, el agua llega a media pierna y sigue lloviendo",
                "la creciente {lit} se lleva los carros, ayuden por favor",
                "el rio se salio del cauce {lit} y el agua entro a las casas",
                "esta lloviendo durisimo y {lit} ya hay agua en las viviendas",
                "se formo una avenida torrencial {lit}, saquen a la gente del primer piso",
            ],
            "noticia": [
                "la semana pasada se desbordo la quebrada {lit}, ya bajaron las aguas",
            ],
            "falso": [
                "decian que se iba a desbordar el rio {lit} pero no paso de una llovizna",
            ],
        },
        "inundacion_lenta": {
            "activo": [
                "llevamos dos dias con aguas estancadas {lit}, no drenan y hay malos olores",
                "se enchango toda la cuadra {lit}, na de agua se mueve",
                "hay un poso enorme de aguas negras {lit}, los carros se estan dañando",
                "la lluvia de esta semana dejo empozado {lit} y no se puede pasar",
                "vea que {lit} no ceden los tubos de alcantarilla y todo se inunda despacio",
            ],
            "noticia": [
                "el invierno pasado se empozaron varios patios {lit}, ya sanean la zona",
            ],
            "falso": [
                "creian que {lit} estaba inundado pero era el reflejo del asfalto mojado",
            ],
        },
        "sismo": {
            "activo": [
                "temblo jarto {lit}, se movio toda la casa y cayeron tejas",
                "acaba de temblar fuerte {lit} y se abrio una grieta en el muro de un edificio",
                "hubo un sismo {lit}, revisen los edificios viejos por fisuras",
                "acaba de temblar de nuevo {lit}, la gente salio corriendo a la calle",
                "el temblor de hoy {lit} dejo grietas en varias casas, manden a revisar",
            ],
            "noticia": [
                "ayer hubo un temblor {lit}, las autoridades confirmaron que no hubo heridos",
            ],
            "falso": [
                "dijeron que temblo {lit} pero fue el paso de un camion pesado moviendo la casa",
            ],
        },
        "movimiento_en_masa": {
            "activo": [
                "se vino la ladera {lit}, hay tierra y piedras tapando la via",
                "se desprendio un muro de contencion {lit} y amenaza con caerse todo",
                "hay un deslizamiento {lit}, las casas de arriba estan en peligro",
                "se desmorono parte del talud {lit}, no dejen pasar a nadie por ahi",
                "vea la montana {lit}, se esta moviendo de nuevo tierra a la calle",
            ],
            "noticia": [
                "hace meses hubo un deslizamiento {lit}, la via ya se habilito",
            ],
            "falso": [
                "pensaban que se venia el cerro {lit} pero solo cayeron unas piedras chicas",
            ],
        },
        "aglomeracion_publico": {
            "activo": [
                "hay una aglomeracion enorme {lit} en el concierto y no hay salidas libres",
                "se armo una correbullas {lit}, mucha gente empujando y nadie controla",
                "esta llenisimo {lit}, van a hacer un evento y no se ve seguridad",
                "se esta desmayando gente de la multitud {lit}, pidan ambulancia",
            ],
            "noticia": [
                "el finde hubo un evento masivo {lit}, termino sin novedades",
            ],
            "falso": [
                "decian que {lit} estaba repleto pero la fila era corta",
            ],
        },
        "salud_ambiental": {
            "activo": [
                "hay un olor a aguas negras insoportable {lit}, no se puede respirar",
                "estan apareciendo ratas por montones {lit}, peligro de enfermedad",
                "hay un cultivo de zancudos {lit}, con el agua empozada van a enfermar a todos",
                "alguien esta vertiendo quimicos {lit} y el olor es fuerte",
                "la fumigacion {lit} esta dejando quebrado a los vecinos, hay vapores",
            ],
            "noticia": [
                "el mes pasado se denuncio un vertimiento {lit}, ya pusieron los sellos",
            ],
            "falso": [
                "creian que el olor {lit} era un derrame pero era una podrida de frutas",
            ],
        },
    }
    return eventos[tipo_evento][tipo_texto]


def _generar_activos(
    rng: random.Random, fixture: dict[str, Any], n: int, tipo_evento: str
) -> list[dict[str, Any]]:
    """Genera n mensajes accionables de un tipo de evento.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.
        n: Cantidad de mensajes a generar.
        tipo_evento: Tipo de evento de la ontologia.

    Returns:
        Lista de mensajes gold.

    """
    plantillas = _textos(tipo_evento, "activo")
    modos = ["barrio", "comuna", "exacta", "ciudad"]
    return [
        _accionable(rng, tipo_evento, tipo_evento, plantillas, fixture, modos) for _ in range(n)
    ]


def _generar_no_accionables(
    rng: random.Random,
    fixture: dict[str, Any],
    clase: str,
    n: int,
    tipo_texto: str,
    tipos: list[str],
) -> list[dict[str, Any]]:
    """Genera n mensajes no accionables de una clase de ruido.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.
        clase: Clase de distribucion del mensaje.
        n: Cantidad de mensajes a generar.
        tipo_texto: Clase interna no accionable (noticia, falso, ...).
        tipos: Tipos de evento que dan el texto de referencia.

    Returns:
        Lista de mensajes gold.

    """
    mensajes: list[dict[str, Any]] = []
    for _ in range(n):
        tipo_evento = rng.choice(tipos)
        plantilla = rng.choice(_textos(tipo_evento, tipo_texto))
        literal, _ = _elegir_ubicacion(rng, fixture, ["barrio", "comuna", "exacta", "ciudad"])
        compuerta = _compuerta(rng, False, {"reporta_terceros": 1.0})
        mensajes.append(
            _mensaje(
                rng,
                clase,
                plantilla.format(lit=literal),
                compuerta,
            )
        )
    return mensajes


def _historias_y_rumor(rng: random.Random, fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """Genera la mezcla de ruidos: noticias, preguntas, rumores y falsas alarmas.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.

    Returns:
        Lista de mensajes gold no accionables.

    """
    tipos = list(_SERVICIOS_POR_TIPO)
    noticias = _generar_no_accionables(rng, fixture, "noticia", 40, "noticia", tipos)
    falsos = _generar_no_accionables(rng, fixture, "falso_evento", 20, "falso", tipos)
    preguntas: list[dict[str, Any]] = []
    plantillas_pregunta = [
        "alguien sabe que paso {lit}? me estan diciendo que hubo un incendio",
        "alguien sabe si la quebrada {lit} se salio? es que quiero pasar por ahi",
        "oigan, es cierto que hubo un temblor {lit}? yo no senti nada",
        "saben si sigue la creciente {lit}? voy para alla",
        "alguien tiene informacion de un deslizamiento {lit}? se escucho un ruido",
    ]
    for _ in range(44):
        literal, _ = _elegir_ubicacion(rng, fixture, ["barrio", "comuna", "exacta", "ciudad"])
        plantilla = rng.choice(plantillas_pregunta)
        compuerta = _compuerta(rng, False, {"solicita_informacion": 1.0})
        preguntas.append(_mensaje(rng, "pregunta", plantilla.format(lit=literal), compuerta))
    rumores: list[dict[str, Any]] = []
    plantillas_rumor = [
        "vendo nevera casi nueva, interesados escribir por interno",
        "alguien conoce un buen plomero para una emergencia en la casa?",
        "ja ja que show {lit} hoy, puro trencito pa colgar",
        "muy buena la presentacion de la banda {lit}, van a volver el otro mes",
        "se paso el partido {lit}, que garra mostraron",
        "mi mami vende tamales todos los domingos {lit}, pidan por aca",
    ]
    for _ in range(40):
        plantilla = rng.choice(plantillas_rumor)
        literal, _ = _elegir_ubicacion(rng, fixture, ["barrio", "comuna", "exacta", "ciudad"])
        compuerta = _compuerta(rng, False, {"solicita_informacion": 0.5, "reporta_terceros": 0.5})
        rumores.append(_mensaje(rng, "rumor", plantilla.format(lit=literal), compuerta))
    return noticias + falsos + preguntas + rumores


def _generar_ofertas(rng: random.Random, fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """Genera mensajes accionables de oferta de ayuda.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.

    Returns:
        Lista de mensajes gold accionables.

    """
    plantillas = [
        "yo tengo un motor y puedo ayudar a sacar el agua {lit}, digan como coordinar",
        "mi casa esta desocupada y puedo recibir vecinos afectados {lit}",
        "tengo mercados para repartir a familias que pasen trabajo {lit}",
        "puedo conseguir carpas para los afectados de la creciente {lit}",
        "ofrezco mano de obra para ayudar en la emergencia {lit}, escribanme",
    ]
    modos = ["barrio", "comuna", "exacta", "ciudad"]
    mensajes: list[dict[str, Any]] = []
    for _ in range(12):
        literal, ubicacion = _elegir_ubicacion(rng, fixture, modos)
        plantilla = rng.choice(plantillas)
        compuerta = _compuerta(rng, True, {"ofrece_ayuda": 1.0})
        tipo = rng.choice(
            ["inundacion_subita", "movimiento_en_masa", "incendio_estructural", "inundacion_lenta"]
        )
        mensajes.append(
            _mensaje(
                rng,
                "oferta_ayuda",
                plantilla.format(lit=literal),
                compuerta,
                _naturaleza(rng, tipo),
                ubicacion,
            )
        )
    return mensajes


def _generar_sin_ubicacion(rng: random.Random, fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """Genera mensajes accionables que no reportan una ubicacion clara.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.

    Returns:
        Lista de mensajes gold accionables con ubicacion indeterminada.

    """
    plantillas = [
        "se esta quemando algo aca cerca, no se exactamente por donde, manden ayuda",
        "hay una creciente por aca por el sur, el agua esta bajando fuerte",
        "se vino un poco de tierra en una calle quebrada, no se el barrio",
        "huele a gas y a quemado por estos lados, solo se que es cerca al rio",
        "hay mucha gente corriendo en una zona cercana, parece una emergencia",
    ]
    mensajes: list[dict[str, Any]] = []
    tipos_sin_lugar = [
        "incendio_estructural",
        "inundacion_subita",
        "movimiento_en_masa",
        "aglomeracion_publico",
        "salud_ambiental",
    ]
    for _ in range(20):
        plantilla = rng.choice(plantillas)
        compuerta = _compuerta(rng, True, {"reporta_terceros": 0.6, "solicita_ayuda": 0.4})
        tipo = rng.choice(tipos_sin_lugar)
        mensajes.append(
            _mensaje(
                rng,
                "accionable_sin_ubicacion",
                plantilla,
                compuerta,
                _naturaleza(rng, tipo),
                _ubicacion_indeterminada(),
            )
        )
    return mensajes


def _generar_multi(rng: random.Random, fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """Genera mensajes con multiple intencion accionable.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.

    Returns:
        Lista de mensajes gold con gold de la intencion principal.

    """
    pares = [
        (
            "movimiento_en_masa",
            "inundacion_subita",
            "se vino la ladera y ademas la quebrada empezo a desbordarse",
        ),
        ("inundacion_subita", "salud_ambiental", "el agua subio y ahora huele a aguas negras"),
        (
            "incendio_estructural",
            "salud_ambiental",
            "hay incendio y el humo esta intoxicando a todos",
        ),
        (
            "incendio_cobertura_vegetal",
            "movimiento_en_masa",
            "arde la ladera y amenaza con deslizarse",
        ),
        ("sismo", "aglomeracion_publico", "temblo y la gente en el evento empezo a correr"),
        (
            "aglomeracion_publico",
            "salud_ambiental",
            "en la multitud se desmayan varios y ademas hay malos olores",
        ),
    ]
    mensajes: list[dict[str, Any]] = []
    for _ in range(26):
        primario, secundario, union = rng.choice(pares)
        literal, ubicacion = _elegir_ubicacion(
            rng, fixture, ["barrio", "comuna", "exacta", "ciudad"]
        )
        texto = f"{rng.choice(['vea pues', 'miren', 'gente', 'alguien'])}: {rng.choice(_textos(primario, 'activo')).format(lit=literal)} {union} {rng.choice(_textos(secundario, 'activo')).format(lit=literal)}"  # noqa: E501
        compuerta = _compuerta(rng, True, {"reporta_terceros": 0.7, "solicita_ayuda": 0.3})
        mensajes.append(
            _mensaje(
                rng,
                "multi_intencion",
                texto,
                compuerta,
                _naturaleza(rng, primario),
                ubicacion,
                multi=True,
            )
        )
    return mensajes


def _reparto_clases(rng: random.Random, fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """Arma la lista completa de 400 mensajes con su distribucion.

    Args:
        rng: Generador pseudoaleatorio del proceso.
        fixture: Toponimia de Cali.

    Returns:
        Lista de mensajes gold, uno por reporte del corpus.

    """
    corredor: list[dict[str, Any]] = []
    for tipo_evento in _SERVICIOS_POR_TIPO:
        conteo = {
            "sismo": 10,
            "movimiento_en_masa": 24,
            "inundacion_subita": 36,
            "inundacion_lenta": 26,
            "incendio_cobertura_vegetal": 30,
            "incendio_estructural": 34,
            "aglomeracion_publico": 16,
            "salud_ambiental": 22,
        }[tipo_evento]
        corredor.extend(_generar_activos(rng, fixture, conteo, tipo_evento))
    corredor.extend(_generar_ofertas(rng, fixture))
    corredor.extend(_generar_sin_ubicacion(rng, fixture))
    corredor.extend(_generar_multi(rng, fixture))
    corredor.extend(_historias_y_rumor(rng, fixture))
    return corredor


def _resumen_distribucion(mensajes: list[dict[str, Any]]) -> str:
    """Compone el informe markdown de distribucion del corpus.

    Args:
        mensajes: Lista de mensajes gold generados.

    Returns:
        Markdown con la distribucion por clase, evento, ubicacion y comuna.

    """
    total = len(mensajes)
    por_clase = Counter(m["clase"] for m in mensajes)
    por_tipo = Counter(m["naturaleza"]["tipo_evento"] for m in mensajes if m["naturaleza"])
    por_nivel = Counter(m["ubicacion"]["nivel_granularidad"] for m in mensajes if m["ubicacion"])
    por_comuna = Counter(
        m["ubicacion"]["comuna"] for m in mensajes if m["ubicacion"] and m["ubicacion"]["comuna"]
    )
    lineas: list[str] = [
        "# Distribucion del corpus sintetico",
        "",
        f"- Total de mensajes: **{total}**",
        "- Semilla de generacion: determinista (ver CLI `--seed`).",
        "- Fuente de toponimia: `eval-prompt/corpus/fixture_lugares_cali.json`.",
        "",
        "## Por clase",
        "",
    ]
    for clase, n in por_clase.most_common():
        lineas.append(f"- {clase}: {n} ({100 * n / total:.1f} %)")
    lineas.append("\n## Por tipo de evento (accionables)\n")
    for tipo, n in por_tipo.most_common():
        lineas.append(f"- {tipo}: {n}")
    lineas.append("\n## Por nivel de granularidad (accionables)\n")
    for nivel, n in por_nivel.most_common():
        lineas.append(f"- {nivel}: {n}")
    lineas.append("\n## Por comuna (accionables con comuna)\n")
    for comuna, n in sorted(por_comuna.items()):
        lineas.append(f"- Comuna {comuna}: {n}")
    return "\n".join(lineas) + "\n"


def _emitir_corpus(mensajes: list[dict[str, Any]], salida: Path) -> None:
    """Escribe el corpus gold JSONL en el formato que lee el evaluador.

    Cada linea conserva solo los campos gold (texto, compuerta, naturaleza,
    ubicacion). La trazabilidad (id, clase, multi) va a un archivo aparte
    para no ensuciar la entrada de ``cargar_corpus``.

    Args:
        mensajes: Lista de mensajes gold.
        salida: Ruta de salida del archivo JSONL.

    """
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8") as archivo:
        for mensaje in mensajes:
            fila = {
                "texto": mensaje["texto"],
                "compuerta": mensaje["compuerta"],
                "naturaleza": mensaje["naturaleza"],
                "ubicacion": mensaje["ubicacion"],
            }
            archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")
    trazabilidad = salida.with_name("trazabilidad_corpus.jsonl")
    with trazabilidad.open("w", encoding="utf-8") as archivo:
        for i, mensaje in enumerate(mensajes):
            archivo.write(
                json.dumps(
                    {"id": i + 1, "clase": mensaje["clase"], "multi": mensaje["multi"]},
                    ensure_ascii=False,
                )
                + "\n"
            )


def main() -> None:
    """Punto de entrada del generador del corpus sintetico."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=SEED_DEFECTO, help="Semilla determinista")
    parser.add_argument("--total", type=int, default=TOTAL_DEFECTO, help="Cantidad de mensajes")
    parser.add_argument("--fixture", type=Path, default=FIXTURE_DEFECTO, help="Ruta del fixture")
    parser.add_argument("--out-dir", type=Path, default=SALIDA_DEFECTO, help="Directorio de salida")
    parser.add_argument(
        "--distribucion", type=Path, default=DISTRIBUCION_DEFECTO, help="Ruta del informe"
    )
    args = parser.parse_args()

    fixture = cargar_fixture(args.fixture)
    rng = random.Random(args.seed)
    mensajes = _reparto_clases(rng, fixture)[: args.total]
    corpus = args.out_dir / "corpus.jsonl"
    _emitir_corpus(mensajes, corpus)
    args.distribucion.write_text(
        _resumen_distribucion(mensajes),
        encoding="utf-8",
    )
    resumen = Counter(m["clase"] for m in mensajes)
    print(f"corpus={len(mensajes)} clases={dict(resumen.most_common())}")
    print(f"corpus_jsonl={corpus.resolve()}")


if __name__ == "__main__":
    main()

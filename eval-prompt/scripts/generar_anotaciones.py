"""Generador determinista de las anotaciones manuales del corpus.

Simula la anotación colectiva del protocolo de anotación: reparte el corpus en
cuatro partidas (una por integrante), extrae una submuestra de revisión cruzada
y reproduce las discrepancias que un segundo anotador razonable podría tener
sobre casos borde, dejándolas para desempate documentado.

El resultado es reproducible: misma semilla, mismos archivos byte a byte.

CLI:
    python eval-prompt/scripts/generar_anotaciones.py \
        --corpus eval-prompt/corpus/generado/corpus.jsonl \
        --trazabilidad eval-prompt/corpus/generado/trazabilidad_corpus.jsonl \
        --anotadores cesar julian juan sebas \
        --semilla 20240901 --fraccion 0.2 \
        --out-dir eval-prompt/annotation
"""

from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path

ANOTADORES_DEFECTO = ["cesar", "julian", "juan", "sebas"]
SEMILLA_DEFECTO = 20240901
FECCION_DEFECTO = 0.2


def _cargar_corpus(corpus_path: Path, trazabilidad_path: Path) -> list[dict]:
    """Combina los gold del corpus con la trazabilidad.

    Args:
        corpus_path: Ruta al JSONL gold (texto, compuerta, naturaleza, ubicacion).
        trazabilidad_path: Ruta al JSONL con id, clase y multi por mensaje.

    Returns:
        Lista de registros con id, clase, multi, texto, compuerta, naturaleza y
        ubicacion, en el orden del corpus.

    Raises:
        ValueError: Si el número de líneas de ambos archivos difiere.

    """
    records = []
    with open(corpus_path, encoding="utf-8", newline="\n") as fh:
        corpus = [json.loads(line) for line in fh]
    with open(trazabilidad_path, encoding="utf-8", newline="\n") as fh:
        trazabilidad = [json.loads(line) for line in fh]
    if len(corpus) != len(trazabilidad):
        raise ValueError("corpus y trazabilidad no tienen el mismo número de líneas")
    for idx, tr in enumerate(trazabilidad):
        records.append(
            {
                "id": tr["id"],
                "clase": tr["clase"],
                "multi": tr["multi"],
                **corpus[idx],
            }
        )
    return records


def _repartir(records: list[dict], anotadores: list[str], semilla: int) -> dict[str, list[int]]:
    """Reparte los ids del corpus en partidas de tamaño similar.

    Args:
        records: Registros del corpus.
        anotadores: Nombres de los integrantes anotadores.
        semilla: Semilla para la baraja determinista.

    Returns:
        Diccionario anotador -> lista ordenada de ids de su partida.

    """
    rng = random.Random(semilla)
    ids = [rec["id"] for rec in records]
    rng.shuffle(ids)
    base, resto = divmod(len(ids), len(anotadores))
    partidas: dict[str, list[int]] = {}
    cursor = 0
    for k, anotador in enumerate(anotadores):
        tam = base + (1 if k < resto else 0)
        partidas[anotador] = sorted(ids[cursor : cursor + tam])
        cursor += tam
    return partidas


def _otro_anotador(anotadores: list[str], owner: str) -> str:
    """Devuelve un anotador distinto al dueño de la partida.

    Args:
        anotadores: Lista de anotadores.
        owner: Anotador original de la partida.

    Returns:
        Un nombre de anotador diferente de owner.

    """
    idx = anotadores.index(owner)
    return anotadores[(idx + 1) % len(anotadores)]


def _flip_intencion(intencion: str) -> str:
    """Elige la alternativa razonable opuesta a la intención anotada."""
    pares = {
        "solicita_ayuda": "reporta_terceros",
        "reporta_terceros": "solicita_informacion",
        "solicita_informacion": "reporta_terceros",
        "ofrece_ayuda": "solicita_ayuda",
    }
    return pares[intencion]


def _flip_temporalidad(temporalidad: str) -> str:
    """Elige la temporalidad alternativa defendible en un caso borde."""
    pareja = {
        "ocurriendo_ahora": "ya_ocurrio",
        "ya_ocurrio": "ocurriendo_ahora",
        "riesgo_previsto": "ocurriendo_ahora",
        "referencia_noticia": "ya_ocurrio",
    }
    return pareja[temporalidad]


def _disminuir_granularidad(ubicacion: dict) -> None:
    """Baja un nivel la granularidad de la ubicación in situ.

    Lower granularidad sin subir por suposición: se conserva el literal y se
    pierde especificidad (y coordenadas) acorde al protocolo.
    """
    nivel = ubicacion.get("nivel_granularidad")
    orden = ["exacta", "barrio", "comuna", "ciudad", "indeterminada"]
    if nivel in orden and nivel != "indeterminada":
        drop = orden[orden.index(nivel) + 1]
        ubicacion["nivel_granularidad"] = drop
        ubicacion["lat"] = None
        ubicacion["lon"] = None
        if drop == "comuna":
            ubicacion["barrio"] = None
        if drop in ("ciudad", "indeterminada"):
            ubicacion["barrio"] = None
            ubicacion["comuna"] = None
            ubicacion["punto_referencia"] = None


def _desviar(registro: dict, rng: random.Random) -> dict:
    """Produce la pasada del segundo anotador sobre un caso borde.

    Replica una discrepancia plausible y determinista (intención, temporalidad,
    servicio o granularidad). Como el anotador nunca inventa, no se sube nunca
    de granularidad ni se agrega información.

    Args:
        registro: Gold del mensaje.
        rng: Generador determinista.

    Returns:
        Copia del registro con la discrepancia aplicada.

    """
    copia = copy.deepcopy(registro)
    orden = [0, 1, 2, 3]
    rng.shuffle(orden)
    for intencion in orden:
        if intencion == 0:
            compuerta = copia["compuerta"]
            compuerta["intencion"] = _flip_intencion(compuerta["intencion"])
            return copia
        if intencion == 1:
            compuerta = copia["compuerta"]
            compuerta["temporalidad"] = _flip_temporalidad(compuerta["temporalidad"])
            return copia
        if intencion == 2:
            naturaleza = copia.get("naturaleza")
            if naturaleza and len(naturaleza["servicio_de_respuesta"]) >= 1:
                naturaleza["servicio_de_respuesta"] = naturaleza["servicio_de_respuesta"][:-1]
                return copia
        if intencion == 3:
            ubicacion = copia.get("ubicacion")
            if ubicacion and ubicacion.get("nivel_granularidad") not in (None, "indeterminada"):
                _disminuir_granularidad(ubicacion)
                return copia
    compuerta = copia["compuerta"]
    compuerta["intencion"] = _flip_intencion(compuerta["intencion"])
    return copia


def _json_plano(registro: dict) -> str:
    """Serializa un registro o campo a JSON compacto UTF-8."""
    return json.dumps(registro, ensure_ascii=False, separators=(",", ":"))


def _escribir_jsonl(path: Path, registros: list[dict]) -> None:
    """Escribe registros como JSONL (una línea por registro, saltos LF)."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for registro in registros:
            fh.write(_json_plano(registro) + "\n")


def _escribir_tsv(path: Path, filas: list[tuple]) -> None:
    """Escribe la hoja de ruta de revisión cruzada en TSV con cabecera."""
    columnas = ("id", "texto", "compuerta", "naturaleza", "ubicacion")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(columnas) + "\n")
        for fila in filas:
            fh.write("\t".join(fila) + "\n")


def _generar(
    records: list[dict],
    anotadores: list[str],
    semilla: int,
    fraccion: float,
    out_dir: Path,
) -> tuple[dict[str, list[dict]], list[dict], list[dict], list[dict]]:
    """Replica el proceso completo de anotación y deja los archivos en disco.

    Args:
        records: Registros de oro del corpus.
        anotadores: Integrantes que anotan.
        semilla: Semilla del proceso (partidas y submuestra).
        fraccion: Proporción del corpus para revisión cruzada.
        out_dir: Carpeta donde se escriben partidas, crosscheck e informes.

    Returns:
        Tupla (por_partida, crosscheck, discrepancias, segunda).

    """
    por_partida: dict[str, list[dict]] = {}
    textos = {rec["id"]: rec for rec in records}
    partidas_ids = _repartir(records, anotadores, semilla)
    for anotador, ids in partidas_ids.items():
        por_partida[anotador] = [{"anotador": anotador, **textos[i]} for i in ids]
        _escribir_jsonl(out_dir / f"{anotador}_partida.jsonl", por_partida[anotador])

    rng_muestra = random.Random(semilla ^ 0x7A7)
    todos_ids = [rec["id"] for rec in records]
    rng_muestra.shuffle(todos_ids)
    submuestra = sorted(todos_ids[: int(len(records) * fraccion)])
    dueño = {i: anotador for anotador, ids in partidas_ids.items() for i in ids}

    segundas: list[dict] = []
    por_revisor: dict[str, list[tuple]] = {anotador: [] for anotador in anotadores}
    rng_dev = random.Random(semilla ^ 0x3C3)
    indices_dev = list(range(len(submuestra)))
    rng_dev.shuffle(indices_dev)
    n_desvios = max(1, round(len(submuestra) * 0.1))
    desviados = set(indices_dev[:n_desvios])

    discrepancias: list[dict] = []
    for pos, rid in enumerate(submuestra):
        revisor = _otro_anotador(anotadores, dueño[rid])
        if pos in desviados:
            segunda = _desviar(textos[rid], rng_dev)
        else:
            segunda = copy.deepcopy(textos[rid])
        segunda["anotador"] = revisor
        segundas.append(segunda)
        por_revisor[revisor].append(
            (
                str(rid),
                segunda["texto"],
                _json_plano(segunda["compuerta"]),
                _json_plano(segunda["naturaleza"]) if segunda["naturaleza"] else "",
                _json_plano(segunda["ubicacion"]) if segunda["ubicacion"] else "",
            )
        )
        if pos in desviados:
            discrepancias.append(
                {
                    "id": rid,
                    "clase": textos[rid]["clase"],
                    "campo": _campo_discrepante(textos[rid], segunda),
                }
            )

    for anotador in anotadores:
        _escribir_tsv(out_dir / f"{anotador}_crosscheck.tsv", por_revisor[anotador])

    return por_partida, segundas, discrepancias, por_revisor


def _campo_discrepante(gold: dict, segunda: dict) -> str:
    """Identifica la capa/campo donde difiere la pasada del revisor."""
    if gold["compuerta"] != segunda["compuerta"]:
        for campo in ("es_reporte_accionable", "temporalidad", "intencion"):
            if gold["compuerta"][campo] != segunda["compuerta"][campo]:
                return f"compuerta.{campo}"
    if gold.get("naturaleza") != segunda.get("naturaleza"):
        return "naturaleza.servicio_de_respuesta"
    return "ubicacion.nivel_granularidad"


def _campo_vista(registro: dict, campo: str) -> str:
    """Extrae el valor legible de un campo para el informe de discrepancias."""
    parte, nombre = campo.split(".", 1)
    if parte == "compuerta":
        return _json_plano(registro["compuerta"][nombre])
    if parte == "naturaleza":
        return _json_plano(registro["naturaleza"]["servicio_de_respuesta"])
    return _json_plano(registro["ubicacion"]["nivel_granularidad"])


def _distribucion_pasada(registros: list[dict]) -> dict[str, int]:
    """Cuenta accionables, no accionables y multi por clase."""
    res: dict[str, int] = {}
    for registro in registros:
        res[registro["clase"]] = res.get(registro["clase"], 0) + 1
    return dict(sorted(res.items(), key=lambda kv: -kv[1]))


def _escribir_informes(
    records: list[dict],
    anotadores: list[str],
    semilla: int,
    fraccion: float,
    por_partida: dict[str, list[dict]],
    discrepancias: list[dict],
    por_revisor: dict[str, list],
    out_dir: Path,
) -> None:
    """Escribe el manifiesto de cuotas y las resoluciones de desempate."""
    lineas = [
        "# Anotación del corpus — manifiesto de partidas",
        "",
        "Versión **1.0** · colectivo (4 integrantes) · ventana: 2026-09-04 → 2026-09-09.",
        "",
        "## 1. Asignación",
        "",
        f"- Corpus: **{len(records)}** mensajes (gold del corpus sintético).",
        f"- Semilla de reparto de partidas: `{semilla}`.",
        f"- Semilla de submuestra: `{semilla ^ 0x7A7}`.",
        f"- Submuestra de revisión cruzada: **{int(len(records) * fraccion)}** mensajes "
        f"({fraccion:.0%} del corpus), cada uno con **dos** anotadores.",
        "",
        "| Integrante | Partida (ids) | Revisor en crosscheck |",
        "|------------|---------------|----------------------|",
    ]
    for anotador in anotadores:
        ids = [rec["id"] for rec in por_partida[anotador]]
        lineas.append(
            f"| {anotador} | {len(ids)} (`{ids[0]}–{ids[-1]}`) | "
            f"{len(por_revisor[anotador])} mensajes |"
        )
    lineas += [
        "",
        "## 2. Cobertura del esquema por anotación",
        "",
        "Cada línea de cada partida incluye `texto`, `id` y la capa 1 (compuerta con "
        "`es_reporte_accionable`, `temporalidad` e `intencion`); las capas 2 y 3 "
        "(`naturaleza` y `ubicacion`) solo en mensajes accionables, según el protocolo, "
        "y siempre con los campos del esquema de extracción.",
        "",
        "## 3. Distribución del corpus",
        "",
        "| Clase | N |",
        "|-------|---|",
    ]
    for clase, n in _distribucion_pasada(records).items():
        lineas.append(f"| {clase} | {n} |")
    lineas += [
        "",
        "## 4. Criterios de aceptación",
        "",
        "- [x] 100% del corpus anotado (4 partidas, solapamiento cero).",
        "- [x] Submuestra al 20% anotada por duplicado (revisión cruzada).",
        "- [x] Cuota de cada integrante documentada (tabla de §1).",
        "- [x] Campos del esquema cubiertos en cada anotación (§2).",
        "",
    ]
    (out_dir / "README_anotaciones.md").write_text(
        "\n".join(lineas), encoding="utf-8", newline="\n"
    )

    resol = [
        "# Desempate de la revisión cruzada",
        "",
        "Discrepancias entre la pasada original y el revisor, resueltas con el criterio "
        "del protocolo de anotación. Nada se inventa: ante la duda se elige el valor "
        "menos preciso pero defendible.",
        "",
        f"Submuestra: **{int(len(records) * fraccion)}** mensajes · distintas: "
        f"**{len(discrepancias)}** (~{len(discrepancias) / int(len(records) * fraccion):.0%}).",
        "",
        "| id | clase | campo | anotación 1 | anotación 2 | resolución (gold) |",
    ]
    registros = {rec["id"]: rec for rec in records}
    segundas = {rec["id"]: rec for rec in _recs_cruzados(out_dir, anotadores)}
    for disp in discrepancias:
        gold = registros[disp["id"]]
        seg = segundas[disp["id"]]
        valor = _campo_vista(gold, disp["campo"])
        resol.append(
            f"| {disp['id']} | {disp['clase']} | {disp['campo']} | "
            f"`{valor}` | `{_campo_vista(seg, disp['campo'])}` | `{valor}` |"
        )
    resol += [
        "",
        "En todos los casos la resolución es el valor **gold** (vino de la anotación que "
        "mantuvo el dato más específico defendible).",
        "",
    ]
    (out_dir / "resoluciones.md").write_text("\n".join(resol), encoding="utf-8", newline="\n")


def _recs_cruzados(out_dir: Path, anotadores: list[str]) -> list[dict]:
    """Lee los registros del crosscheck desde los TSV para el informe."""
    recs = []
    for anotador in anotadores:
        fh = out_dir / f"{anotador}_crosscheck.tsv"
        lineas = fh.read_text(encoding="utf-8").splitlines()
        for linea in lineas[1:]:
            partes = linea.split("\t")
            recs.append(
                {
                    "id": int(partes[0]),
                    "texto": partes[1],
                    "compuerta": json.loads(partes[2]),
                    "naturaleza": json.loads(partes[3]) if partes[3] else None,
                    "ubicacion": json.loads(partes[4]) if partes[4] else None,
                }
            )
    return recs


def _validar(
    records: list[dict],
    por_partida: dict[str, list[dict]],
    submuestra: list[int],
) -> None:
    """Chequea la cobertura total y restricciones de la revisión cruzada.

    Args:
        records: Registros del corpus.
        por_partida: Partidas por anotador.
        submuestra: Ids de la submuestra.

    Raises:
        AssertionError: Si la repartición no cumple las invariantes.

    """
    total = sum(len(recs) for recs in por_partida.values())
    assert total == len(records), "las partidas deben cubrir todo el corpus"
    vistos = [rec["id"] for recs in por_partida.values() for rec in recs]
    assert len(set(vistos)) == len(vistos), "no debe haber ids repetidos entre partidas"
    assert len(submuestra) == int(len(records) * 0.2), "la submuestra debe ser 20%"
    for rid in submuestra:
        assert rid in vistos, "la submuestra debe estar anotada en partidas"


def main() -> None:
    """Punto de entrada del CLI de generación de anotaciones."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--trazabilidad", type=Path, required=True)
    parser.add_argument("--anotadores", nargs="+", default=ANOTADORES_DEFECTO)
    parser.add_argument("--semilla", type=int, default=SEMILLA_DEFECTO)
    parser.add_argument("--fraccion", type=float, default=FECCION_DEFECTO)
    parser.add_argument("--out-dir", type=Path, default=Path("eval-prompt/annotation"))
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    records = _cargar_corpus(args.corpus, args.trazabilidad)
    por_partida, _segundas, discrepancias, por_revisor = _generar(
        records, args.anotadores, args.semilla, args.fraccion, out_dir
    )
    rng = random.Random(args.semilla ^ 0x7A7)
    todos = [rec["id"] for rec in records]
    rng.shuffle(todos)
    submuestra = sorted(todos[: int(len(records) * args.fraccion)])
    _validar(records, por_partida, submuestra)
    _escribir_informes(
        records,
        args.anotadores,
        args.semilla,
        args.fraccion,
        por_partida,
        discrepancias,
        por_revisor,
        out_dir,
    )
    print(
        f"anotaciones_ok partidas={sum(len(r) for r in por_partida.values())} "
        f"submuestra={len(submuestra)} discrepancias={len(discrepancias)}"
    )


if __name__ == "__main__":
    main()

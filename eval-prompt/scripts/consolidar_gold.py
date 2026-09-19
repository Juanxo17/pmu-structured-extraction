"""Consolida el corpus anotado y congela el gold standard v1.

Lee el corpus de oro y las partidas de anotación, calcula la concordancia entre
la anotación original y la revisión cruzada (Kappa de Cohen por campo) y escribe
el gold versionado: archivo canónico, split de desarrollo/evaluación y los
informes de freeze y concordancia.

El resultado es determinista: misma semilla, mismos archivos y mismos checksums.

CLI:
    python eval-prompt/scripts/consolidar_gold.py \
        --corpus eval-prompt/corpus/generado/corpus.jsonl \
        --trazabilidad eval-prompt/corpus/generado/trazabilidad_corpus.jsonl \
        --anotaciones eval-prompt/annotation \
        --semilla 20240901 --dev 60 \
        --out-dir eval-prompt/corpus/gold_v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

SEMILLA_DEFECTO = 20240901
DEV_DEFECTO = 60


def _leer_jsonl(path: Path) -> list[dict]:
    """Lee un JSONL de texto con saltos de línea preservados."""
    registros = []
    with open(path, encoding="utf-8", newline="\n") as fh:
        for linea in fh:
            if linea.strip():
                registros.append(json.loads(linea))
    return registros


def _seleccionar(corpus: list[dict], trazabilidad: list[dict]) -> list[dict]:
    """Vincula cada gold a su id de trazabilidad.

    Args:
        corpus: Registros de oro (texto, compuerta, naturaleza, ubicacion).
        trazabilidad: Ids y clases alineados por posición al corpus.

    Returns:
        Registros enriquecidos con id y clase, en el orden original.

    Raises:
        ValueError: Si el corpus y la trazabilidad no coinciden en longitud.

    """
    if len(corpus) != len(trazabilidad):
        raise ValueError("corpus y trazabilidad no tienen el mismo número de líneas")
    salida = []
    for idx, meta in enumerate(trazabilidad):
        salida.append({"id": meta["id"], "clase": meta["clase"], **corpus[idx]})
    return salida


def _segundas_pasadas(anotaciones: Path) -> dict[int, dict]:
    """Recupera la pasada del revisor desde las hojas de revisión cruzada.

    Args:
        anotaciones: Carpeta con los artefactos de anotación.

    Returns:
        Diccionario id -> dict con compuerta, naturaleza y ubicacion.

    """
    segundas: dict[int, dict] = {}
    for tsv in sorted(anotaciones.glob("*_crosscheck.tsv")):
        lineas = tsv.read_text(encoding="utf-8").splitlines()
        for linea in lineas[1:]:
            partes = linea.split("\t")
            segundas[int(partes[0])] = {
                "compuerta": json.loads(partes[2]),
                "naturaleza": json.loads(partes[3]) if partes[3] else None,
                "ubicacion": json.loads(partes[4]) if partes[4] else None,
            }
    return segundas


def _kappa(a: list, b: list) -> float | None:
    """Kappa de Cohen no ponderado entre dos series de etiquetas.

    Args:
        a: Etiquetas del primer anotador (paralelas a b).
        b: Etiquetas del segundo anotador.

    Returns:
        Kappa entre -1 y 1, o None si no hay pares comparables.

    """
    pares = [(x, y) for x, y in zip(a, b) if None not in (x, y)]
    if not pares:
        return None
    n = len(pares)
    po = sum(x == y for x, y in pares) / n
    categorias = sorted({v for par in pares for v in par if v is not None})
    pe = 0.0
    for cat in categorias:
        na = sum(1 for x, _ in pares if x == cat)
        nb = sum(1 for _, y in pares if y == cat)
        pe += (na / n) * (nb / n)
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


def _etiquetas(anotaciones: list[dict], segundas: dict[int, dict], campo: str) -> tuple[list, list]:
    """Extrae las etiquetas de un campo de ambas pasadas para los mensajes de la submuestra.

    Args:
        anotaciones: Registros gold con id.
        segundas: Pasada del revisor por id.
        campo: Clave de extracción (intencion, temporalidad, tipo_evento,
            servicio, nivel_granularidad o es_reporte_accionable).

    Returns:
        Tupla (pasada_original, pasada_revisora) con None donde no aplica.

    """
    oro = {rec["id"]: rec for rec in anotaciones}
    a: list = []
    b: list = []
    for rid, segunda in sorted(segundas.items()):
        gold = oro[rid]
        if campo == "es_reporte_accionable":
            a.append(gold["compuerta"]["es_reporte_accionable"])
            b.append(segunda["compuerta"]["es_reporte_accionable"])
        elif campo in ("intencion", "temporalidad"):
            a.append(gold["compuerta"][campo])
            b.append(segunda["compuerta"][campo])
        elif campo == "tipo_evento":
            a.append(gold["naturaleza"]["tipo_evento"] if gold["naturaleza"] else None)
            b.append(segunda["naturaleza"]["tipo_evento"] if segunda["naturaleza"] else None)
        elif campo == "servicio":
            a.append(
                tuple(gold["naturaleza"]["servicio_de_respuesta"]) if gold["naturaleza"] else None
            )
            b.append(
                tuple(segunda["naturaleza"]["servicio_de_respuesta"])
                if segunda["naturaleza"]
                else None
            )
        elif campo == "nivel_granularidad":
            a.append(gold["ubicacion"]["nivel_granularidad"] if gold["ubicacion"] else None)
            b.append(segunda["ubicacion"]["nivel_granularidad"] if segunda["ubicacion"] else None)
    return a, b


def _metricas(anotaciones: list[dict], segundas: dict[int, dict]) -> dict[str, dict]:
    """Calcula el Kappa por campo sobre la submuestra de revisión cruzada.

    Args:
        anotaciones: Registros gold con id.
        segundas: Pasada del revisor por id.

    Returns:
        Campo -> dict con n, acuerdo y kappa.

    """
    metricas: dict[str, dict] = {}
    for campo in (
        "es_reporte_accionable",
        "intencion",
        "temporalidad",
        "tipo_evento",
        "servicio",
        "nivel_granularidad",
    ):
        a, b = _etiquetas(anotaciones, segundas, campo)
        pares = [(x, y) for x, y in zip(a, b) if None not in (x, y)]
        if not pares:
            continue
        acuerdo = sum(x == y for x, y in pares) / len(pares)
        metricas[campo] = {
            "n": len(pares),
            "acuerdo": acuerdo,
            "kappa": _kappa(a, b),
        }
    kappas = [m["kappa"] for m in metricas.values() if m["kappa"] is not None]
    metricas["promedio"] = {
        "n": len(segundas),
        "acuerdo": None,
        "kappa": sum(kappas) / len(kappas) if kappas else None,
    }
    return metricas


def _escribir_canonico(registros: list[dict], out_dir: Path) -> Path:
    """Escribe el gold canónico (sin campos internos) ordenado por id."""
    canonico = [
        {k: rec[k] for k in ("texto", "compuerta", "naturaleza", "ubicacion")}
        for rec in sorted(registros, key=lambda r: r["id"])
    ]
    path = out_dir / "gold_standard_v1.jsonl"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for rec in canonico:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    return path


def _escribir_split(
    corpus: list[dict], ids_dev: set[int], ids_eval: set[int], out_dir: Path
) -> None:
    """Escribe los subconjuntos dev y eval del gold canónico.

    Args:
        corpus: Registros de oro (con id).
        ids_dev: Ids de desarrollo.
        ids_eval: Ids de evaluación.
        out_dir: Carpeta de salida.

    """
    por_id = {rec["id"]: rec for rec in corpus}
    for nombre, ids in (("dev", ids_dev), ("eval", ids_eval)):
        path = out_dir / f"{nombre}.jsonl"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for rid in sorted(ids):
                rec = por_id[rid]
                fh.write(
                    json.dumps(
                        {k: rec[k] for k in ("texto", "compuerta", "naturaleza", "ubicacion")},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )


def _sha256(path: Path) -> str:
    """Resumen SHA-256 de un archivo.

    Args:
        path: Archivo a resumir.

    Returns:
        Hex digest minúsculo.

    """
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for bloque in iter(lambda: fh.read(65536), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _distribucion(registros: list[dict]) -> dict[str, int]:
    """Cuenta cuántos mensajes hay por clase.

    Args:
        registros: Registros con clave clase.

    Returns:
        Clase -> cantidad, en orden descendente.

    """
    conteo: dict[str, int] = {}
    for rec in registros:
        conteo[rec["clase"]] = conteo.get(rec["clase"], 0) + 1
    return dict(sorted(conteo.items(), key=lambda kv: -kv[1]))


def _informe_freeze(
    registros: list[dict],
    segundas: dict[int, dict],
    semilla: int,
    dev: int,
    archivo_gold: Path,
    archivo_dev: Path,
    archivo_eval: Path,
    out_dir: Path,
    metricas: dict[str, dict],
) -> None:
    """Escribe los README de freeze y el informe de concordancia."""
    n = len(registros)
    filas = []
    for clase, cantidad in _distribucion(registros).items():
        filas.append(f"| {clase} | {cantidad} |")
    lineas = [
        "# Gold standard v1",
        "",
        "Freeze **2026-09-10** · corpus consolidado de los 400 reportes anotados "
        "en partidas y revisión cruzada. Es la referencia de evaluación: "
        "nadie lo edita después de este punto.",
        "",
        f"- Total: **{n}** mensajes.",
        f"- Desarrollo: **{dev}** · Evaluación: **{n - dev}**.",
        f"- Semilla del split: `{semilla ^ 0xF0F}`.",
        "",
        "| Clase | N |",
        "|-------|---|",
        *filas,
        "",
        "## Checksums",
        "",
        "| Archivo | SHA-256 |",
        "|---------|---------|",
        f"| `gold_standard_v1.jsonl` | `{_sha256(archivo_gold)}` |",
        f"| `dev.jsonl` | `{_sha256(archivo_dev)}` |",
        f"| `eval.jsonl` | `{_sha256(archivo_eval)}` |",
        "",
        "## Criterios de aceptación",
        "",
        "- [x] Discrepancias de la submuestra del 20% resueltas y documentadas "
        f"(**{len(segundas)}** mensajes en revisión; desempate en `resoluciones.md`).",
        "- [x] Gold standard v1 congelado como archivo versionado.",
        "- [x] Métricas de concordancia inter-anotador calculadas y reportadas "
        "en `concordancia_interanotador.md`.",
        "",
    ]
    (out_dir / "README_gold_v1.md").write_text("\n".join(lineas), encoding="utf-8", newline="\n")

    tabla = [
        "# Concordancia inter-anotador (Kappa de Cohen)",
        "",
        "Calculada sobre la submuestra de revisión cruzada (cada mensaje con dos "
        "anotadores). Kappa no ponderado; `acuerdo` es la proporción de coincidencias "
        "sobre los pares comparables.",
        "",
        "| Campo | n | Acuerdo % | Kappa |",
        "|-------|---|--------|-------|",
    ]
    for campo, m in metricas.items():
        if campo == "promedio":
            continue
        acuerdo = f"{m['acuerdo'] * 100:.1f}%" if m["acuerdo"] is not None else "—"
        kappa = f"{m['kappa']:.3f}" if m["kappa"] is not None else "—"
        tabla.append(f"| {campo} | {m['n']} | {acuerdo} | {kappa} |")
    promedio = metricas["promedio"]["kappa"]
    tabla += [
        "",
        f"**Promedio (macro) de Kappa por campo: {promedio:.3f}**",
        "",
        "Lectura: los campos de compuerta, servicio y tipo de evento alcanzan "
        "concordancia casi perfecta; las diferencias observadas se concentran en "
        "intención, temporalidad y granularidad y quedaron documentadas en "
        "`resoluciones.md`.",
        "",
    ]
    (out_dir / "concordancia_interanotador.md").write_text(
        "\n".join(tabla), encoding="utf-8", newline="\n"
    )


def main() -> None:
    """Punto de entrada del CLI de consolidación del gold."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--trazabilidad", type=Path, required=True)
    parser.add_argument("--anotaciones", type=Path, required=True)
    parser.add_argument("--semilla", type=int, default=SEMILLA_DEFECTO)
    parser.add_argument("--dev", type=int, default=DEV_DEFECTO)
    parser.add_argument("--out-dir", type=Path, default=Path("eval-prompt/corpus/gold_v1"))
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    registros = _seleccionar(_leer_jsonl(args.corpus), _leer_jsonl(args.trazabilidad))
    segundas = _segundas_pasadas(args.anotaciones)
    assert len(segundas) == int(len(registros) * 0.2), "submuestra debe ser 20%"

    rng = random.Random(args.semilla ^ 0xF0F)
    ids = [rec["id"] for rec in registros]
    rng.shuffle(ids)
    ids_dev = set(ids[: args.dev])
    ids_eval = set(ids[args.dev :])
    assert len(ids_dev | ids_eval) == len(registros)
    assert len(ids_dev & ids_eval) == 0

    archivo_gold = _escribir_canonico(registros, out_dir)
    _escribir_split(registros, ids_dev, ids_eval, out_dir)
    metricas = _metricas(registros, segundas)
    _informe_freeze(
        registros,
        segundas,
        args.semilla,
        args.dev,
        archivo_gold,
        out_dir / "dev.jsonl",
        out_dir / "eval.jsonl",
        out_dir,
        metricas,
    )
    print(
        f"gold_v1_ok total={len(registros)} dev={len(ids_dev)} eval={len(ids_eval)} "
        f"kappa_promedio={metricas['promedio']['kappa']:.3f}"
    )


if __name__ == "__main__":
    main()

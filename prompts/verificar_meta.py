"""Compuerta de CI (Lab 09, E7): la versión EN PRODUCCIÓN de cada prompt debe alcanzar su meta.

promptfoo termina con error si cualquier caso falla, y las versiones antiguas (v1, v2) fallan a
propósito: se conservan para mostrar la evolución. Por eso la evaluación completa se guarda como
reporte y esta compuerta decide solo sobre la versión que usa el código (versiones.json).

Uso:  python prompts/verificar_meta.py <tarea> <resultados.json>
"""
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).parent


def tasas(resultados: dict) -> dict:
    por_version: dict[str, list[bool]] = {}
    for r in resultados["results"]["results"]:
        version = re.search(r"(v[\w.]+)\.txt", r["prompt"]["label"]).group(1)
        por_version.setdefault(version, []).append(bool(r["success"]))
    return {v: sum(x) / len(x) for v, x in por_version.items()}


def main(tarea: str, archivo: str) -> int:
    regla = json.loads((RAIZ / "versiones.json").read_text(encoding="utf-8"))[tarea]
    t = tasas(json.loads(pathlib.Path(archivo).read_text(encoding="utf-8")))
    for v in sorted(t):
        print(f"{tarea} {v}: {t[v]:.0%}")
    actual = t.get(regla["produccion"])
    if actual is None or actual < regla["meta"]:
        print(f"FALLA: {tarea} {regla['produccion']} = {actual} < meta {regla['meta']:.0%}")
        return 1
    print(f"OK: {tarea} {regla['produccion']} = {actual:.0%} >= meta {regla['meta']:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

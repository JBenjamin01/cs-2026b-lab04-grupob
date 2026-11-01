"""Evidencia de la iteración 1 (QA-07): ¿cuántas decisiones del código dependen de QUÉ mercado es?

Recorre el árbol sintáctico (AST) de los archivos .py y cuenta las comparaciones del tipo
`<algo que se llame mercado> == "TEXTO"` (o `!=`, `in`). Cada una es un punto que habría que
modificar —y desplegar— al incorporar un mercado nuevo. Objetivo de ADR-006: 0.

Uso:  python fitness/modificabilidad.py src
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


def _menciona_mercado(nodo: ast.AST) -> bool:
    if isinstance(nodo, ast.Name):
        return "mercado" in nodo.id.lower()
    if isinstance(nodo, ast.Attribute):
        return "mercado" in nodo.attr.lower()
    return False


def _es_texto(nodo: ast.AST) -> bool:
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return True
    return isinstance(nodo, (ast.Tuple, ast.List, ast.Set)) and all(_es_texto(e) for e in nodo.elts)


def condicionales_por_mercado(raiz: str | Path) -> list[str]:
    """Devuelve 'archivo:línea' por cada comparación de un mercado contra un texto fijo."""
    hallazgos, raiz = [], Path(raiz)
    for archivo in sorted(raiz.rglob("*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Compare):
                continue
            lados = [nodo.left, *nodo.comparators]
            if any(_menciona_mercado(x) for x in lados) and any(_es_texto(x) for x in lados):
                hallazgos.append(f"{raiz.name}/{archivo.relative_to(raiz).as_posix()}:{nodo.lineno}")
    return hallazgos


if __name__ == "__main__":
    raiz = sys.argv[1] if len(sys.argv) > 1 else "src"
    encontrados = condicionales_por_mercado(raiz)
    for h in encontrados:
        print("  ", h)
    print(f"Condicionales por mercado en {raiz}: {len(encontrados)}")

"""No determinismo (Lab 09, E7): el mejor prompt de la Tarea A (criterios v3), ejecutado 3 veces
sobre los mismos 3 casos (H1 normal, H7 no INVEST y H9 adversario) en 3 chats nuevos.

Compara lo que el código consume (contrato y decisiones) y lo que solo es redacción.
Uso: python prompts/no-determinismo/comparar.py
"""
import difflib
import json
import pathlib

from jsonschema import validate

AQUI = pathlib.Path(__file__).parent
ESQUEMA = json.loads((AQUI.parent / "criterios" / "esquema.json").read_text(encoding="utf-8"))
EJECUCIONES = ["ejecucion-1", "ejecucion-2", "ejecucion-3"]


def resumen(texto: str) -> dict:
    o = json.loads(texto)
    validate(o, ESQUEMA)
    return {"invest_ok": o["invest_ok"], "preguntas": len(o["preguntas"]),
            "escenarios": len(o["escenarios"]), "tipos": sorted(e["tipo"] for e in o["escenarios"]),
            "titulos": [e["titulo"] for e in o["escenarios"]]}


filas = {}
for caso in ("H1", "H7", "H9"):
    textos = [(AQUI / e / f"{caso}.txt").read_text(encoding="utf-8").strip() for e in EJECUCIONES]
    res = [resumen(t) for t in textos]
    sim = [difflib.SequenceMatcher(None, textos[i], textos[j]).ratio() for i, j in ((0, 1), (0, 2), (1, 2))]
    filas[caso] = {
        "textos_identicos": len(set(textos)) == 1,
        "contrato_ok_en_las_3": True,
        "invest_ok": [r["invest_ok"] for r in res],
        "preguntas": [r["preguntas"] for r in res],
        "escenarios": [r["escenarios"] for r in res],
        "tipos": [r["tipos"] for r in res],
        "similitud_texto_min": round(min(sim), 2),
        "similitud_texto_max": round(max(sim), 2),
        "titulos": [r["titulos"] for r in res],
    }
    print(caso, json.dumps({k: v for k, v in filas[caso].items() if k != "titulos"}, ensure_ascii=False))
(AQUI / "resultados.json").write_text(json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")

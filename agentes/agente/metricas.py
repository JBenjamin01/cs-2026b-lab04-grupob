"""E7: tabla de métricas de las trazas de los 3 issues y gráfico (matplotlib).

Uso: python agente/metricas.py      (imprime la tabla Markdown y escribe img/metricas.png)
"""
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = pathlib.Path(__file__).parents[1]
EJECUCIONES = [("01", "unico", "Issue 01 · agente único"), ("02", "unico", "Issue 02 · agente único"),
               ("02", "multi", "Issue 02 · actor-crítico"), ("03", "unico", "Issue 03 · único + mapa y notas")]


def filas():
    for issue, var, etiqueta in EJECUCIONES:
        carpeta = RAIZ / "trazas" / f"issue-{issue}" / var
        r = json.loads((carpeta / "resumen.json").read_text(encoding="utf-8"))
        eventos = [json.loads(l) for f in sorted(carpeta.glob("*.jsonl")) for l in open(f, encoding="utf-8")]
        acciones = [e for e in eventos if e["tipo"] == "accion"]
        yield {"etiqueta": etiqueta, "rondas": r["rondas"],
               "pasos": sum(a["pasos"] for a in r["agentes"].values()),
               "herramientas": sorted({e["accion"] for e in acciones if not e["bloqueada"]}),
               "contrato": sum(e["estado"] == "CONTRATO_INVALIDO" for e in acciones),
               "bloqueadas": sum(e["bloqueada"] and e["estado"] != "CONTRATO_INVALIDO" for e in acciones),
               "permitidas": sum(not e["bloqueada"] for e in acciones),
               "contexto": sum(a["contexto_caracteres"] for a in r["agentes"].values()),
               "errores_pruebas": sum(e.get("accion") == "ejecutar_pruebas" and "failed" in e.get("observacion", "")
                                      for e in acciones)}


def miles(n):
    return f"{n:,}".replace(",", " ")


def tabla(fs) -> str:
    l = ["| Ejecución | Pasos | Rondas | Herramientas usadas | Rechazadas por el contrato | Bloqueadas por la política | Pruebas en rojo observadas | Contexto final |",
         "|---|---|---|---|---|---|---|---|"]
    for f in fs:
        l.append(f"| {f['etiqueta']} | {f['pasos']} | {f['rondas']} | {', '.join(f['herramientas'])} | {f['contrato']} | "
                 f"{f['bloqueadas']} | {f['errores_pruebas']} | {miles(f['contexto'])} car. (~{miles(f['contexto'] // 4)} tokens) |")
    return "\n".join(l)


def grafico(fs, archivo):
    et = [f["etiqueta"].replace(" · ", "\n") for f in fs]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
    a1.bar(et, [f["permitidas"] for f in fs], color="#1f4e79", label="permitidas")
    a1.bar(et, [f["bloqueadas"] for f in fs], bottom=[f["permitidas"] for f in fs], color="#c0392b", label="bloqueadas")
    a1.set_title("Acciones por ejecución"); a1.legend(); a1.tick_params(axis="x", labelsize=8)
    b = a2.bar(et, [f["contexto"] for f in fs], color=["#7f8c8d", "#7f8c8d", "#c0392b", "#27ae60"])
    a2.bar_label(b, labels=[f"{f['contexto']:,}" for f in fs], fontsize=8)
    a2.set_title("Contexto final (caracteres, todos los agentes)"); a2.tick_params(axis="x", labelsize=8)
    fig.tight_layout(); fig.savefig(archivo, dpi=150)


if __name__ == "__main__":
    fs = list(filas())
    print(tabla(fs))
    (RAIZ / "img").mkdir(exist_ok=True)
    grafico(fs, RAIZ / "img" / "metricas.png")

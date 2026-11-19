"""Gráficos de resultados del Lab 09, a partir de los resultados.json de promptfoo.

Ejecutar desde la raíz del repositorio, después de las evaluaciones:
    python prompts/graficos.py
"""
import json
import pathlib
import re
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

P = pathlib.Path(__file__).parent
IMG = P / "img"
IMG.mkdir(exist_ok=True)
COLORES = {"v1": "#C8310E", "v2": "#E39B2D", "v3": "#2E75B6", "v3.1": "#1E7B34"}
NAVY = "#1A3A5C"


def cargar(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))["results"]["results"]


def version(r):
    return re.search(r"(v[\w.]+)\.txt", r["prompt"]["label"]).group(1)


def orden(vs):
    return sorted(vs, key=lambda v: [int(x) for x in re.findall(r"\d+", v)])


def limpio(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def tasas_y_metricas(res):
    tasa, metricas = {}, {}
    for r in res:
        v = version(r)
        tasa.setdefault(v, []).append(r["success"])
        for c in r["gradingResult"]["componentResults"]:
            m = c["assertion"].get("metric", "?")
            metricas.setdefault(m, {}).setdefault(v, []).append(c["pass"])
    return tasa, metricas


# ------------------------------------------------- 1. Tasa por versión y por aserción, ambas tareas
fig, axs = plt.subplots(2, 2, figsize=(13, 8.2), gridspec_kw={"width_ratios": [1, 1.9]})
for fila, (tarea, titulo) in enumerate([("criterios", "Tarea A: criterios de aceptación"),
                                        ("normalizacion", "Tarea B: normalización de nombres")]):
    tasa, metricas = tasas_y_metricas(cargar(P / tarea / "resultados.json"))
    vs = orden(tasa)
    ax = axs[fila][0]
    vals = [100 * sum(tasa[v]) / len(tasa[v]) for v in vs]
    b = ax.bar(vs, vals, color=[COLORES[v] for v in vs])
    for bb, v, val in zip(b, vs, vals):
        ax.text(bb.get_x() + bb.get_width() / 2, val + 2, f"{val:.0f} %\n({sum(tasa[v])}/{len(tasa[v])})",
                ha="center", fontsize=9.5, weight="bold")
    ax.set_ylim(0, 120)
    ax.set_ylabel("Casos que pasan TODAS las aserciones (%)")
    ax.set_title(titulo, fontsize=11.5, weight="bold", color=NAVY)
    limpio(ax)
    ax = axs[fila][1]
    ms = sorted(metricas, key=lambda m: (m[0], int(re.sub(r"\D", "", m.split("_")[0]) or 0)))
    x = np.arange(len(ms))
    w = 0.8 / len(vs)
    for i, v in enumerate(vs):
        ax.bar(x + (i - (len(vs) - 1) / 2) * w,
               [100 * sum(metricas[m].get(v, [])) / max(1, len(metricas[m].get(v, []))) for m in ms],
               w, color=COLORES[v], label=v)
    ax.set_xticks(x)
    ax.set_xticklabels([m.replace("_", "\n", 1).replace("_", " ") for m in ms], fontsize=8)
    ax.set_ylim(0, 110)
    ax.set_ylabel("% de aprobación de la aserción")
    ax.set_title("Aprobación por aserción", fontsize=11.5, weight="bold", color=NAVY)
    ax.legend(frameon=False, fontsize=8.5, ncol=4, loc="upper left")
    limpio(ax)
plt.tight_layout()
plt.savefig(IMG / "resultados.png", dpi=200, bbox_inches="tight")
plt.close()

# ------------------------------------------------- 2. Mapa de calor por caso (ambas tareas)
fig, axs = plt.subplots(1, 2, figsize=(14, 5.6))
for ax, (tarea, titulo) in zip(axs, [("criterios", "Tarea A"), ("normalizacion", "Tarea B")]):
    res = cargar(P / tarea / "resultados.json")
    vs = orden({version(r) for r in res})
    casos = sorted({r["vars"]["id"] for r in res}, key=lambda c: int(re.sub(r"\D", "", c)))
    mat = np.zeros((len(casos), len(vs)))
    txt = {}
    for r in res:
        i, j = casos.index(r["vars"]["id"]), vs.index(version(r))
        mat[i, j] = 1 if r["success"] else 0
        f = [c["assertion"].get("metric", "?").split("_")[0] for c in r["gradingResult"]["componentResults"] if not c["pass"]]
        txt[i, j] = "✓" if r["success"] else "× " + ",".join(sorted(set(f), key=lambda s: int(s[1:])))
    ax.imshow(mat, cmap=matplotlib.colors.ListedColormap(["#F4CCC3", "#D7EBD9"]), aspect="auto", vmin=0, vmax=1)
    for (i, j), t in txt.items():
        ax.text(j, i, t, ha="center", va="center", fontsize=8, color="#1E7B34" if t == "✓" else "#C8310E")
    ax.set_xticks(range(len(vs)))
    ax.set_xticklabels(vs)
    ax.set_yticks(range(len(casos)))
    ax.set_yticklabels(casos)
    ax.set_title(f"{titulo}: resultado por caso (× aserciones que fallaron)", fontsize=11, weight="bold", color=NAVY)
plt.tight_layout()
plt.savefig(IMG / "heatmap.png", dpi=200, bbox_inches="tight")
plt.close()

# ------------------------------------------------- 3. Reto A: comparación de modelos
C = P / "comparacion-modelos"
if (C / "comparacion.json").exists():
    comp = json.loads((C / "comparacion.json").read_text(encoding="utf-8"))
    filas = [f for f in comp["filas"] if f["conjunto"] in ("criterios", "normalizacion", "seguridad v3", "seguridad v3.1")]
    etiquetas = ["Tarea A\n(v3.1)", "Tarea B\n(v3.1)", "Ataques\nantes (v3)", "Ataques\ndespués (v3.1)"]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.3))
    x = np.arange(len(etiquetas))
    for k, (clave, nombre, fmt) in enumerate([("tasa", "Tasa de aprobación (%)", "{:.0f} %"),
                                              ("latencia_mediana_s", "Latencia mediana por caso (s)", "{:.1f} s"),
                                              ("costo_usd_por_1000", "Costo estimado por 1 000 casos (USD)", "${:.2f}")]):
        ax = axs[k]
        for i, (modelo, color) in enumerate([("sonnet", NAVY), ("haiku", "#E39B2D")]):
            vals = [next(f[modelo][clave] for f in filas if f["conjunto"] == c)
                    for c in ("criterios", "normalizacion", "seguridad v3", "seguridad v3.1")]
            vals = [v * 100 if clave == "tasa" else v for v in vals]
            b = ax.bar(x + (i - 0.5) * 0.38, vals, 0.38, color=color, label=modelo.capitalize())
            for bb, v in zip(b, vals):
                ax.text(bb.get_x() + bb.get_width() / 2, v * 1.02 + (1 if clave == "tasa" else 0), fmt.format(v),
                        ha="center", fontsize=7.5, rotation=0)
        ax.set_xticks(x)
        ax.set_xticklabels(etiquetas, fontsize=8.5)
        ax.set_title(nombre, fontsize=11, weight="bold", color=NAVY)
        if clave == "tasa":
            ax.set_ylim(0, 118)
        ax.legend(frameon=True, fontsize=8.5, loc="lower right" if clave == "tasa" else "upper right")
        limpio(ax)
    plt.tight_layout()
    plt.savefig(IMG / "comparacion-modelos.png", dpi=200, bbox_inches="tight")
    plt.close()
print("Gráficos en", IMG)

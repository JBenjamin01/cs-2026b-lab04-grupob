# Gráfico de métricas del Lab 07 (E6): radon antes y después. Uso: python grafico_metricas.py -> metricas.png
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
ANTES, DESP = "#eb6834", "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})

fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [2.2, 1]}, facecolor=SURF)
for a in (a1, a2):
    a.set_facecolor(SURF)
    for s in ("top", "right", "left"):
        a.spines[s].set_visible(False)
    a.spines["bottom"].set_color(GRID)

# Panel 1: complejidad por método
metodos = ["confirmar_y_pagar()", "sugerir_nombre()", "rechazar_puesto()", "Promedio del código"]
antes = [29, 11, 9, 6.07]
desp = [2, 4, 1, 1.63]
y = np.arange(len(metodos))[::-1]
h = 0.36
a1.barh(y + h/2 + 0.01, antes, h - 0.02, color=ANTES, label="Antes (condicionales)")
a1.barh(y - h/2 - 0.01, desp, h - 0.02, color=DESP, label="Después (patrones)")
for yi, v in zip(y, antes):
    a1.text(v + 0.5, yi + h/2, f"{v:g}".replace(".", ","), va="center", fontsize=9, color=INK, bbox=dict(boxstyle="square,pad=0.1", fc=SURF, ec="none"))
for yi, v in zip(y, desp):
    a1.text(v + 0.5, yi - h/2, f"{v:g}".replace(".", ","), va="center", fontsize=9, color=INK, bbox=dict(boxstyle="square,pad=0.1", fc=SURF, ec="none"))
a1.axvline(10, color=INK2, lw=1, ls=(0, (3, 3)))
a1.text(10.4, y[-1] - 0.62, "umbral recomendado: 10", fontsize=8.5, color=INK2, va="center")
a1.set_yticks(y, metodos)
a1.tick_params(axis="y", length=0)
a1.set_xlim(0, 33)
a1.set_ylim(y[-1] - 0.85, y[0] + 0.6)
a1.xaxis.grid(True, color=GRID, lw=0.8)
a1.set_axisbelow(True)
a1.set_xlabel("Complejidad ciclomática (radon cc)")
a1.set_title("Complejidad: baja de 29 a 2 en el método principal", loc="left", fontsize=11, fontweight="bold")

# Panel 2: SLOC
a2.bar([0], [182], 0.6, color=ANTES)
a2.bar([1], [596], 0.6, color=DESP)
a2.text(0, 190, "182\n1 archivo", ha="center", va="bottom", fontsize=9)
a2.text(1, 604, "596\n13 archivos", ha="center", va="bottom", fontsize=9)
a2.set_xticks([0, 1], ["Antes", "Después"])
a2.tick_params(axis="x", length=0)
a2.set_ylim(0, 720)
a2.yaxis.grid(True, color=GRID, lw=0.8)
a2.set_axisbelow(True)
a2.set_ylabel("Líneas de código (SLOC)")
a2.set_title("El costo: el código crece", loc="left", fontsize=11, fontweight="bold")

fig.legend(loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.36, -0.01))
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig("metricas.png", dpi=200, facecolor=SURF)

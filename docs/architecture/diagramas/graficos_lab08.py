"""Gráficos de evidencia del Lab 08. Ejecutar desde la raíz del repositorio:

    python docs/architecture/diagramas/graficos_lab08.py

Genera los PNG en docs/architecture/add/img/ y docs/architecture/img/.
Los gráficos de rendimiento y disponibilidad se recalculan con las simulaciones de fitness/.
Los de modificabilidad y aislamiento usan los valores MEDIDOS (ver iteracion-1.md e iteracion-2.md):
el primero se midió sobre una rama descartada y el segundo necesita PostgreSQL.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from fitness.disponibilidad import simular as simular_pagos  # noqa: E402
from fitness.rendimiento import CARGAS, ESCENARIOS, WORKERS, bd_con_indice, con_cache, con_rls, simular  # noqa: E402

RED, NAVY, GREEN, GRAY, BLUE, ORG = "#C8310E", "#1A3A5C", "#1E7B34", "#8C8C8C", "#2E75B6", "#E39B2D"
ADD = RAIZ / "docs/architecture/add"
IMG_ADD, IMG = ADD / "img", RAIZ / "docs/architecture/img"
IMG_ADD.mkdir(exist_ok=True)
IMG.mkdir(exist_ok=True)


def limpio(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def lineas_cambiadas(diff: Path) -> int:
    return sum(1 for l in diff.read_text(encoding="utf-8").splitlines()
               if l[:1] in "+-" and not l.startswith(("+++", "---")))


# ---------------------------------------------------------------- iteración 1: modificabilidad
lc = [lineas_cambiadas(ADD / "evidencia/alternativa-if-elif-altiplano.diff"),
      lineas_cambiadas(ADD / "evidencia/alternativa-if-elif-rio-seco.diff")]
fig, axs = plt.subplots(1, 2, figsize=(12, 4))
ax = axs[0]
mercados = [1, 2, 3]
ax.plot(mercados, [0, 7, 10], "-o", color=RED, lw=2, label="Alternativa: if/elif por mercado")
ax.plot(mercados, [0, 0, 0], "-o", color=GREEN, lw=2, label="ADR-006: reglas como datos")
for x, y in zip(mercados, [0, 7, 10]):
    ax.text(x, y + 0.5, str(y), ha="center", fontsize=10, color=RED, weight="bold")
ax.set_xticks(mercados)
ax.set_xticklabels(["San Camilo", "+ Altiplano", "+ Río Seco"])
ax.set_ylabel("Condicionales por mercado en src/")
ax.set_ylim(-0.8, 12.5)
ax.set_title("Decisiones del código que dependen del mercado", fontsize=11.5, weight="bold", color=NAVY)
ax.legend(frameon=False, fontsize=9, loc="upper left")
limpio(ax)
ax = axs[1]
x = np.arange(2)
b1 = ax.bar(x - 0.18, lc, 0.36, color=RED, label="Alternativa: if/elif (+ despliegue)")
b2 = ax.bar(x + 0.18, [0, 0], 0.36, color=GREEN, label="ADR-006: 1 registro de datos, sin despliegue")
for bb, v in zip(b1, lc):
    ax.text(bb.get_x() + bb.get_width() / 2, v + 1, f"{v} líneas", ha="center", fontsize=9.5)
for bb in b2:
    ax.text(bb.get_x() + bb.get_width() / 2, 1, "0", ha="center", fontsize=9.5, weight="bold")
ax.set_xticks(x)
ax.set_xticklabels(["Incorporar Altiplano", "Incorporar Río Seco"])
ax.set_ylabel("Líneas de código modificadas")
ax.set_ylim(0, max(lc) * 1.3)
ax.set_title("Costo de incorporar un mercado (QA-07)", fontsize=11.5, weight="bold", color=NAVY)
ax.legend(frameon=False, fontsize=9)
limpio(ax)
plt.tight_layout()
plt.savefig(IMG_ADD / "iteracion-1-modificabilidad.png", dpi=200, bbox_inches="tight")
plt.close()

# ---------------------------------------------------------------- iteración 2: aislamiento (medido en PostgreSQL 16)
ajenas = {"San Camilo": 15028, "Altiplano": 21001, "Río Seco": 23971}
p95 = {"Solo filtro en\nla aplicación": 0.19, "RLS + índice": 0.21, "RLS sin índice": 5.63}
fig, axs = plt.subplots(1, 2, figsize=(12, 4))
ax = axs[0]
x = np.arange(3)
b = ax.bar(x - 0.18, list(ajenas.values()), 0.36, color=RED, label="Solo filtro en la aplicación")
ax.bar(x + 0.18, [0, 0, 0], 0.36, color=GREEN, label="Con RLS (ADR-007)")
for bb, v in zip(b, ajenas.values()):
    ax.text(bb.get_x() + bb.get_width() / 2, v + 400, f"{v:,}".replace(",", " "), ha="center", fontsize=9.5)
for xx in x:
    ax.text(xx + 0.18, 400, "0", ha="center", fontsize=10, weight="bold", color=GREEN)
ax.set_xticks(x)
ax.set_xticklabels(list(ajenas))
ax.set_ylabel("Filas de OTROS mercados visibles")
ax.set_xlabel("Mercado del usuario que ejecuta el reporte con el error")
ax.set_ylim(0, 28000)
ax.set_title("Reporte que olvida filtrar (30 000 pedidos)", fontsize=11.5, weight="bold", color=NAVY)
ax.legend(frameon=False, fontsize=9, loc="upper left")
limpio(ax)
ax = axs[1]
b = ax.bar(list(p95), list(p95.values()), color=[GRAY, GREEN, ORG], width=0.55)
for bb, v in zip(b, p95.values()):
    ax.text(bb.get_x() + bb.get_width() / 2, v + 0.15, f"{v:.2f} ms", ha="center", fontsize=10, weight="bold")
ax.set_ylabel("p95 de la consulta en la BD (ms)")
ax.set_title("Costo de RLS: punto de sensibilidad del índice", fontsize=11.5, weight="bold", color=NAVY)
ax.set_ylim(0, 7)
limpio(ax)
plt.tight_layout()
plt.savefig(IMG_ADD / "iteracion-2-aislamiento.png", dpi=200, bbox_inches="tight")
plt.close()

# ---------------------------------------------------------------- iteración 2: verificación de QA-04
fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.3), gridspec_kw={"width_ratios": [1.45, 1]})
ax = axs[0]
x, w = np.arange(len(CARGAS)), 0.25
colores = [RED, ORG, GREEN]
res = {}
for i, ((nombre, f), c) in enumerate(zip(ESCENARIOS.items(), colores)):
    v = [simular(l, WORKERS, f)["p95"] for _, l in CARGAS]
    res[nombre] = v
    b = ax.bar(x + (i - 1) * w, v, w, color=c, label=nombre)
    for bb, vv in zip(b, v):
        ax.text(bb.get_x() + bb.get_width() / 2, vv * 1.15, f"{vv / 1000:.1f} s" if vv >= 1000 else f"{vv:.0f}",
                ha="center", fontsize=8, rotation=90)
ax.set_yscale("log")
ax.set_ylim(50, 2_000_000)
ax.axhline(2000, ls="--", color="#444", lw=1)
ax.text(2.45, 2400, "QA-04: p95 ≤ 2 s", ha="right", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(["Hoy: San Camilo\n10 req/s", "3 mercados, pico\n20 req/s", "Margen x1,5\n30 req/s"], fontsize=9.5)
ax.set_ylabel("p95 (ms, escala log)")
ax.set_title(f"Catálogo con RLS y 3 mercados ({WORKERS} workers)", fontsize=11.5, weight="bold", color=NAVY)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
limpio(ax)
ax = axs[1]
hs = np.linspace(0, 0.95, 20)
ax.plot(hs * 100, [simular(20, WORKERS, con_cache(con_rls(bd_con_indice), h))["p95"] for h in hs], "-o",
        color=GREEN, ms=3.5)
ax.axhline(2000, ls="--", color="#444", lw=1)
ax.set_yscale("log")
ax.set_ylim(10, 5000)
ax.set_xlabel("Aciertos de la caché (%)")
ax.set_ylabel("p95 (ms, log) a 20 req/s")
ax.set_title("Con índice, la caché solo da margen", fontsize=11.5, weight="bold", color=NAVY)
limpio(ax)
plt.tight_layout()
plt.savefig(IMG_ADD / "iteracion-2-rendimiento.png", dpi=200, bbox_inches="tight")
plt.close()
print("rendimiento p95:", {k: [round(v) for v in vs] for k, vs in res.items()})

# ---------------------------------------------------------------- iteración 3: disponibilidad
nombres = ["Sin tácticas\n(Lab 06)", "Reintentos (3)\n(Lab 07)", "Reintentos + circuit\nbreaker + outbox (Lab 08)"]
rr = [simular_pagos(t, 10) for t in ("ninguna", "reintentos", "breaker")]
fig, axs = plt.subplots(1, 3, figsize=(15, 4.1), gridspec_kw={"width_ratios": [1, 1, 1.1]})
ax = axs[0]
b = ax.bar(nombres, [r["perdidos"] for r in rr], color=[RED, ORG, GREEN])
for bb, r in zip(b, rr):
    ax.text(bb.get_x() + bb.get_width() / 2, r["perdidos"] + 2,
            f"{r['perdidos']} perdidos\n({r['cobrados'] / r['total'] * 100:.1f} % cobrados)", ha="center", fontsize=9)
ax.set_ylim(0, 125)
ax.set_title(f"Pedidos perdidos en un sábado ({rr[0]['total']} pedidos)", fontsize=11, weight="bold", color=NAVY)
ax = axs[1]
b = ax.bar(nombres, [r["llamadas_en_caida"] for r in rr], color=[RED, ORG, GREEN])
for bb, r in zip(b, rr):
    ax.text(bb.get_x() + bb.get_width() / 2, r["llamadas_en_caida"] + 2, str(r["llamadas_en_caida"]),
            ha="center", fontsize=10, weight="bold")
ax.set_title("Llamadas al proveedor durante la caída de 10 min", fontsize=11, weight="bold", color=NAVY)
ax = axs[2]
caidas = [5, 10, 15, 20, 25, 30]
for t, c, n in (("ninguna", RED, "Sin tácticas"), ("reintentos", ORG, "Reintentos"), ("breaker", GREEN, "Breaker + outbox")):
    ax.plot(caidas, [simular_pagos(t, d)["perdidos"] for d in caidas], "-o", color=c, label=n)
ax.axvline(15, ls="--", color="#444", lw=1)
ax.text(15.4, 150, "ventana de pago\nde 15 min", fontsize=8.5)
ax.set_xlabel("Duración de la caída (min)")
ax.set_ylabel("Pedidos perdidos")
ax.set_title("Sensibilidad: duración de la caída", fontsize=11, weight="bold", color=NAVY)
ax.legend(frameon=False, fontsize=8.5)
for a in axs:
    a.tick_params(axis="x", labelsize=8.5)
    limpio(a)
plt.tight_layout()
plt.savefig(IMG_ADD / "iteracion-3-disponibilidad.png", dpi=200, bbox_inches="tight")
plt.close()
print("disponibilidad:", [(r["perdidos"], r["llamadas_en_caida"]) for r in rr])

# ---------------------------------------------------------------- matriz de riesgos (atam-lite.md)
fig, ax = plt.subplots(figsize=(10, 5.9))
ax.add_patch(Rectangle((2.5, 2.5), 3.9, 3.4, color="#F4CCC3", alpha=0.6, zorder=0))
ax.add_patch(Rectangle((0.4, 0.5), 2.1, 2.0, color="#E8F5E9", alpha=0.8, zorder=0))
ax.text(6.25, 5.85, "Zona crítica", ha="right", va="top", fontsize=9, color=RED, style="italic")
ax.text(0.5, 0.6, "Zona aceptable", fontsize=9, color=GREEN, style="italic")
riesgos = [  # (id, texto, probabilidad, impacto, color, posición de la etiqueta)
    ("R1", "Sin aislamiento: un mercado\nve pedidos de otro", 4, 5, GREEN, "derecha"),
    ("R2", "Proveedor caído cancela el\npedido (código del Lab 07)", 4, 4, GREEN, "derecha"),
    ("R3", "Regla mal escrita, sin\ndespliegue ni revisión", 3, 4, ORG, "abajo"),
    ("R4", "VPS único: punto único de falla", 3, 5, RED, "arriba"),
    ("R5", "Tabla nueva sin política\nRLS expone otro mercado", 2, 5, GREEN, "izquierda"),
    ("R6", "Caída del proveedor > 15 min\ncancela pedidos", 3, 3, ORG, "derecha"),
    ("R7", "Cobro duplicado al\nreintentar un pago diferido", 2, 4, ORG, "izquierda"),
    ("R8", "Caché con precio o\nstock desactualizado", 4, 2, GREEN, "derecha"),
]
posiciones = {"derecha": (0.2, 0, "left", "center"), "izquierda": (-0.2, 0, "right", "center"),
              "arriba": (0, 0.3, "center", "bottom"), "abajo": (0, -0.3, "center", "top")}
for rid, txt, p, i, c, pos in riesgos:
    dx, dy, ha, va = posiciones[pos]
    ax.scatter(p, i, s=650, color=c, zorder=3, edgecolor="white", lw=1.5)
    ax.text(p, i, rid, ha="center", va="center", color="white", fontsize=9.5, weight="bold", zorder=4)
    ax.text(p + dx, i + dy, txt, ha=ha, va=va, fontsize=8, zorder=4)
ax.set_xlim(0.3, 6.4)
ax.set_ylim(0.5, 5.95)
ax.set_xticks(range(1, 6))
ax.set_yticks(range(1, 6))
ax.set_xlabel("Probabilidad (1 = muy baja … 5 = muy alta)")
ax.set_ylabel("Impacto en los escenarios de calidad")
ax.set_title("Riesgos de la evaluación ATAM-lite", fontsize=12, weight="bold", color=NAVY)
ax.scatter([], [], color=GREEN, s=80, label="Mitigado con evidencia")
ax.scatter([], [], color=ORG, s=80, label="Mitigado en parte")
ax.scatter([], [], color=RED, s=80, label="Aceptado (plazo de 1 mes)")
ax.legend(frameon=False, fontsize=8.5, loc="lower right")
ax.grid(alpha=0.25)
limpio(ax)
plt.tight_layout()
plt.savefig(IMG / "riesgos.png", dpi=200, bbox_inches="tight")
plt.close()
print("OK")

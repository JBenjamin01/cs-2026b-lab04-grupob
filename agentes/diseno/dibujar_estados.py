"""Dibuja diseno/estados.png a partir de las mismas transiciones de estados.puml (matplotlib, sin PlantUML)."""
import pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = pathlib.Path(__file__).parent
POS = {"[*]i": (0, 6.2), "Decidiendo": (0, 4.8), "ValidandoContrato": (0, 3.0), "Finalizado": (-4.6, 3.0),
       "EvaluandoPolitica": (0, 1.2), "LimiteAlcanzado": (-4.6, 1.2), "EsperandoAprobacion": (4.8, 1.2),
       "Ejecutando": (0, -0.6), "Observando": (4.8, -0.6), "[*]f": (-6.3, 2.1)}
ARCOS = {("Decidiendo", "ValidandoContrato"): 0.0, ("ValidandoContrato", "Decidiendo"): 0.5,
         ("EvaluandoPolitica", "Decidiendo"): -0.75, ("Observando", "Decidiendo"): 0.55,
         ("EsperandoAprobacion", "Decidiendo"): 0.15}


def transiciones():
    for l in (AQUI / "estados.puml").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\S+) --> (\S+)(?: : (.*))?$", l.strip())
        if m:
            o, d, t = m.groups()
            yield ("[*]i" if o == "[*]" else o), ("[*]f" if d == "[*]" else d), (t or "")


def borde(n, c, hacia):
    """Punto del borde de la caja de n (centro c) en la dirección de 'hacia'."""
    if n.startswith("[*]"):
        r = 0.3; dx, dy = hacia[0] - c[0], hacia[1] - c[1]; m = (dx * dx + dy * dy) ** 0.5 or 1
        return c[0] + r * dx / m, c[1] + r * dy / m
    dx, dy = hacia[0] - c[0], hacia[1] - c[1]
    k = min(1.55 / abs(dx) if dx else 9e9, 0.37 / abs(dy) if dy else 9e9)
    return c[0] + dx * k, c[1] + dy * k


fig, ax = plt.subplots(figsize=(11, 8.2)); ax.axis("off"); ax.set_xlim(-6.9, 7.6); ax.set_ylim(-1.5, 6.8)
for n, (x, y) in POS.items():
    if n.startswith("[*]"):
        ax.add_patch(plt.Circle((x, y), 0.18, color="black"))
        if n == "[*]f":
            ax.add_patch(plt.Circle((x, y), 0.28, fill=False, color="black"))
        continue
    fc = "#d5f5e3" if n == "Finalizado" else "#fadbd8" if n == "LimiteAlcanzado" else "#fef9e7" if n == "EsperandoAprobacion" else "#fde9e7"
    ax.add_patch(matplotlib.patches.FancyBboxPatch((x - 1.5, y - 0.32), 3.0, 0.64, boxstyle="round,pad=0.05", fc=fc, ec="#7f1d1d", zorder=5))
    ax.text(x, y, n, zorder=6, ha="center", va="center", fontsize=9, weight="bold")
for o, d, t in transiciones():
    (x1, y1), (x2, y2) = POS[o], POS[d]
    if o == d:
        ax.annotate("", xy=(x1 + 1.1, y1 + 0.33), xytext=(x1 + 1.6, y1 + 0.33),
                    arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=-1.6", color="#555"))
        ax.text(x1 + 0.2, y1 + 0.75, t, fontsize=6.5, color="#555"); continue
    rad = ARCOS.get((o, d), 0.0)
    (sx, sy), (ex, ey) = borde(o, (x1, y1), (x2, y2)), borde(d, (x2, y2), (x1, y1))
    ax.annotate("", xy=(ex, ey), xytext=(sx, sy), zorder=8,
                arrowprops=dict(arrowstyle="-|>", color="#1f4e79", lw=1, shrinkA=0, shrinkB=0,
                                connectionstyle=f"arc3,rad={rad}"))
    mx, my = (x1 + x2) / 2 + rad * (y2 - y1) * 0.5, (y1 + y2) / 2 - rad * (x2 - x1) * 0.5
    if (o, d) == ("Decidiendo", "ValidandoContrato"): mx -= 1.3
    mx, my = {("EvaluandoPolitica", "Decidiendo"): (-2.3, 2.15), ("Observando", "Decidiendo"): (5.7, 3.3),
              ("EsperandoAprobacion", "Decidiendo"): (2.6, 2.4)}.get((o, d), (mx, my))
    ax.text(mx, my, t.replace(" / ", "\n/ "), fontsize=6.5, ha="center", va="center", color="#1f4e79",
            bbox=dict(fc="white", ec="none", alpha=0.9, pad=0.5), zorder=7)
ax.set_title("Máquina de estados del agente (estados.puml)", fontsize=11, weight="bold")
fig.tight_layout(); fig.savefig(AQUI / "estados.png", dpi=150)

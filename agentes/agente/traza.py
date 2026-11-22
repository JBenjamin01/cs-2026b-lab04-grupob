"""Observabilidad: convierte las trazas JSONL en un diagrama de secuencia (Mermaid + PNG) y en métricas.

Uso: python agente/traza.py trazas/issue-01/unico      (escribe trayectoria.mmd y trayectoria.png en esa carpeta)
"""
import collections, json, pathlib, sys

ORDEN = ["planificador", "ejecutor", "revisor", "ejecutor_r2", "revisor_r2"]
ALIAS = {"planificador": "PL", "ejecutor": "EJ", "revisor": "RV"}
NOMBRES = {"U": "Humano", "PL": "Planificador", "EJ": "Ejecutor (actor)", "RV": "Revisor (crítico)",
           "P": "Política", "H": "Herramientas"}


def cargar(carpeta="trazas"):
    eventos = []
    for n in ORDEN:
        f = pathlib.Path(carpeta) / f"{n}.jsonl"
        if f.exists():
            ronda = int(n.split("_r")[1]) if "_r" in n else 1
            eventos += [dict(json.loads(l), ronda=ronda) for l in open(f, encoding="utf-8")]
    return eventos


def resumir(e) -> str:
    obs, acc, args = e["observacion"], e["accion"], e["args"]
    if acc == "leer_archivo": return f"contenido de {args['ruta'].split('/')[-1]}"
    if acc == "buscar": return "sin resultados" if "sin resultados" in obs else f"{len(obs.splitlines())} coincidencia(s)"
    if acc == "ver_cambios": return f"diff de {len(obs.splitlines())} líneas"
    if acc == "mapa_repo": return f"mapa de {len(obs.splitlines())} líneas"
    if acc in ("anotar", "leer_notas"): return "nota guardada" if acc == "anotar" else "notas leídas"
    if acc == "ejecutar_comando" and args.get("comando", "").startswith("radon"): return "complejidad A"
    if acc == "editar_archivo" and obs.startswith("OK"): return "OK, archivo modificado"
    return (obs.strip().splitlines() or [""])[-1].replace(";", ",").replace("#", "N.")[:40]


def mensajes(eventos) -> list[tuple[str, str, str, str]]:
    """Lista de (origen, destino, texto, estilo) con estilo: ->> llamada, -->> respuesta, -x bloqueo, note."""
    m, ronda_actual = [], 1
    for e in eventos:
        a = ALIAS[e["agente"]]
        if e["ronda"] != ronda_actual:
            ronda_actual = e["ronda"]
            m.append(("EJ", "RV", f"Ronda {ronda_actual} del bucle actor-crítico", "note"))
        if e["tipo"] == "objetivo":
            if a == "PL" or not any(x["agente"] == "planificador" for x in eventos):
                origen = "U"
            else:
                origen = "PL" if a == "EJ" and e["ronda"] == 1 else ("RV" if a == "EJ" else "EJ")
            texto = ("objetivo" if origen == "U" else "plan" if origen == "PL"
                     else "cambios solicitados" if origen == "RV" else "resumen + diff")
            m.append((origen, a, texto, "->>"))
        elif e["tipo"] == "accion":
            if e["bloqueada"]:
                motivo = "CONTRATO INVÁLIDO" if e["estado"] == "CONTRATO_INVALIDO" else "BLOQUEADO"
                m += [(a, "P", e["accion"], "-x"), ("P", a, motivo, "--x")]
            else:
                m += [(a, "H", e["accion"], "->>"), ("H", a, resumir(e), "-->>")]
        elif e["tipo"] == "final" and (a in ("RV", "EJ")) and not e["texto"].startswith("CAMBIOS"):
            if a == "RV" or not any(x["agente"] == "revisor" for x in eventos):
                m.append((a, "U", e["texto"].split(".")[0][:60], "-->>"))
    return m


def participantes(eventos) -> list[str]:
    presentes = {ALIAS[e["agente"]] for e in eventos}
    return ["U"] + [p for p in ("PL", "EJ", "RV") if p in presentes] + ["P", "H"]


def a_mermaid(eventos) -> str:
    l = ["sequenceDiagram", "    autonumber", "    actor U as Humano"]
    l += [f"    participant {p} as {NOMBRES[p]}" for p in participantes(eventos)[1:]]
    for o, d, t, s in mensajes(eventos):
        l.append(f"    Note over {o},{d}: {t}" if s == "note" else f"    {o}{s}{d}: {t}")
    return "\n".join(l)


def a_png(eventos, archivo, titulo="") -> None:
    """Renderiza el mismo diagrama de secuencia con matplotlib (sin depender de mermaid-cli)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ps, ms = participantes(eventos), mensajes(eventos)
    x = {p: i * 2.2 for i, p in enumerate(ps)}
    alto = 1.2 + 0.42 * len(ms)
    fig, ax = plt.subplots(figsize=(1.9 * len(ps) + 1, max(4, alto * 0.62)))
    ax.set_xlim(-1.2, x[ps[-1]] + 1.2); ax.set_ylim(-alto, 1.0); ax.axis("off")
    for p in ps:
        ax.add_patch(plt.Rectangle((x[p] - 0.95, 0.15), 1.9, 0.6, fc="#fde9e7" if p != "U" else "#e8f0fe", ec="#7f1d1d"))
        ax.text(x[p], 0.45, NOMBRES[p], ha="center", va="center", fontsize=8, weight="bold")
        ax.plot([x[p], x[p]], [0.15, -alto + 0.3], color="#999", lw=0.8, ls="--", zorder=0)
    for i, (o, d, t, s) in enumerate(ms, 1):
        y = -0.25 - 0.42 * (i - 1)
        if s == "note":
            ax.add_patch(plt.Rectangle((min(x[o], x[d]) - 0.6, y - 0.15), abs(x[d] - x[o]) + 1.2, 0.3, fc="#fff7d6", ec="#b58900"))
            ax.text((x[o] + x[d]) / 2, y, t, ha="center", va="center", fontsize=7, style="italic")
            continue
        color = "#c0392b" if "x" in s else ("#1f4e79" if s == "->>" else "#555")
        ax.annotate("", xy=(x[d], y), xytext=(x[o], y),
                    arrowprops=dict(arrowstyle="-|>" if "x" not in s else "-", color=color, lw=1.1,
                                    ls="--" if s.startswith("--") else "-"))
        if "x" in s:
            ax.plot(x[d], y, marker="x", color=color, ms=7, mew=2)
        ax.text((x[o] + x[d]) / 2, y + 0.06, f"{i}. {t}", ha="center", va="bottom", fontsize=6.5, color=color)
    if titulo:
        ax.set_title(titulo, fontsize=10, weight="bold")
    fig.tight_layout(); fig.savefig(archivo, dpi=150); plt.close(fig)


def metricas(eventos) -> dict:
    m = collections.defaultdict(collections.Counter)
    for e in eventos:
        if e["tipo"] == "accion":
            m[e["agente"]]["bloqueadas" if e["bloqueada"] else "permitidas"] += 1
            m[e["agente"]][e["accion"]] += 1
    return {k: dict(v) for k, v in m.items()}


if __name__ == "__main__":
    carpeta = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "trazas")
    ev = cargar(carpeta)
    (carpeta / "trayectoria.mmd").write_text(a_mermaid(ev), encoding="utf-8")
    a_png(ev, carpeta / "trayectoria.png", f"Trayectoria: {carpeta.as_posix().replace('trazas/', '')}")
    print(json.dumps(metricas(ev), ensure_ascii=False, indent=1))

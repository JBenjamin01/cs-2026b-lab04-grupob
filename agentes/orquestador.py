"""Sistema agéntico de San Camilo en Línea (Lab 10).

Dos formas de coordinar (Albada, 2025, cap. 8):
  unico          un solo agente ReAct (ejecutor) resuelve el issue.
  actor-critico  planificador (gestor) -> [ejecutor (actor) <-> revisor (crítico, solo lectura)] -> humano.
Cada agente recibe su propia política (mínimo privilegio). Todo ocurre en agentes/trabajo/, una copia de
trabajo_original/issue-NN/; el repositorio real solo cambia si el humano ejecuta --aplicar.

Uso:
  python orquestador.py 01                         # agente único, decisiones grabadas
  python orquestador.py 02 --modo actor-critico    # planificador + ejecutor + revisor (máx. 2 rondas)
  python orquestador.py 03 --interactivo           # sin clave de API: copiar y pegar con su asistente
  python orquestador.py 01 --aplicar               # el humano aprueba: copia a src/ los archivos cambiados
"""
import argparse, json, pathlib, shutil, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from agente.herramientas import Herramientas
from agente.modelos import ModeloGrabado, ModeloInteractivo
from agente.nucleo import Agente
from agente.politica import Politica

RAIZ = pathlib.Path(__file__).parent
REPO = RAIZ.parent
MAX_RONDAS = 2                                                      # presupuesto del bucle actor-crítico
SOLO_LECTURA = {"ver_cambios", "leer_archivo", "buscar", "ejecutar_pruebas"}


def preparar_sandbox(issue: str) -> Herramientas:
    base = RAIZ / "trabajo_original" / f"issue-{issue}"
    shutil.rmtree(RAIZ / "trabajo", ignore_errors=True)            # cada ejecución parte del estado original
    shutil.copytree(base, RAIZ / "trabajo")
    return Herramientas(RAIZ / "trabajo", original=base)


def modelo(issue, variante, nombre, interactivo):
    archivo = RAIZ / "trayectorias" / f"issue-{issue}" / variante / f"{nombre}.json"
    archivo.parent.mkdir(parents=True, exist_ok=True)
    return ModeloInteractivo(archivo) if interactivo else ModeloGrabado(archivo)


def politica_ejecutor() -> Politica:
    p = Politica(max_pasos=12)
    p.herramientas_permitidas = p.herramientas_permitidas | {"ver_cambios"}   # leer su propio diff es solo lectura
    return p


def ejecutar(issue: str, modo: str, interactivo: bool = False) -> list:
    h = preparar_sandbox(issue)
    variante = "unico" if modo == "unico" else "multi"
    trazas = RAIZ / "trazas" / f"issue-{issue}" / variante
    trazas.mkdir(parents=True, exist_ok=True)
    tarea = f"ISSUE-{issue}.md"

    if modo == "unico":
        ejecutor = Agente("ejecutor", modelo(issue, variante, "ejecutor", interactivo), h, politica_ejecutor(),
                          f"Resuelve {tarea}. Responde solo con el JSON del protocolo.\nHerramientas: {h.catalogo()}",
                          trazas / "ejecutor.jsonl")
        print(f"EJECUTOR: {ejecutor.ejecutar()}\n")
        return [ejecutor]

    planificador = Agente("planificador", modelo(issue, variante, "planificador", interactivo), h,
                          Politica(herramientas_permitidas=set(), max_pasos=2),
                          f"Planifica cómo resolver {tarea} en el repositorio de San Camilo en Línea.",
                          trazas / "planificador.jsonl")
    plan = planificador.ejecutar()
    print(f"PLANIFICADOR:\n{plan}\n")
    agentes, retro = [planificador], ""
    for ronda in range(1, MAX_RONDAS + 1):
        sufijo = "" if ronda == 1 else f"_r{ronda}"
        ejecutor = Agente("ejecutor", modelo(issue, variante, f"ejecutor{sufijo}", interactivo), h, politica_ejecutor(),
                          f"Resuelve {tarea} siguiendo este plan:\n{plan}\n{retro}Herramientas: {h.catalogo()}",
                          trazas / f"ejecutor{sufijo}.jsonl")
        resumen = ejecutor.ejecutar()
        revisor = Agente("revisor", modelo(issue, variante, f"revisor{sufijo}", interactivo), h,
                         Politica(herramientas_permitidas=SOLO_LECTURA, max_pasos=8),
                         f"Revisa el cambio del ejecutor. Responde APROBADO... o CAMBIOS SOLICITADOS...\nResumen:\n{resumen}",
                         trazas / f"revisor{sufijo}.jsonl")
        veredicto = revisor.ejecutar()
        agentes += [ejecutor, revisor]
        print(f"--- RONDA {ronda}\nEJECUTOR: {resumen}\nREVISOR: {veredicto}\n")
        if not veredicto.startswith("CAMBIOS SOLICITADOS"):         # el crítico acepta: se pasa al humano
            break
        retro = f"El revisor solicitó cambios:\n{veredicto}\n"      # el crítico rechaza: nueva ronda
    print(f"Rondas actor-crítico: {ronda} de {MAX_RONDAS}. Decisión final: HUMANO (aprobar o rechazar el PR).")
    return agentes


def resumir(issue: str, modo: str, agentes: list) -> dict:
    """Métricas de la ejecución (se guardan junto a las trazas para observacion.md)."""
    variante = "unico" if modo == "unico" else "multi"
    r = {"issue": issue, "modo": modo, "rondas": sum(a.nombre == "revisor" for a in agentes) or 1, "agentes": {}}
    for a in agentes:
        clave = a.nombre if a.nombre not in r["agentes"] else f"{a.nombre}_r2"
        acciones = [e for e in a.eventos if e["tipo"] == "accion"]
        r["agentes"][clave] = {
            "pasos": len(acciones) + sum(e["tipo"] == "final" for e in a.eventos),
            "contrato_invalido": sum(e["estado"] == "CONTRATO_INVALIDO" for e in acciones),
            "bloqueadas": sum(e["bloqueada"] and e["estado"] != "CONTRATO_INVALIDO" for e in acciones),
            "herramientas": sorted({e["accion"] for e in acciones if not e["bloqueada"]}),
            "contexto_caracteres": len(json.dumps(a.historial, ensure_ascii=False)),
        }
        print(f"[{clave}] contexto final: {r['agentes'][clave]['contexto_caracteres']} caracteres "
              f"(~{r['agentes'][clave]['contexto_caracteres'] // 4} tokens)")
    (RAIZ / "trazas" / f"issue-{issue}" / variante / "resumen.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    return r


def aplicar(issue: str) -> None:
    """El humano aprobó el cambio: copia al repositorio real los archivos de src/ que cambiaron."""
    base, trabajo = RAIZ / "trabajo_original" / f"issue-{issue}", RAIZ / "trabajo"
    for p in sorted((trabajo / "src").rglob("*.py")):
        rel = p.relative_to(trabajo)
        if (base / rel).read_text(encoding="utf-8") != p.read_text(encoding="utf-8"):
            shutil.copyfile(p, REPO / rel)
            print(f"aplicado: {rel.as_posix()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("issue", choices=["01", "02", "03"])
    ap.add_argument("--modo", choices=["unico", "actor-critico"], default="unico")
    ap.add_argument("--interactivo", action="store_true", help="ModeloInteractivo: copiar y pegar con su asistente")
    ap.add_argument("--aplicar", action="store_true", help="copiar a src/ los archivos que el agente cambió")
    a = ap.parse_args()
    resumir(a.issue, a.modo, ejecutar(a.issue, a.modo, a.interactivo))
    if a.aplicar:
        aplicar(a.issue)

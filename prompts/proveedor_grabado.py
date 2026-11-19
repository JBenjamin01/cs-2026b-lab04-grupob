"""Proveedor de promptfoo que devuelve respuestas GRABADAS (fixtures), sin clave de API.

Las respuestas se obtuvieron con un asistente de IA y se guardaron SIN EDITAR en
<carpeta de grabaciones>/<version>/<id>.txt. Cada promptfooconfig.yaml indica su carpeta con
config.grabaciones (relativa a esta carpeta prompts/). Así la evaluación es reproducible en CI.
"""
import pathlib
import re

BASE = pathlib.Path(__file__).parent


def call_api(prompt, options, context):
    carpeta = BASE / options.get("config", {}).get("grabaciones", "grabaciones")
    etiqueta = context["prompt"]["label"]
    version = re.search(r"(v[\w.]+)\.txt", etiqueta).group(1)
    caso = context["vars"]["id"]
    archivo = carpeta / version / f"{caso}.txt"
    if not archivo.exists():
        return {"error": f"Sin grabación para {version}/{caso}"}
    return {"output": archivo.read_text(encoding="utf-8").strip()}

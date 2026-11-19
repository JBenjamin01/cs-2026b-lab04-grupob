"""Generador de normalización de nombres (Lab 09, E6): el prompt versionado detrás de ProveedorLLM.

La plantilla vive en prompts/normalizacion/<version>.txt (versionada y evaluada con promptfoo).
La salida del LLM es un dato no confiable: antes de usarla se valida en dos niveles
(capa 3 de la defensa en capas):
  1. contrato: JSON que cumple prompts/normalizacion/esquema.json;
  2. dominio: una asignación por entrada, en el mismo orden, y cada producto del catálogo o
     "desconocido" (las mismas reglas que las aserciones B2 y B3 de la evaluación).
Si algo no cumple, se lanza SalidaInvalida y el comerciante elige el producto a mano (capa 4:
la salida nunca publica nada por sí sola). Además, el catálogo que entra al prompt se filtra
(capa 1 sobre la fuente de datos): un nombre de producto con órdenes o signos no se envía.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from jsonschema import ValidationError, validate

from catalogo.ia import ProveedorLLM

PROMPTS = Path(__file__).resolve().parents[2] / "prompts" / "normalizacion"
DESCONOCIDO = "desconocido"
# Capa 1 sobre la fuente de datos (red teaming R7): los nombres del catálogo los crean comerciantes,
# así que solo entran al prompt nombres cortos hechos de letras y espacios (sin órdenes ni signos).
NOMBRE_VALIDO = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]{2,40}$")


class SalidaInvalida(Exception):
    """La respuesta del LLM no cumple el contrato: se descarta y se registra."""


@dataclass(frozen=True)
class Asignacion:
    entrada: str
    producto: str | None          # None = desconocido: el comerciante elige a mano
    confianza: str


class GeneradorNormalizacion:
    def __init__(self, proveedor: ProveedorLLM, catalogo: list[str], version: str = "v3.1",
                 carpeta: Path = PROMPTS):
        self._proveedor = proveedor          # Strategy (Lab 07): Claude, local o grabado
        self._catalogo = [n for n in catalogo if NOMBRE_VALIDO.match(n)]
        self.descartados = [n for n in catalogo if not NOMBRE_VALIDO.match(n)]
        self._plantilla = (carpeta / f"{version}.txt").read_text(encoding="utf-8")
        self._esquema = json.loads((carpeta / "esquema.json").read_text(encoding="utf-8"))
        self.version = version

    def prompt_para(self, entradas: list[str]) -> str:
        return (self._plantilla
                .replace("{{catalogo}}", "\n".join(self._catalogo) + "\n")
                .replace("{{entradas}}", json.dumps(entradas, ensure_ascii=False)))

    def normalizar(self, entradas: list[str]) -> list[Asignacion]:
        texto = self._proveedor.completar(self.prompt_para(entradas))
        try:
            datos = json.loads(texto)
            validate(datos, self._esquema)                       # nivel 1: contrato
        except (json.JSONDecodeError, ValidationError) as e:
            raise SalidaInvalida(f"{self.version}: {e.__class__.__name__}: {str(e).splitlines()[0]}") from e
        resultados = datos["resultados"]
        if [r["entrada"] for r in resultados] != list(entradas):   # nivel 2: dominio
            raise SalidaInvalida(f"{self.version}: las entradas no coinciden con las enviadas")
        validos = set(self._catalogo) | {DESCONOCIDO}
        fuera = [r["producto"] for r in resultados if r["producto"] not in validos]
        if fuera:
            raise SalidaInvalida(f"{self.version}: productos fuera del catálogo: {fuera}")
        return [Asignacion(r["entrada"], None if r["producto"] == DESCONOCIDO else r["producto"], r["confianza"])
                for r in resultados]

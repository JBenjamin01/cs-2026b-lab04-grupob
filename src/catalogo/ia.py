"""IA aislada (Lab 07, E5): normalizar nombres de productos del catálogo.

Los comerciantes escriben «papa amarila», «keso paria»…; la IA sugiere el nombre canónico y el
comerciante solo confirma (QA-01: publicar en ≤ 3 toques). Un LLM no es determinista, así que:
- STRATEGY + ADAPTER: ProveedorLLM es la interfaz; cada proveedor es un adaptador intercambiable.
- DECORATOR: ConCache evita pagar dos veces por el mismo prompt.
- CHAIN OF RESPONSIBILITY: la salida pasa por una cadena de guardrails antes de mostrarse.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class GuardrailError(ValueError):
    """La respuesta de la IA no pasó un guardrail: no se muestra al comerciante."""


# ---------- STRATEGY + ADAPTER ----------
class ProveedorLLM(ABC):
    @abstractmethod
    def completar(self, prompt: str) -> str: ...


class ClaudeAdapter(ProveedorLLM):
    """Adapta un SDK de chat (messages_create -> bloques de contenido) a completar()."""

    def __init__(self, cliente, modelo: str = "claude", max_tokens: int = 50):
        self._cliente = cliente
        self._modelo = modelo
        self._max_tokens = max_tokens

    def completar(self, prompt: str) -> str:
        r = self._cliente.messages_create(model=self._modelo, max_tokens=self._max_tokens,
                                          messages=[{"role": "user", "content": prompt}])
        return r["content"][0]["text"]


class LocalAdapter(ProveedorLLM):
    """Adapta un modelo local (generate -> texto plano) a completar()."""

    def __init__(self, modelo):
        self._modelo = modelo

    def completar(self, prompt: str) -> str:
        return self._modelo.generate(prompt)


# ---------- DECORATOR ----------
class ConCache(ProveedorLLM):
    def __init__(self, interno: ProveedorLLM):
        self._interno = interno
        self._cache: dict[str, str] = {}

    def completar(self, prompt: str) -> str:
        if prompt not in self._cache:
            self._cache[prompt] = self._interno.completar(prompt)
        return self._cache[prompt]


# ---------- CHAIN OF RESPONSIBILITY: guardrails de salida ----------
class Guardrail(ABC):
    def __init__(self, siguiente: Guardrail | None = None):
        self._siguiente = siguiente

    def validar(self, texto: str) -> str:
        texto = self._aplicar(texto)
        return self._siguiente.validar(texto) if self._siguiente else texto

    @abstractmethod
    def _aplicar(self, texto: str) -> str: ...


class LimpiarFormato(Guardrail):
    """Quita espacios, comillas y el punto final que suelen agregar los modelos."""

    def _aplicar(self, texto):
        return texto.strip().strip('"').strip("'").rstrip(".").strip()


class SinPreciosNiCantidades(Guardrail):
    """Un nombre de producto no lleva precios ni cifras: si aparecen, la IA los inventó."""

    def _aplicar(self, texto):
        if "S/" in texto or any(ch.isdigit() for ch in texto):
            raise GuardrailError("La IA incluyó un precio o una cantidad")
        return texto


class LongitudMaxima(Guardrail):
    def __init__(self, maximo: int, siguiente: Guardrail | None = None):
        super().__init__(siguiente)
        self._maximo = maximo

    def _aplicar(self, texto):
        if len(texto) > self._maximo:
            raise GuardrailError(f"Nombre de más de {self._maximo} caracteres")
        return texto


class SoloDelCatalogo(Guardrail):
    """La IA no puede inventar productos: devuelve la forma canónica o rechaza."""

    def __init__(self, catalogo: list[str], siguiente: Guardrail | None = None):
        super().__init__(siguiente)
        self._canonicos = {nombre.lower(): nombre for nombre in catalogo}

    def _aplicar(self, texto):
        if texto.lower() not in self._canonicos:
            raise GuardrailError(f"'{texto}' no está en el catálogo")
        return self._canonicos[texto.lower()]


def cadena_guardrails(catalogo: list[str]) -> Guardrail:
    return LimpiarFormato(SinPreciosNiCantidades(LongitudMaxima(40, SoloDelCatalogo(catalogo))))


# ---------- Cliente de los patrones ----------
class NormalizadorNombres:
    def __init__(self, proveedores: dict[str, ProveedorLLM], guardrails: Guardrail, catalogo: list[str]):
        self._proveedores = proveedores
        self._guardrails = guardrails
        self._canonicos = {nombre.lower(): nombre for nombre in catalogo}
        self._catalogo = catalogo

    def sugerir_nombre(self, nombre: str, proveedor: str = "CLAUDE") -> str | None:
        """Devuelve el nombre canónico sugerido, o None si la IA no dio una respuesta válida
        (en ese caso el comerciante escribe o elige el nombre a mano)."""
        exacto = self._canonicos.get(nombre.strip().lower())
        if exacto:  # no se paga una llamada a la IA si no hace falta
            return exacto
        if proveedor not in self._proveedores:
            raise ValueError(f"Proveedor de IA no soportado: {proveedor}")
        prompt = (f"Normaliza el nombre de producto '{nombre}' a uno de esta lista: "
                  f"{', '.join(self._catalogo)}. Responde solo con el nombre.")
        try:
            return self._guardrails.validar(self._proveedores[proveedor].completar(prompt))
        except GuardrailError:
            return None

"""Módulo Catálogo. Interfaz pública: los demás módulos importan desde aquí, no desde modelos.py."""
from catalogo.ia import (ClaudeAdapter, ConCache, LocalAdapter, NormalizadorNombres, ProveedorLLM,
                         cadena_guardrails)
from catalogo.modelos import Comerciante, Producto

__all__ = ["ClaudeAdapter", "Comerciante", "ConCache", "LocalAdapter", "NormalizadorNombres", "Producto",
           "ProveedorLLM", "cadena_guardrails"]

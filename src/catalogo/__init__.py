"""Módulo Catálogo. Interfaz pública: los demás módulos importan desde aquí, no desde modelos.py."""
from catalogo.modelos import Comerciante, Producto

__all__ = ["Comerciante", "Producto"]

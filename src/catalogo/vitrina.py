"""Vitrina de la PWA: qué productos ve el cliente (Lab 10).

Un producto se muestra si el comerciante lo tiene publicado (`disponible`). La búsqueda por nombre
usa el mismo criterio.
"""
from __future__ import annotations


def productos_visibles(productos: list) -> list:
    """Productos que la PWA muestra a los clientes, en el mismo orden."""
    return [p for p in productos if p.disponible and p.stock_disponible > 0]   # issue 02: sin agotados


def buscar_productos(productos: list, texto: str) -> list:
    """Búsqueda por nombre (sin distinguir mayúsculas) entre los productos de la vitrina."""
    t = texto.strip().lower()
    return [p for p in productos_visibles(productos) if t in p.nombre.lower()]   # mismo criterio que la vitrina

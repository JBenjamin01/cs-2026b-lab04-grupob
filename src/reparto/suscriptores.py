"""Suscriptor del módulo Reparto (OBSERVER, Lab 07): crea la orden de reparto de un delivery pagado.

Recibe datos neutrales (dict), así que no necesita importar nada de pedidos para esto.
"""
from __future__ import annotations

from comun.eventos import Suscriptor


class AsignadorReparto(Suscriptor):
    def __init__(self, cola_reparto: list[str]):
        self._cola = cola_reparto

    def actualizar(self, evento: str, datos: dict) -> None:
        if datos["tipo_entrega"] == "DELIVERY":
            self._cola.append(f"reparto:{datos['codigo']}:{datos['distrito']}")

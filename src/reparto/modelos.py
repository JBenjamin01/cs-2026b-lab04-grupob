"""Módulo Reparto — Repartidor conoce los pedidos que reparte (navegación reparto -> pedidos)."""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from pedidos import Pedido


@dataclass
class Repartidor:
    nombre: str
    celular: str
    disponible: bool = True
    pedidos: list[Pedido] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def tomar_pedido(self, pedido: Pedido) -> None:
        self.pedidos.append(pedido)
        self.disponible = False

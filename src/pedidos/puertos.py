"""Puerto de persistencia del módulo Pedidos."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from pedidos.pedido import Pedido


class RepositorioPedidos(ABC):
    @abstractmethod
    def buscar_por_id(self, id: UUID) -> Pedido: ...

    @abstractmethod
    def guardar(self, pedido: Pedido) -> None: ...


class RepositorioEnMemoria(RepositorioPedidos):
    """Adaptador en memoria para desarrollo y pruebas (en producción: ORM de Django)."""

    def __init__(self) -> None:
        self._pedidos: dict[UUID, Pedido] = {}

    def buscar_por_id(self, id: UUID) -> Pedido:
        return self._pedidos[id]

    def guardar(self, pedido: Pedido) -> None:
        self._pedidos[pedido.id] = pedido

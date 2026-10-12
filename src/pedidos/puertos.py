"""Puerto de persistencia del módulo Pedidos."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from pedidos.dominio import Pedido


class RepositorioPedidos(ABC):
    @abstractmethod
    def buscar_por_id(self, id: UUID) -> Pedido: ...

    @abstractmethod
    def buscar_por_subpedido(self, subpedido_id: UUID) -> Pedido: ...

    @abstractmethod
    def guardar(self, pedido: Pedido) -> None: ...

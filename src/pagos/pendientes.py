"""Outbox de pagos pendientes (Lab 08, iteración 3, ADR-008).

Si el proveedor no responde, el cobro se guarda aquí en la MISMA transacción que el pedido
(tabla pagos.pago_pendiente en PostgreSQL, no en Redis: si Redis se reinicia, no se pierde).
El worker (Celery beat, cada minuto) lo reintenta cuando el circuito se cierra.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class PagoPendiente:
    pedido_id: UUID
    medio: str
    monto: Decimal
    celular: str
    codigo_aprobacion: str
    desde: datetime


class ColaPagosPendientes(ABC):
    @abstractmethod
    def agregar(self, pendiente: PagoPendiente) -> None: ...

    @abstractmethod
    def pendientes(self) -> list[PagoPendiente]: ...

    @abstractmethod
    def quitar(self, pedido_id: UUID) -> None: ...


class ColaPagosPendientesEnMemoria(ColaPagosPendientes):
    """Adaptador para pruebas; en producción, el ORM de Django sobre pagos.pago_pendiente."""

    def __init__(self) -> None:
        self._por_pedido: dict[UUID, PagoPendiente] = {}

    def agregar(self, pendiente: PagoPendiente) -> None:
        self._por_pedido[pendiente.pedido_id] = pendiente      # idempotente por pedido

    def pendientes(self) -> list[PagoPendiente]:
        return sorted(self._por_pedido.values(), key=lambda p: p.desde)   # los más antiguos primero

    def quitar(self, pedido_id: UUID) -> None:
        self._por_pedido.pop(pedido_id, None)

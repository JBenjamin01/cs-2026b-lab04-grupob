"""Módulo Pagos — entidad Pago, su estado y el puerto PasarelaPago (ADR-001, ADR-004, ADR-005).

Lab 07: reembolsar() recibe la referencia del proveedor (no el id interno del pago), porque es
lo que los proveedores necesitan para devolver un cobro (CA-3 del Lab 05).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class EstadoPago(Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    RECHAZADO = "RECHAZADO"
    EXPIRADO = "EXPIRADO"


@dataclass
class Pago:
    pedido_id: UUID
    monto: Decimal
    referencia_proveedor: str | None
    estado: EstadoPago = EstadoPago.PENDIENTE
    fecha_hora: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)

    def esta_confirmado(self) -> bool:
        return self.estado is EstadoPago.CONFIRMADO


class PasarelaPago(ABC):
    """STRATEGY (puerto): todas las formas de cobrar se usan igual."""

    @abstractmethod
    def iniciar_cobro(
        self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str
    ) -> Pago: ...

    @abstractmethod
    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None: ...

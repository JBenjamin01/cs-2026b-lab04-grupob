"""Módulo Pagos — entidad Pago, su estado y el puerto PasarelaPago (ADR-001, ADR-004)."""
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
    referencia_proveedor: str
    estado: EstadoPago = EstadoPago.PENDIENTE
    fecha_hora: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)

    def esta_confirmado(self) -> bool:
        return self.estado is EstadoPago.CONFIRMADO


class PasarelaPago(ABC):
    """Puerto hacia el proveedor de pagos que cobra con Yape (R-05)."""

    @abstractmethod
    def iniciar_cobro(
        self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str
    ) -> Pago: ...

    @abstractmethod
    def reembolsar(self, pago_id: UUID, monto: Decimal) -> None: ...


class YapeAdapter(PasarelaPago):
    """Adaptador del proveedor de pagos. El código de aprobación no se almacena."""

    def iniciar_cobro(
        self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str
    ) -> Pago:
        raise NotImplementedError("Integrar con la API del proveedor de pagos")

    def reembolsar(self, pago_id: UUID, monto: Decimal) -> None:
        raise NotImplementedError("Integrar con la API del proveedor de pagos")

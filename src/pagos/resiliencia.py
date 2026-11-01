"""Táctica de disponibilidad (Lab 08, iteración 3, ADR-008): CIRCUIT BREAKER como DECORATOR.

Envuelve a cualquier PasarelaPago (ya envuelta en ConReintentos, Lab 07) sin modificarla:
- CERRADO: deja pasar los cobros y cuenta los que fallan (reintentos agotados).
- ABIERTO: tras `umbral` fallas seguidas, falla rápido con CircuitoAbierto, sin llamar al
  proveedor caído; el pedido queda pendiente en la outbox (pagos/pendientes.py).
- SEMIABIERTO: pasado `espera_s`, deja pasar UN cobro de prueba; si funciona se cierra.
"""
from __future__ import annotations

import time
from decimal import Decimal
from typing import Callable
from uuid import UUID

from pagos.modelos import EstadoPago, Pago, PasarelaPago


class CircuitoAbierto(Exception):
    """Falla rápida: el proveedor está caído y el cobro se difiere."""


class ConCircuitBreaker(PasarelaPago):
    def __init__(self, interna: PasarelaPago, umbral: int = 3, espera_s: float = 60,
                 reloj: Callable[[], float] = time.monotonic):
        self._interna = interna
        self._umbral = umbral
        self._espera = espera_s
        self._reloj = reloj
        self._fallas = 0
        self._abierto_desde: float | None = None

    @property
    def estado(self) -> str:
        if self._abierto_desde is None:
            return "CERRADO"
        return "SEMIABIERTO" if self._reloj() - self._abierto_desde >= self._espera else "ABIERTO"

    def iniciar_cobro(self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str) -> Pago:
        self._verificar_paso()
        try:
            pago = self._interna.iniciar_cobro(pedido_id, monto, celular, codigo_aprobacion)
        except TimeoutError:
            self._registrar_falla()
            raise
        if pago.estado is EstadoPago.EXPIRADO:     # ConReintentos agotó sus intentos
            self._registrar_falla()
        else:                                      # el proveedor respondió (aprobado o rechazado)
            self._fallas, self._abierto_desde = 0, None
        return pago

    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None:
        self._verificar_paso()
        try:
            self._interna.reembolsar(referencia_proveedor, monto)
        except TimeoutError:
            self._registrar_falla()
            raise
        self._fallas, self._abierto_desde = 0, None

    def _verificar_paso(self) -> None:
        if self.estado == "ABIERTO":
            raise CircuitoAbierto("Proveedor de pagos no disponible: el cobro se difiere")

    def _registrar_falla(self) -> None:
        self._fallas += 1
        if self._fallas >= self._umbral or self.estado == "SEMIABIERTO":
            self._abierto_desde = self._reloj()

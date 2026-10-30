"""Pagos con patrones (Lab 07, E2): ADAPTER + STRATEGY + FACTORY (registro).

- YapeAdapter y PlinAdapter traducen cada SDK a la interfaz PasarelaPago (Adapter).
- Cada adaptador es una estrategia intercambiable de cobro (Strategy).
- FabricaPasarelas crea la estrategia por nombre; un medio nuevo solo se registra (Factory).
Pendiente (E4): el bucle de reintentos todavía está duplicado en los dos adaptadores.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Callable
from uuid import UUID

from pagos.modelos import EstadoPago, Pago, PasarelaPago


class YapeAdapter(PasarelaPago):
    """El SDK cobra en soles y responde con un diccionario."""

    def __init__(self, sdk, intentos: int = 3):
        self._sdk = sdk
        self._intentos = intentos

    def iniciar_cobro(self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str) -> Pago:
        for _ in range(self._intentos):
            try:
                r = self._sdk.cobrar_yape(celular, monto, codigo_aprobacion)
                estado = EstadoPago.CONFIRMADO if r["estado"] == "APROBADO" else EstadoPago.RECHAZADO
                return Pago(pedido_id, monto, r["id_transaccion"], estado)
            except TimeoutError:
                continue
        return Pago(pedido_id, monto, None, EstadoPago.EXPIRADO)

    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None:
        self._sdk.devolver(referencia_proveedor, monto)


class PlinAdapter(PasarelaPago):
    """El cliente cobra en céntimos y responde con (código HTTP, id de transacción)."""

    def __init__(self, cliente, intentos: int = 3):
        self._cliente = cliente
        self._intentos = intentos

    def iniciar_cobro(self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str) -> Pago:
        for _ in range(self._intentos):
            try:
                codigo, tx = self._cliente.charge(_a_centimos(monto), celular, codigo_aprobacion)
                estado = EstadoPago.CONFIRMADO if codigo == 200 else EstadoPago.RECHAZADO
                return Pago(pedido_id, monto, tx, estado)
            except TimeoutError:
                continue
        return Pago(pedido_id, monto, None, EstadoPago.EXPIRADO)

    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None:
        self._cliente.refund(referencia_proveedor, _a_centimos(monto))


def _a_centimos(monto: Decimal) -> int:
    return int(monto * 100)


class FabricaPasarelas:
    """Se crea e inyecta una instancia (no es Singleton): las pruebas registran SDK simulados."""

    def __init__(self):
        self._creadores: dict[str, Callable[[], PasarelaPago]] = {}

    def registrar(self, medio: str, creador: Callable[[], PasarelaPago]) -> None:
        self._creadores[medio] = creador

    def crear(self, medio: str) -> PasarelaPago:
        if medio not in self._creadores:
            raise ValueError(f"Medio de pago no soportado: {medio}")
        return self._creadores[medio]()

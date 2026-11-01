"""ADAPTER (Lab 07): traduce cada SDK de pagos a la interfaz PasarelaPago.

Lab 08 (FF-02, ADR-005): se separaron de pasarelas.py. Solo arranque.py importa este módulo;
pedidos, reparto, catalogo, notificaciones y mercados tienen prohibido hacerlo (.importlinter).
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pagos.modelos import EstadoPago, Pago, PasarelaPago


class YapeAdapter(PasarelaPago):
    """El SDK cobra en soles y responde con un diccionario."""

    def __init__(self, sdk):
        self._sdk = sdk

    def iniciar_cobro(self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str) -> Pago:
        r = self._sdk.cobrar_yape(celular, monto, codigo_aprobacion)
        estado = EstadoPago.CONFIRMADO if r["estado"] == "APROBADO" else EstadoPago.RECHAZADO
        return Pago(pedido_id, monto, r["id_transaccion"], estado)

    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None:
        self._sdk.devolver(referencia_proveedor, monto)


class PlinAdapter(PasarelaPago):
    """El cliente cobra en céntimos y responde con (código HTTP, id de transacción)."""

    def __init__(self, cliente):
        self._cliente = cliente

    def iniciar_cobro(self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str) -> Pago:
        codigo, tx = self._cliente.charge(_a_centimos(monto), celular, codigo_aprobacion)
        estado = EstadoPago.CONFIRMADO if codigo == 200 else EstadoPago.RECHAZADO
        return Pago(pedido_id, monto, tx, estado)

    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None:
        self._cliente.refund(referencia_proveedor, _a_centimos(monto))


def _a_centimos(monto: Decimal) -> int:
    return int(monto * 100)

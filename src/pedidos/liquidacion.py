"""Liquidación de un pedido a varios puestos (Lab 10).

Un pedido de San Camilo en Línea puede reunir productos de varios puestos y se paga una sola vez
(Yape o Plin). La plataforma cobra una comisión sobre lo vendido y abona a cada puesto su parte.
Todos los montos son Decimal con 2 decimales (céntimos de sol).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENTIMO = Decimal("0.01")


def comision_del_pedido(subtotales: dict[str, Decimal], tasa: Decimal) -> Decimal:
    """Comisión de la plataforma por un pedido: `tasa` aplicada a lo vendido por cada puesto."""
    comision = Decimal("0")
    for subtotal in subtotales.values():        # issue 01: cada puesto paga la comisión de SU parte
        comision += (subtotal * tasa).quantize(CENTIMO, rounding=ROUND_HALF_UP)
    return comision


def abonos_a_puestos(subtotales: dict[str, Decimal], tasa: Decimal) -> dict[str, Decimal]:
    """Monto que se abona a cada puesto: su subtotal menos la comisión de su parte."""
    # issue 03: Decimal y el MISMO redondeo que comision_del_pedido, así abonos + comisión = total
    return {puesto: s - (s * tasa).quantize(CENTIMO, rounding=ROUND_HALF_UP)
            for puesto, s in subtotales.items()}

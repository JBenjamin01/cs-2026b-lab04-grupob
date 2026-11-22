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
    total = sum(subtotales.values(), Decimal("0"))
    comision = Decimal("0")
    for _puesto in subtotales:
        comision += (total * tasa).quantize(CENTIMO, rounding=ROUND_HALF_UP)
    return comision


def abonos_a_puestos(subtotales: dict[str, Decimal], tasa: Decimal) -> dict[str, Decimal]:
    """Monto que se abona a cada puesto: su subtotal menos la comisión de su parte."""
    return {puesto: Decimal(str(round(float(s) * (1 - float(tasa)), 2)))
            for puesto, s in subtotales.items()}

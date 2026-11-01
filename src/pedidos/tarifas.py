"""STRATEGY (Lab 07): tarifa de delivery intercambiable, elegida según el tipo de entrega."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

ZONAS_AREQUIPA = {
    "Cercado": Decimal("5"), "Selva Alegre": Decimal("5"),
    "Yanahuara": Decimal("8"), "Cayma": Decimal("8"), "Miraflores": Decimal("8"),
}


class TarifaEnvio(ABC):
    @abstractmethod
    def calcular(self, subtotal: Decimal, distrito: str | None) -> Decimal: ...


class TarifaRecojo(TarifaEnvio):
    """Recojo en el centro de acopio del mercado: sin costo."""

    def calcular(self, subtotal, distrito):
        return Decimal("0")


class TarifaPorZona(TarifaEnvio):
    """Delivery: precio por zona de Arequipa, gratis desde un monto mínimo."""

    def __init__(self, zonas: dict[str, Decimal], por_defecto: Decimal = Decimal("12"),
                 gratis_desde: Decimal = Decimal("150")):
        self._zonas = zonas
        self._por_defecto = por_defecto
        self._gratis_desde = gratis_desde

    def calcular(self, subtotal, distrito):
        if subtotal >= self._gratis_desde:
            return Decimal("0")
        return self._zonas.get(distrito, self._por_defecto)


def tarifas_por_defecto() -> dict[str, TarifaEnvio]:
    """Tarifas que se usan cuando el servicio se crea sin reglas de mercado (pruebas del Lab 07).
    Desde el Lab 08, las zonas de cada mercado vienen de sus datos (ADR-006)."""
    return {"RECOJO_MERCADO": TarifaRecojo(), "DELIVERY": TarifaPorZona(ZONAS_AREQUIPA)}

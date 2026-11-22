"""Reglas de negocio de un mercado, cargadas desde datos (táctica «diferir el enlace», ADR-006).

El código define QUÉ reglas existen (pedido mínimo, medios de pago, zonas de delivery, comisión,
horario); cada mercado define SUS VALORES. Ningún método pregunta «¿qué mercado es?»: la fitness
function FF-03 lo verifica en la integración continua.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time
from decimal import ROUND_HALF_UP, Decimal
from types import MappingProxyType
from typing import Mapping

from comun.excepciones import ReglaNegocioError

COMISION_MAXIMA = Decimal("0.15")   # tope acordado con los mercados: 15 % del subtotal
_CODIGO = re.compile(r"^[A-Z][A-Z0-9_]{2,29}$")


class ConfiguracionInvalida(ValueError):
    """Los datos de un mercado no son válidos; se rechazan ANTES de guardarlos (riesgo R3 de atam-lite.md)."""


@dataclass(frozen=True)
class ReglasMercado:
    codigo: str
    nombre: str
    pedido_minimo: Decimal
    comision: Decimal                      # fracción del subtotal (0.05 = 5 %)
    medios_pago: frozenset[str]
    zonas_delivery: Mapping[str, Decimal]  # distrito -> costo de envío
    tarifa_por_defecto: Decimal            # distrito no listado
    delivery_gratis_desde: Decimal
    abre: time
    cierra: time

    # ---------- reglas que usa el módulo Pedidos ----------
    def validar_pedido(self, subtotal: Decimal, medio: str) -> None:
        if subtotal < self.pedido_minimo:
            raise ReglaNegocioError(f"{self.nombre}: el pedido mínimo es S/ {self.pedido_minimo}")
        if medio not in self.medios_pago:
            raise ReglaNegocioError(f"{self.nombre} no acepta pagos con {medio}")

    def comision_de(self, subtotal: Decimal) -> Decimal:
        return (subtotal * self.comision).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def esta_abierto(self, momento: datetime) -> bool:
        """La PWA lo usa para mostrar el mercado como abierto o cerrado."""
        return self.abre <= momento.time() < self.cierra

    # ---------- construcción desde datos, con validación ----------
    @classmethod
    def desde_dict(cls, d: dict) -> "ReglasMercado":
        try:
            reglas = cls(
                codigo=d["codigo"],
                nombre=d["nombre"],
                pedido_minimo=Decimal(str(d["pedido_minimo"])),
                comision=Decimal(str(d["comision"])),
                medios_pago=frozenset(d["medios_pago"]),
                zonas_delivery=MappingProxyType({k: Decimal(str(v)) for k, v in d["zonas_delivery"].items()}),
                tarifa_por_defecto=Decimal(str(d["tarifa_por_defecto"])),
                delivery_gratis_desde=Decimal(str(d["delivery_gratis_desde"])),
                abre=time.fromisoformat(d["abre"]),
                cierra=time.fromisoformat(d["cierra"]),
            )
        except (KeyError, ArithmeticError, ValueError, TypeError) as e:
            raise ConfiguracionInvalida(f"Datos de mercado incompletos o mal escritos: {e}") from e
        reglas._validar()
        return reglas

    def _validar(self) -> None:
        errores = []
        if not _CODIGO.match(self.codigo):
            errores.append("código en MAYÚSCULAS, sin espacios (p. ej. RIO_SECO)")
        if not Decimal("0") <= self.comision <= COMISION_MAXIMA:
            errores.append(f"comisión entre 0 y {COMISION_MAXIMA}")
        montos = [self.pedido_minimo, self.tarifa_por_defecto, self.delivery_gratis_desde,
                  *self.zonas_delivery.values()]
        if any(m < 0 for m in montos):
            errores.append("montos no negativos")
        if not self.medios_pago:
            errores.append("al menos un medio de pago")
        if self.abre >= self.cierra:
            errores.append("hora de apertura anterior a la de cierre")
        if errores:
            raise ConfiguracionInvalida(f"Mercado {self.codigo}: " + "; ".join(errores))

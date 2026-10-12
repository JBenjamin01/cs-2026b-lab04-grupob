"""Módulo Catálogo — generado con IA a partir de clases.puml y revisado por el equipo."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from comun.excepciones import ReglaNegocioError


@dataclass
class Comerciante:
    nombre: str
    numero_puesto: str
    celular: str
    id: UUID = field(default_factory=uuid4)


@dataclass
class Producto:
    nombre: str
    precio: Decimal
    unidad_medida: str
    stock_disponible: Decimal
    comerciante: Comerciante
    disponible: bool = True
    id: UUID = field(default_factory=uuid4)

    def reservar(self, cantidad: Decimal) -> None:
        if not self.disponible or cantidad > self.stock_disponible:
            raise ReglaNegocioError(f"Stock insuficiente de {self.nombre}")
        self.stock_disponible -= cantidad

    def liberar(self, cantidad: Decimal) -> None:
        self.stock_disponible += cantidad

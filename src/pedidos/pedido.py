"""Pedido multipuesto (Lab 07): COMPOSITE + contexto del patrón STATE.

COMPOSITE: Pedido (raíz) contiene PedidoPuesto (compuestos), que contienen LineaPedido (hojas).
Los tres son ItemPedido y responden subtotal() de la misma forma, así que el total del pedido
se calcula recorriendo el árbol sin preguntar qué tipo de elemento es cada uno.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Iterator
from uuid import UUID, uuid4

from catalogo import Comerciante, Producto
from comun.excepciones import ReglaNegocioError
from pagos import Pago
from pedidos.estados import Creado, EstadoPedido, EstadoPedidoPuesto, Pendiente


def a_soles(monto: Decimal) -> Decimal:
    """Redondea al céntimo: un kg fraccionado puede dar S/ 2.625 y ningún medio cobra eso."""
    return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class TipoEntrega(Enum):
    RECOJO_MERCADO = "RECOJO_MERCADO"
    DELIVERY = "DELIVERY"


@dataclass
class Cliente:
    nombre: str
    celular: str
    direccion: str


class ItemPedido(ABC):
    """COMPOSITE: componente común de hojas y compuestos."""

    @abstractmethod
    def subtotal(self) -> Decimal: ...


class LineaPedido(ItemPedido):
    """Hoja: un producto de un puesto."""

    def __init__(self, producto: Producto, cantidad: Decimal, precio_unitario: Decimal):
        self.producto = producto
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario

    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad


class PedidoPuesto(ItemPedido):
    """Compuesto: la parte del pedido que prepara un puesto. Contexto de EstadoPedidoPuesto."""

    def __init__(self, comerciante: Comerciante):
        self.comerciante = comerciante
        self.lineas: list[LineaPedido] = []
        self.motivo_rechazo: str | None = None
        self.fecha_actualizacion = datetime.now()
        self.id: UUID = uuid4()
        self._estado: EstadoPedidoPuesto = Pendiente()

    @property
    def estado(self) -> str:
        return self._estado.nombre

    def cambiar_a(self, nuevo: EstadoPedidoPuesto) -> None:
        self._estado = nuevo
        self.fecha_actualizacion = datetime.now()

    def agregar(self, linea: LineaPedido) -> None:
        self.lineas.append(linea)

    def subtotal(self) -> Decimal:
        return sum((linea.subtotal() for linea in self.lineas), Decimal("0"))

    # --- transiciones: se delegan al objeto estado ---
    def recibir(self) -> None:
        self._estado.recibir(self)

    def marcar_listo(self) -> None:
        self._estado.marcar_listo(self)

    def rechazar(self, motivo: str) -> None:
        self._estado.rechazar(self, motivo)

    def marcar_recogido(self, repartidor_id: UUID, codigo_recojo: str) -> None:
        self._estado.marcar_recogido(self, repartidor_id, codigo_recojo)

    def marcar_entregado(self) -> None:
        self._estado.marcar_entregado(self)

    def anular(self) -> None:
        self._estado.anular(self)


class Pedido(ItemPedido):
    """Raíz del Composite y contexto de EstadoPedido."""

    def __init__(self, cliente: Cliente, tipo_entrega: str = "RECOJO_MERCADO",
                 distrito: str | None = None, codigo: str | None = None):
        self.cliente = cliente
        self.tipo_entrega = TipoEntrega(tipo_entrega)
        self.distrito = distrito
        self.id: UUID = uuid4()
        self.codigo = codigo or self.id.hex[:8].upper()
        self.subpedidos: list[PedidoPuesto] = []
        self.costo_envio = Decimal("0")
        self.medio_pago: str | None = None
        self.pago: Pago | None = None
        self.fecha_creacion = datetime.now()
        self._estado: EstadoPedido = Creado()

    @property
    def estado(self) -> str:
        return self._estado.nombre

    def cambiar_a(self, nuevo: EstadoPedido) -> None:
        self._estado = nuevo

    # --- Composite ---
    def subtotal(self) -> Decimal:
        activos = (pp for pp in self.subpedidos if pp.estado not in ("RECHAZADO", "ANULADO"))
        return sum((pp.subtotal() for pp in activos), Decimal("0"))

    def total(self) -> Decimal:
        return a_soles(self.subtotal() + self.costo_envio)

    def lineas(self) -> Iterator[LineaPedido]:
        for pp in self.subpedidos:
            yield from pp.lineas

    def subpedido_de(self, comerciante: Comerciante) -> PedidoPuesto:
        for pp in self.subpedidos:
            if pp.comerciante.id == comerciante.id:
                return pp
        raise ReglaNegocioError("El puesto no participa en el pedido")

    def _agregar(self, producto: Producto, cantidad: Decimal) -> None:
        """Lo invoca el estado Creado: el primer producto de un puesto crea su PedidoPuesto."""
        try:
            pp = self.subpedido_de(producto.comerciante)
        except ReglaNegocioError:
            pp = PedidoPuesto(producto.comerciante)
            self.subpedidos.append(pp)
        pp.agregar(LineaPedido(producto, cantidad, producto.precio))

    # --- transiciones: se delegan al objeto estado ---
    def agregar_linea(self, producto: Producto, cantidad: Decimal) -> None:
        self._estado.agregar_linea(self, producto, cantidad)

    def confirmar(self) -> None:
        self._estado.confirmar(self)

    def registrar_pago(self, pago: Pago) -> None:
        self._estado.registrar_pago(self, pago)

    def cancelar(self, motivo: str) -> None:
        self._estado.cancelar(self, motivo)

    def marcar_preparado(self) -> None:
        self._estado.marcar_preparado(self)

    def marcar_en_camino(self) -> None:
        self._estado.marcar_en_camino(self)

    def marcar_entregado(self) -> None:
        self._estado.marcar_entregado(self)

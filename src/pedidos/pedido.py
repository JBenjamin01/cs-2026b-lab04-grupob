"""Pedido multipuesto (Lab 07, E2): dominio del Lab 05 adaptado al flujo refactorizado.

Todavía usa transiciones con condicionales sobre el atributo estado (se reemplaza por State en E3).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Iterator
from uuid import UUID, uuid4

from catalogo.modelos import Comerciante, Producto
from comun.excepciones import EstadoInvalidoError, ReglaNegocioError
from pagos.modelos import Pago


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


class LineaPedido:
    def __init__(self, producto: Producto, cantidad: Decimal, precio_unitario: Decimal):
        self.producto = producto
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario

    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad


class PedidoPuesto:
    def __init__(self, comerciante: Comerciante):
        self.comerciante = comerciante
        self.lineas: list[LineaPedido] = []
        self.estado = "PENDIENTE"
        self.motivo_rechazo: str | None = None
        self.fecha_actualizacion = datetime.now()
        self.id: UUID = uuid4()

    def _transicion(self, desde: str, hacia: str) -> None:
        if self.estado != desde:
            raise EstadoInvalidoError(f"{self.estado} -> {hacia} no permitido")
        self.estado = hacia
        self.fecha_actualizacion = datetime.now()

    def agregar(self, linea: LineaPedido) -> None:
        self.lineas.append(linea)

    def subtotal(self) -> Decimal:
        return sum((linea.subtotal() for linea in self.lineas), Decimal("0"))

    def recibir(self) -> None:
        self._transicion("PENDIENTE", "RECIBIDO")

    def marcar_listo(self) -> None:
        self._transicion("RECIBIDO", "LISTO")

    def rechazar(self, motivo: str) -> None:
        self._transicion("RECIBIDO", "RECHAZADO")
        self.motivo_rechazo = motivo

    def marcar_recogido(self, repartidor_id: UUID, codigo_recojo: str) -> None:
        if not codigo_recojo:
            raise ReglaNegocioError("Código de recojo inválido")
        self._transicion("LISTO", "RECOGIDO")

    def marcar_entregado(self) -> None:
        self._transicion("RECOGIDO", "ENTREGADO")

    def anular(self) -> None:
        self._transicion("PENDIENTE", "ANULADO")


class Pedido:
    def __init__(self, cliente: Cliente, tipo_entrega: str = "RECOJO_MERCADO",
                 distrito: str | None = None, codigo: str | None = None):
        self.cliente = cliente
        self.tipo_entrega = TipoEntrega(tipo_entrega)
        self.distrito = distrito
        self.id: UUID = uuid4()
        self.codigo = codigo or self.id.hex[:8].upper()
        self.subpedidos: list[PedidoPuesto] = []
        self.estado = "CREADO"
        self.costo_envio = Decimal("0")
        self.medio_pago: str | None = None
        self.pago: Pago | None = None
        self.fecha_creacion = datetime.now()

    def _exigir(self, *estados: str) -> None:
        if self.estado not in estados:
            raise EstadoInvalidoError(f"Operación no válida en un pedido {self.estado}")

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

    def agregar_linea(self, producto: Producto, cantidad: Decimal) -> None:
        self._exigir("CREADO")
        try:
            pp = self.subpedido_de(producto.comerciante)
        except ReglaNegocioError:
            pp = PedidoPuesto(producto.comerciante)
            self.subpedidos.append(pp)
        pp.agregar(LineaPedido(producto, cantidad, producto.precio))

    def confirmar(self) -> None:
        self._exigir("CREADO")
        if not self.subpedidos:
            raise ReglaNegocioError("El pedido no tiene productos")
        reservadas = []
        try:
            for linea in self.lineas():
                linea.producto.reservar(linea.cantidad)
                reservadas.append(linea)
        except ReglaNegocioError:
            for linea in reservadas:
                linea.producto.liberar(linea.cantidad)
            raise
        self.estado = "PENDIENTE_PAGO"

    def registrar_pago(self, pago: Pago) -> None:
        self._exigir("PENDIENTE_PAGO")
        self.pago = pago
        for pp in self.subpedidos:
            pp.recibir()
        self.estado = "PAGADO"

    def cancelar(self, motivo: str) -> None:
        self._exigir("CREADO", "PENDIENTE_PAGO")
        if self.estado == "PENDIENTE_PAGO":
            for linea in self.lineas():
                linea.producto.liberar(linea.cantidad)
        for pp in self.subpedidos:
            pp.anular()
        self.estado = "CANCELADO"

    def marcar_preparado(self) -> None:
        self._exigir("PAGADO")
        self.estado = "PREPARADO"

    def marcar_en_camino(self) -> None:
        self._exigir("PREPARADO")
        self.estado = "EN_CAMINO"

    def marcar_entregado(self) -> None:
        self._exigir("PREPARADO", "EN_CAMINO")
        for pp in self.subpedidos:
            if pp.estado == "RECOGIDO":
                pp.marcar_entregado()
        self.estado = "ENTREGADO"

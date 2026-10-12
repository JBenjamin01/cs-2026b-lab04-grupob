"""Módulo Pedidos — esqueleto generado con IA (Prompt IA 2) a partir de clases.puml y revisado.

Equivalencia de nombres (regla C5): camelCase en UML = snake_case en Python (PEP 8),
p. ej. calcularTotal() = calcular_total().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from catalogo import Comerciante, Producto
from comun.excepciones import EstadoInvalidoError, ReglaNegocioError
from pagos import Pago


class EstadoPedido(Enum):
    CREADO = "CREADO"
    PENDIENTE_PAGO = "PENDIENTE_PAGO"
    PAGADO = "PAGADO"
    PREPARADO = "PREPARADO"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


class EstadoPedidoPuesto(Enum):
    PENDIENTE = "PENDIENTE"
    RECIBIDO = "RECIBIDO"
    LISTO = "LISTO"
    RECOGIDO = "RECOGIDO"
    ENTREGADO = "ENTREGADO"
    RECHAZADO = "RECHAZADO"
    ANULADO = "ANULADO"


class TipoEntrega(Enum):
    RECOJO_MERCADO = "RECOJO_MERCADO"
    DELIVERY = "DELIVERY"


@dataclass
class Cliente:
    nombre: str
    celular: str
    direccion: str
    id: UUID = field(default_factory=uuid4)


@dataclass
class LineaPedido:
    producto: Producto
    cantidad: Decimal
    precio_unitario: Decimal

    def calcular_subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad


@dataclass
class PedidoPuesto:
    comerciante: Comerciante
    lineas: list[LineaPedido] = field(default_factory=list)
    estado: EstadoPedidoPuesto = EstadoPedidoPuesto.PENDIENTE
    motivo_rechazo: str | None = None
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)

    def _transicion(self, desde: EstadoPedidoPuesto, hacia: EstadoPedidoPuesto) -> None:
        if self.estado is not desde:
            raise EstadoInvalidoError(f"{self.estado.name} -> {hacia.name} no permitido")
        self.estado = hacia
        self.fecha_actualizacion = datetime.now()

    def calcular_subtotal(self) -> Decimal:
        return sum((l.calcular_subtotal() for l in self.lineas), Decimal("0"))

    def recibir(self) -> None:
        self._transicion(EstadoPedidoPuesto.PENDIENTE, EstadoPedidoPuesto.RECIBIDO)

    def marcar_listo(self) -> None:
        self._transicion(EstadoPedidoPuesto.RECIBIDO, EstadoPedidoPuesto.LISTO)

    def rechazar(self, motivo: str) -> None:
        self._transicion(EstadoPedidoPuesto.RECIBIDO, EstadoPedidoPuesto.RECHAZADO)
        self.motivo_rechazo = motivo

    def marcar_recogido(self, repartidor_id: UUID, codigo_recojo: str) -> None:
        if not codigo_recojo:
            raise ReglaNegocioError("Código de recojo inválido")
        self._transicion(EstadoPedidoPuesto.LISTO, EstadoPedidoPuesto.RECOGIDO)

    def marcar_entregado(self) -> None:
        self._transicion(EstadoPedidoPuesto.RECOGIDO, EstadoPedidoPuesto.ENTREGADO)

    def anular(self) -> None:
        self._transicion(EstadoPedidoPuesto.PENDIENTE, EstadoPedidoPuesto.ANULADO)


@dataclass
class Pedido:
    cliente: Cliente
    tipo_entrega: TipoEntrega
    costo_envio: Decimal = Decimal("0")
    subpedidos: list[PedidoPuesto] = field(default_factory=list)
    estado: EstadoPedido = EstadoPedido.CREADO
    pago: Pago | None = None
    codigo_seguimiento: str = field(default_factory=lambda: uuid4().hex[:8].upper())
    fecha_creacion: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)

    def _exigir(self, *estados: EstadoPedido) -> None:
        if self.estado not in estados:
            raise EstadoInvalidoError(f"Operación no válida en {self.estado.name}")

    def agregar_linea(self, producto: Producto, cantidad: Decimal) -> None:
        self._exigir(EstadoPedido.CREADO)
        subpedido = next(
            (s for s in self.subpedidos if s.comerciante.id == producto.comerciante.id), None
        )
        if subpedido is None:  # primer producto de ese puesto: nace el PedidoPuesto
            subpedido = PedidoPuesto(comerciante=producto.comerciante)
            self.subpedidos.append(subpedido)
        subpedido.lineas.append(LineaPedido(producto, cantidad, producto.precio))

    def calcular_total(self) -> Decimal:
        activos = (s for s in self.subpedidos if s.estado is not EstadoPedidoPuesto.RECHAZADO)
        return sum((s.calcular_subtotal() for s in activos), Decimal("0")) + self.costo_envio

    def confirmar(self) -> None:
        self._exigir(EstadoPedido.CREADO)
        if not self.subpedidos:  # regla C3: un pedido tiene 1..* subpedidos
            raise ReglaNegocioError("El pedido no tiene productos")
        reservadas: list[LineaPedido] = []
        try:
            for linea in (l for s in self.subpedidos for l in s.lineas):
                linea.producto.reservar(linea.cantidad)
                reservadas.append(linea)
        except ReglaNegocioError:
            for linea in reservadas:
                linea.producto.liberar(linea.cantidad)
            raise
        self.estado = EstadoPedido.PENDIENTE_PAGO

    def registrar_pago(self, pago: Pago) -> None:
        self._exigir(EstadoPedido.PENDIENTE_PAGO)
        if not pago.esta_confirmado():
            raise ReglaNegocioError("El pago no está confirmado")
        self.pago = pago
        for subpedido in self.subpedidos:
            subpedido.recibir()
        self.estado = EstadoPedido.PAGADO

    def cancelar(self, motivo: str) -> None:
        self._exigir(EstadoPedido.CREADO, EstadoPedido.PENDIENTE_PAGO)
        if self.estado is EstadoPedido.PENDIENTE_PAGO:
            for linea in (l for s in self.subpedidos for l in s.lineas):
                linea.producto.liberar(linea.cantidad)
        for subpedido in self.subpedidos:
            subpedido.anular()
        self.estado = EstadoPedido.CANCELADO

    def buscar_subpedido(self, subpedido_id: UUID) -> PedidoPuesto:
        for subpedido in self.subpedidos:
            if subpedido.id == subpedido_id:
                return subpedido
        raise ReglaNegocioError("Subpedido no encontrado")

    def marcar_preparado(self) -> None:
        self._exigir(EstadoPedido.PAGADO)
        self.estado = EstadoPedido.PREPARADO

    def marcar_en_camino(self) -> None:
        self._exigir(EstadoPedido.PREPARADO)
        self.estado = EstadoPedido.EN_CAMINO

    def marcar_entregado(self) -> None:
        self._exigir(EstadoPedido.PREPARADO, EstadoPedido.EN_CAMINO)
        for subpedido in self.subpedidos:
            if subpedido.estado is EstadoPedidoPuesto.RECOGIDO:
                subpedido.marcar_entregado()
        self.estado = EstadoPedido.ENTREGADO

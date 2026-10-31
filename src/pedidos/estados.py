"""STATE (Lab 07): implementa las máquinas de estados del Lab 05.

La clase base de cada máquina PROHÍBE todas las transiciones; cada estado redefine SOLO las
permitidas. Así, una transición inválida es imposible por construcción y ningún estado
pregunta por el nombre de otro estado.
- EstadoPedidoPuesto: docs/design/estados-pedidopuesto.mmd (7 estados).
- EstadoPedido: estados del pedido de ADR-002 (CREADO, PENDIENTE_PAGO, PAGADO, …).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from comun.excepciones import EstadoInvalidoError, ReglaNegocioError

if TYPE_CHECKING:  # solo para las anotaciones: evita una importación circular
    from catalogo.modelos import Producto
    from pagos.modelos import Pago
    from pedidos.pedido import Pedido, PedidoPuesto


# =============================== Subpedido de un puesto ===============================
class EstadoPedidoPuesto:
    nombre = "?"

    def _invalida(self, operacion: str):
        raise EstadoInvalidoError(f"No se puede {operacion} un subpedido {self.nombre}")

    def recibir(self, pp: PedidoPuesto) -> None:
        self._invalida("recibir")

    def marcar_listo(self, pp: PedidoPuesto) -> None:
        self._invalida("marcar listo")

    def rechazar(self, pp: PedidoPuesto, motivo: str) -> None:
        self._invalida("rechazar")

    def marcar_recogido(self, pp: PedidoPuesto, repartidor_id, codigo_recojo: str) -> None:
        self._invalida("recoger")

    def marcar_entregado(self, pp: PedidoPuesto) -> None:
        self._invalida("entregar")

    def anular(self, pp: PedidoPuesto) -> None:
        self._invalida("anular")


class Pendiente(EstadoPedidoPuesto):
    nombre = "PENDIENTE"

    def recibir(self, pp):
        pp.cambiar_a(Recibido())

    def anular(self, pp):
        pp.cambiar_a(Anulado())


class Recibido(EstadoPedidoPuesto):
    nombre = "RECIBIDO"

    def marcar_listo(self, pp):
        pp.cambiar_a(Listo())

    def rechazar(self, pp, motivo):
        pp.motivo_rechazo = motivo
        pp.cambiar_a(Rechazado())


class Listo(EstadoPedidoPuesto):
    nombre = "LISTO"

    def marcar_recogido(self, pp, repartidor_id, codigo_recojo):
        if not codigo_recojo:
            raise ReglaNegocioError("Código de recojo inválido")
        pp.cambiar_a(Recogido())


class Recogido(EstadoPedidoPuesto):
    nombre = "RECOGIDO"

    def marcar_entregado(self, pp):
        pp.cambiar_a(EntregadoPuesto())


class EntregadoPuesto(EstadoPedidoPuesto):
    nombre = "ENTREGADO"


class Rechazado(EstadoPedidoPuesto):
    nombre = "RECHAZADO"


class Anulado(EstadoPedidoPuesto):
    nombre = "ANULADO"


# ===================================== Pedido =====================================
class EstadoPedido:
    nombre = "?"

    def _invalida(self, operacion: str):
        raise EstadoInvalidoError(f"No se puede {operacion} un pedido {self.nombre}")

    def agregar_linea(self, pedido: Pedido, producto: Producto, cantidad) -> None:
        self._invalida("agregar productos a")

    def confirmar(self, pedido: Pedido) -> None:
        self._invalida("confirmar")

    def registrar_pago(self, pedido: Pedido, pago: Pago) -> None:
        self._invalida("registrar el pago de")

    def cancelar(self, pedido: Pedido, motivo: str) -> None:
        self._invalida("cancelar")

    def marcar_preparado(self, pedido: Pedido) -> None:
        self._invalida("preparar")

    def marcar_en_camino(self, pedido: Pedido) -> None:
        self._invalida("despachar")

    def marcar_entregado(self, pedido: Pedido) -> None:
        self._invalida("entregar")


class Creado(EstadoPedido):
    nombre = "CREADO"

    def agregar_linea(self, pedido, producto, cantidad):
        pedido._agregar(producto, cantidad)

    def confirmar(self, pedido):
        if not pedido.subpedidos:  # regla C3 del Lab 05: 1..* subpedidos
            raise ReglaNegocioError("El pedido no tiene productos")
        reservadas = []
        try:
            for linea in pedido.lineas():
                linea.producto.reservar(linea.cantidad)
                reservadas.append(linea)
        except ReglaNegocioError:
            for linea in reservadas:
                linea.producto.liberar(linea.cantidad)
            raise
        pedido.cambiar_a(PendientePago())

    def cancelar(self, pedido, motivo):
        for pp in pedido.subpedidos:
            pp.anular()
        pedido.cambiar_a(Cancelado())


class PendientePago(EstadoPedido):
    nombre = "PENDIENTE_PAGO"

    def registrar_pago(self, pedido, pago):
        pedido.pago = pago
        for pp in pedido.subpedidos:
            pp.recibir()
        pedido.cambiar_a(Pagado())

    def cancelar(self, pedido, motivo):
        for linea in pedido.lineas():
            linea.producto.liberar(linea.cantidad)
        for pp in pedido.subpedidos:
            pp.anular()
        pedido.cambiar_a(Cancelado())


class Pagado(EstadoPedido):
    nombre = "PAGADO"

    def marcar_preparado(self, pedido):
        pedido.cambiar_a(Preparado())


class Preparado(EstadoPedido):
    nombre = "PREPARADO"

    def marcar_en_camino(self, pedido):
        pedido.cambiar_a(EnCamino())

    def marcar_entregado(self, pedido):
        _entregar(pedido)


class EnCamino(EstadoPedido):
    nombre = "EN_CAMINO"

    def marcar_entregado(self, pedido):
        _entregar(pedido)


def _entregar(pedido: Pedido) -> None:
    for pp in pedido.subpedidos:
        if pp.estado == "RECOGIDO":
            pp.marcar_entregado()
    pedido.cambiar_a(Entregado())


class Entregado(EstadoPedido):
    nombre = "ENTREGADO"


class Cancelado(EstadoPedido):
    nombre = "CANCELADO"

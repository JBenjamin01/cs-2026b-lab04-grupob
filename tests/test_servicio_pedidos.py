"""Pruebas de los criterios de aceptación de HU-03 con dobles de los puertos."""
from decimal import Decimal
from uuid import UUID

from catalogo.modelos import Comerciante, Producto
from notificaciones.puertos import NotificadorMensajeria
from pagos.modelos import EstadoPago, Pago, PasarelaPago
from pedidos.dominio import Cliente, EstadoPedido, EstadoPedidoPuesto, Pedido, TipoEntrega
from pedidos.puertos import RepositorioPedidos
from pedidos.servicio import ServicioPedidos


class RepoMemoria(RepositorioPedidos):
    def __init__(self, pedido): self.pedido = pedido
    def buscar_por_id(self, id): return self.pedido
    def buscar_por_subpedido(self, subpedido_id): return self.pedido
    def guardar(self, pedido): self.pedido = pedido


class PasarelaFalsa(PasarelaPago):
    def __init__(self, estado): self.estado, self.reembolsos = estado, []
    def iniciar_cobro(self, pedido_id: UUID, monto, celular, codigo_aprobacion):
        return Pago(pedido_id, monto, "TX-1", self.estado)
    def reembolsar(self, pago_id, monto): self.reembolsos.append(monto)


class NotificadorFalso(NotificadorMensajeria):
    def __init__(self): self.enviados = []
    def notificar_comerciante(self, celular, resumen): self.enviados.append(celular)
    def notificar_cliente(self, celular, mensaje): self.enviados.append(celular)


def pedido_dos_puestos():
    papa = Producto("Papa", Decimal("3"), "kg", Decimal("10"), Comerciante("A", "P-1", "911"))
    queso = Producto("Queso", Decimal("20"), "kg", Decimal("5"), Comerciante("B", "P-2", "922"))
    pedido = Pedido(Cliente("Demo", "900", "Cercado"), TipoEntrega.RECOJO_MERCADO)
    pedido.agregar_linea(papa, Decimal("2"))
    pedido.agregar_linea(queso, Decimal("1"))
    return pedido, papa, queso


def test_ca1_pago_aprobado():
    pedido, _, _ = pedido_dos_puestos()
    notif = NotificadorFalso()
    s = ServicioPedidos(RepoMemoria(pedido), PasarelaFalsa(EstadoPago.CONFIRMADO), notif)
    s.confirmar_y_pagar(pedido.id, "900", "123456")
    assert pedido.estado is EstadoPedido.PAGADO
    assert all(pp.estado is EstadoPedidoPuesto.RECIBIDO for pp in pedido.subpedidos)
    assert notif.enviados == ["911", "922"]


def test_ca2_pago_rechazado_libera_stock():
    pedido, papa, queso = pedido_dos_puestos()
    s = ServicioPedidos(RepoMemoria(pedido), PasarelaFalsa(EstadoPago.RECHAZADO), NotificadorFalso())
    s.confirmar_y_pagar(pedido.id, "900", "000000")
    assert pedido.estado is EstadoPedido.CANCELADO
    assert (papa.stock_disponible, queso.stock_disponible) == (Decimal("10"), Decimal("5"))
    assert all(pp.estado is EstadoPedidoPuesto.ANULADO for pp in pedido.subpedidos)


def test_ca3_rechazo_de_un_puesto_reembolsa_solo_su_parte():
    pedido, _, _ = pedido_dos_puestos()
    pasarela = PasarelaFalsa(EstadoPago.CONFIRMADO)
    s = ServicioPedidos(RepoMemoria(pedido), pasarela, NotificadorFalso())
    s.confirmar_y_pagar(pedido.id, "900", "123456")
    puesto_b = pedido.subpedidos[1]
    s.procesar_rechazo_puesto(puesto_b.id, "sin queso")
    assert puesto_b.estado is EstadoPedidoPuesto.RECHAZADO
    assert pedido.subpedidos[0].estado is EstadoPedidoPuesto.RECIBIDO
    assert pasarela.reembolsos == [Decimal("20")]
    assert pedido.estado is EstadoPedido.PAGADO


def test_webhook_duplicado_se_ignora():
    pedido, _, _ = pedido_dos_puestos()
    notif = NotificadorFalso()
    s = ServicioPedidos(RepoMemoria(pedido), PasarelaFalsa(EstadoPago.PENDIENTE), notif)
    s.confirmar_y_pagar(pedido.id, "900", "123456")
    assert pedido.estado is EstadoPedido.PENDIENTE_PAGO
    confirmado = Pago(pedido.id, pedido.calcular_total(), "TX-1", EstadoPago.CONFIRMADO)
    s.procesar_webhook_pago(pedido.id, confirmado)
    s.procesar_webhook_pago(pedido.id, confirmado)  # reenvío del proveedor
    assert pedido.estado is EstadoPedido.PAGADO
    assert notif.enviados == ["911", "922"]

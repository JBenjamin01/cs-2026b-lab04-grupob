"""Pruebas que DEMUESTRAN cada patrón (Lab 07). Solo usan la versión con patrones."""
from decimal import Decimal
from uuid import uuid4

import pytest

from arranque import crear_servicio_pedidos
from catalogo.modelos import Comerciante, Producto
from comun.excepciones import EstadoInvalidoError
from pagos.modelos import EstadoPago, Pago, PasarelaPago
from pagos.pasarelas import FabricaPasarelas, PlinAdapter, YapeAdapter
from pedidos.externos import PlinClient, YapeSDK
from pedidos.pedido import Cliente, Pedido, PedidoPuesto
from pedidos.servicio import ServicioPedidos


@pytest.fixture
def productos():
    rosa = Comerciante("Rosa", "P-12", "911000001")
    juan = Comerciante("Juan", "P-40", "922000002")
    return (Producto("Papa amarilla", Decimal("3.50"), "kg", Decimal("20"), rosa),
            Producto("Queso paria", Decimal("22.00"), "kg", Decimal("5"), juan))


def nuevo_pedido(productos, tipo="RECOJO_MERCADO", distrito=None):
    papa, queso = productos
    p = Pedido(Cliente("Cliente demo", "959000111", "Calle Demo 123"), tipo, distrito, codigo="SC-0001")
    p.agregar_linea(papa, Decimal("4"))
    p.agregar_linea(queso, Decimal("1"))
    return p


# ================================ E2: STRATEGY + ADAPTER + FACTORY ================================
class PasarelaTarjetaFalsa(PasarelaPago):
    def __init__(self):
        self.cobros = []

    def iniciar_cobro(self, pedido_id, monto, celular, codigo_aprobacion):
        self.cobros.append(monto)
        return Pago(pedido_id, monto, "TJ-1", EstadoPago.CONFIRMADO)

    def reembolsar(self, referencia_proveedor, monto):
        pass


def test_open_closed_nuevo_medio_sin_modificar_el_servicio(productos):
    tarjeta = PasarelaTarjetaFalsa()
    fabrica = FabricaPasarelas()
    fabrica.registrar("TARJETA", lambda: tarjeta)            # solo se REGISTRA el medio nuevo
    servicio = ServicioPedidos(fabrica, [])
    assert servicio.confirmar_y_pagar(nuevo_pedido(productos), "TARJETA") == "PAGADO"
    assert tarjeta.cobros == [Decimal("36.00")]


def test_factory_rechaza_un_medio_no_registrado():
    with pytest.raises(ValueError, match="no soportado"):
        FabricaPasarelas().crear("BITCOIN")


def test_adapters_traducen_soles_y_centimos():
    yape, plin = YapeSDK(), PlinClient()
    pago_y = YapeAdapter(yape).iniciar_cobro(uuid4(), Decimal("12.50"), "9", "123456")
    pago_p = PlinAdapter(plin).iniciar_cobro(uuid4(), Decimal("12.50"), "9", "123456")
    assert (yape.montos, plin.montos) == ([Decimal("12.50")], [1250])
    assert pago_y.esta_confirmado() and pago_p.esta_confirmado()
    assert (pago_y.referencia_proveedor, pago_p.referencia_proveedor) == ("YP-0001", "PL-0001")


def test_los_montos_se_redondean_al_centimo(productos):
    """0.75 kg x S/ 3.50 = S/ 2.625: la versión antes cobraba 2.625 por Yape y 262 céntimos por Plin."""
    papa, _ = productos
    yape, plin = YapeSDK(), PlinClient()
    app = crear_servicio_pedidos(yape=yape, plin=plin)
    for medio in ("YAPE", "PLIN"):
        p = Pedido(Cliente("Cliente demo", "959000111", "Calle Demo 123"))
        p.agregar_linea(papa, Decimal("0.75"))
        app.servicio.confirmar_y_pagar(p, medio)
    assert (yape.montos, plin.montos) == ([Decimal("2.63")], [263])


# ================================ E3: STATE ================================
def test_state_impide_transiciones_invalidas_del_subpedido(productos):
    pp = PedidoPuesto(productos[0].comerciante)
    with pytest.raises(EstadoInvalidoError):
        pp.marcar_listo()                    # PENDIENTE -> LISTO no existe en la máquina del Lab 05
    pp.recibir()
    pp.rechazar("sin stock")
    with pytest.raises(EstadoInvalidoError):
        pp.marcar_listo()                    # RECHAZADO es final
    assert pp.estado == "RECHAZADO"


def test_state_del_pedido_bloquea_cambios_despues_de_pagar(productos):
    app = crear_servicio_pedidos()
    p = nuevo_pedido(productos)
    app.servicio.confirmar_y_pagar(p, "YAPE")
    with pytest.raises(EstadoInvalidoError):
        p.agregar_linea(productos[0], Decimal("1"))
    with pytest.raises(EstadoInvalidoError):
        p.cancelar("me arrepentí")           # un pedido PAGADO se gestiona por reembolso (CA-3)


def test_state_ciclo_completo_hasta_entregado(productos):
    app = crear_servicio_pedidos()
    p = nuevo_pedido(productos, "DELIVERY", "Cercado")
    app.servicio.confirmar_y_pagar(p, "YAPE")
    for pp in p.subpedidos:
        pp.marcar_listo()
        pp.marcar_recogido(uuid4(), "QR-1")
    p.marcar_preparado()
    p.marcar_en_camino()
    p.marcar_entregado()
    assert p.estado == "ENTREGADO"
    assert [pp.estado for pp in p.subpedidos] == ["ENTREGADO", "ENTREGADO"]

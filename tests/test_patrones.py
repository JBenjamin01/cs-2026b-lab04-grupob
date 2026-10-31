"""Pruebas que DEMUESTRAN cada patrón (Lab 07, E2–E5). Solo usan la versión con patrones."""
from decimal import Decimal
from uuid import uuid4

import pytest

from arranque import crear_normalizador, crear_servicio_pedidos
from catalogo.ia import (ClaudeAdapter, ConCache, LimpiarFormato, LongitudMaxima, SinPreciosNiCantidades,
                         SoloDelCatalogo)
from catalogo.modelos import Comerciante, Producto
from comun.eventos import PublicadorEventos, Suscriptor
from comun.excepciones import EstadoInvalidoError
from notificaciones.puertos import BandejaMensajes
from notificaciones.suscriptores import NotificadorCliente, NotificadorComerciantes
from pagos.modelos import EstadoPago, Pago, PasarelaPago
from pagos.pasarelas import ConReintentos, FabricaPasarelas, PlinAdapter, YapeAdapter
from pedidos.externos import ClienteClaudeSimulado, PlinClient, YapeSDK
from pedidos.pedido import Cliente, LineaPedido, Pedido, PedidoPuesto
from pedidos.servicio import ServicioPedidos
from pedidos.tarifas import TarifaEnvio, tarifas_por_defecto


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
    servicio = ServicioPedidos(fabrica, PublicadorEventos(), tarifas_por_defecto())
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


# ================================ E4: OBSERVER, DECORATOR, COMPOSITE, STRATEGY (tarifa) ================================
class Auditoria(Suscriptor):
    def __init__(self):
        self.registros = []

    def actualizar(self, evento, datos):
        self.registros.append((evento, datos["codigo"]))


def test_observer_nuevo_suscriptor_sin_tocar_el_servicio(productos):
    fabrica = FabricaPasarelas()
    fabrica.registrar("YAPE", lambda: YapeAdapter(YapeSDK()))
    publicador = PublicadorEventos()
    auditoria = Auditoria()
    publicador.suscribir("pedido_pagado", auditoria)      # interesado nuevo: solo se suscribe
    ServicioPedidos(fabrica, publicador, tarifas_por_defecto()).confirmar_y_pagar(nuevo_pedido(productos), "YAPE")
    assert auditoria.registros == [("pedido_pagado", "SC-0001")]


def test_webhook_duplicado_se_ignora(productos):
    class PasarelaPendiente(PasarelaTarjetaFalsa):
        def iniciar_cobro(self, pedido_id, monto, celular, codigo_aprobacion):
            return Pago(pedido_id, monto, "TX-9", EstadoPago.PENDIENTE)

    fabrica = FabricaPasarelas()
    fabrica.registrar("YAPE", PasarelaPendiente)
    eventos = []
    publicador = PublicadorEventos()
    publicador.suscribir("pedido_pagado", NotificadorCliente(BandejaMensajes(eventos)))
    servicio = ServicioPedidos(fabrica, publicador, tarifas_por_defecto())
    p = nuevo_pedido(productos)
    assert servicio.confirmar_y_pagar(p, "YAPE") == "PENDIENTE_PAGO"
    confirmado = Pago(p.id, p.total(), "TX-9", EstadoPago.CONFIRMADO)
    servicio.procesar_webhook_pago(p, confirmado)
    servicio.procesar_webhook_pago(p, confirmado)   # el proveedor reenvía el webhook
    assert p.estado == "PAGADO"
    assert len(eventos) == 1


def test_observer_un_aviso_por_puesto():
    eventos = []
    NotificadorComerciantes(BandejaMensajes(eventos)).actualizar("pedido_pagado", {
        "codigo": "SC-9", "puestos": [{"celular": "1", "numero_puesto": "A", "productos": 2},
                                      {"celular": "2", "numero_puesto": "B", "productos": 1}]})
    assert eventos == ["whatsapp:1:Pedido SC-9 - 2 producto(s) para el puesto A",
                       "whatsapp:2:Pedido SC-9 - 1 producto(s) para el puesto B"]


class PasarelaQueFalla(PasarelaPago):
    def __init__(self, timeouts, estado=EstadoPago.CONFIRMADO):
        self.timeouts, self.estado, self.llamadas = timeouts, estado, 0

    def iniciar_cobro(self, pedido_id, monto, celular, codigo_aprobacion):
        self.llamadas += 1
        if self.llamadas <= self.timeouts:
            raise TimeoutError
        return Pago(pedido_id, monto, "X", self.estado)

    def reembolsar(self, referencia_proveedor, monto):
        pass


def test_decorator_reintentos_solo_ante_timeout():
    interna = PasarelaQueFalla(timeouts=2)
    assert ConReintentos(interna).iniciar_cobro(uuid4(), Decimal("1"), "9", "1").esta_confirmado()
    assert interna.llamadas == 3
    rechazo = PasarelaQueFalla(timeouts=0, estado=EstadoPago.RECHAZADO)
    assert ConReintentos(rechazo).iniciar_cobro(uuid4(), Decimal("1"), "9", "1").estado is EstadoPago.RECHAZADO
    assert rechazo.llamadas == 1                          # un rechazo NUNCA se reintenta


def test_decorator_reintentos_agotados_marca_expirado():
    pago = ConReintentos(PasarelaQueFalla(timeouts=5), intentos=3).iniciar_cobro(uuid4(), Decimal("1"), "9", "1")
    assert pago.estado is EstadoPago.EXPIRADO


def test_composite_subtotal_recursivo(productos):
    papa, queso = productos
    pp = PedidoPuesto(papa.comerciante)
    pp.agregar(LineaPedido(papa, Decimal("2"), Decimal("3.50")))
    pp.agregar(LineaPedido(papa, Decimal("1"), Decimal("3.50")))
    assert pp.subtotal() == Decimal("10.50")             # compuesto = suma de sus hojas
    p = nuevo_pedido(productos)
    assert p.subtotal() == sum((item.subtotal() for item in p.subpedidos), Decimal("0"))
    assert [type(i).__name__ for i in p.lineas()] == ["LineaPedido", "LineaPedido"]


def test_composite_agrupa_por_puesto(productos):
    papa, queso = productos
    p = nuevo_pedido(productos)
    p.agregar_linea(papa, Decimal("1"))                   # mismo puesto: no crea otro subpedido
    assert [len(pp.lineas) for pp in p.subpedidos] == [2, 1]


class TarifaPlana(TarifaEnvio):
    def calcular(self, subtotal, distrito):
        return Decimal("7")


def test_strategy_tarifa_nueva_sin_tocar_el_servicio(productos):
    fabrica = FabricaPasarelas()
    fabrica.registrar("YAPE", lambda: YapeAdapter(YapeSDK()))
    tarifas = tarifas_por_defecto() | {"DELIVERY": TarifaPlana()}
    p = nuevo_pedido(productos, "DELIVERY", "Socabaya")
    ServicioPedidos(fabrica, PublicadorEventos(), tarifas).confirmar_y_pagar(p, "YAPE")
    assert p.costo_envio == Decimal("7")


# ================================ E5: IA AISLADA ================================
def test_decorator_cache_evita_llamadas_repetidas():
    claude = ClienteClaudeSimulado("Choclo")
    proveedor = ConCache(ClaudeAdapter(claude))
    assert proveedor.completar("p") == proveedor.completar("p") == "Choclo"
    assert claude.llamadas == 1


def test_normalizador_con_cache_no_repite_la_llamada():
    claude = ClienteClaudeSimulado("Papa amarilla")
    n = crear_normalizador(["Papa amarilla"], claude=claude)
    n.sugerir_nombre("papa amarila")
    n.sugerir_nombre("papa amarila")
    assert claude.llamadas == 1


def test_chain_cada_guardrail_bloquea_lo_suyo():
    catalogo = ["Papa amarilla"]
    with pytest.raises(ValueError, match="precio"):
        SinPreciosNiCantidades().validar("Papa a S/ 2")
    with pytest.raises(ValueError, match="caracteres"):
        LongitudMaxima(10).validar("Papa amarilla de Chiguata")
    with pytest.raises(ValueError, match="catálogo"):
        SoloDelCatalogo(catalogo).validar("Papa huayro")
    cadena = LimpiarFormato(SinPreciosNiCantidades(LongitudMaxima(40, SoloDelCatalogo(catalogo))))
    assert cadena.validar('  "papa AMARILLA."  ') == "Papa amarilla"


def test_chain_el_orden_importa():
    """Sin limpiar primero, las comillas harían fallar a SoloDelCatalogo."""
    with pytest.raises(ValueError):
        SoloDelCatalogo(["Rocoto"]).validar('"Rocoto"')
    assert LimpiarFormato(SoloDelCatalogo(["Rocoto"])).validar('"Rocoto"') == "Rocoto"

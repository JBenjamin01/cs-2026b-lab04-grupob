"""Iteración 3 de ADD (Lab 08, QA-09): circuit breaker + outbox de pagos pendientes (ADR-008)."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from arranque import crear_servicio_pedidos
from catalogo.modelos import Comerciante, Producto
from pagos import CircuitoAbierto, ConCircuitBreaker, EstadoPago, Pago, PasarelaPago
from pedidos.externos import YapeSDK
from pedidos.pedido import Cliente, Pedido


class Reloj:
    """Reloj controlable: now() para el servicio y monotonic() para el circuito."""

    def __init__(self):
        self.s = 0.0

    def avanzar(self, minutos):
        self.s += minutos * 60

    def now(self):
        return datetime(2026, 10, 31, 8, 30) + timedelta(seconds=self.s)

    def monotonic(self):
        return self.s


class ProveedorCaido(PasarelaPago):
    def __init__(self):
        self.llamadas, self.caido = 0, True

    def iniciar_cobro(self, pedido_id, monto, celular, codigo_aprobacion):
        self.llamadas += 1
        if self.caido:
            return Pago(pedido_id, monto, None, EstadoPago.EXPIRADO)   # reintentos agotados
        return Pago(pedido_id, monto, "OK-1", EstadoPago.CONFIRMADO)

    def reembolsar(self, referencia_proveedor, monto):
        pass


def nuevo_pedido():
    papa = Producto("Papa amarilla", Decimal("3.50"), "kg", Decimal("100"), Comerciante("Rosa", "P-12", "911000001"))
    p = Pedido(Cliente("Cliente demo", "959000111", "Calle Demo 123"), "RECOJO_MERCADO", None)
    p.agregar_linea(papa, Decimal("4"))
    return p, papa


def yape_caido():
    return YapeSDK(fallas=10**6)         # todas las llamadas lanzan TimeoutError hasta que se "recupere"


def recuperar(yape):
    yape.fallas = yape.llamadas


# ---------------------------------------------------------------- circuit breaker (unidad)
def test_circuito_se_abre_tras_tres_fallas_y_ya_no_llama_al_proveedor():
    reloj, prov = Reloj(), ProveedorCaido()
    cb = ConCircuitBreaker(prov, umbral=3, espera_s=60, reloj=reloj.monotonic)
    for _ in range(3):
        assert cb.iniciar_cobro(None, Decimal("10"), "959", "1").estado is EstadoPago.EXPIRADO
    assert cb.estado == "ABIERTO"
    with pytest.raises(CircuitoAbierto):
        cb.iniciar_cobro(None, Decimal("10"), "959", "1")
    assert prov.llamadas == 3                      # la cuarta no llegó al proveedor caído


def test_semiabierto_se_cierra_si_el_proveedor_se_recupera_y_se_reabre_si_no():
    reloj, prov = Reloj(), ProveedorCaido()
    cb = ConCircuitBreaker(prov, umbral=1, espera_s=60, reloj=reloj.monotonic)
    cb.iniciar_cobro(None, Decimal("10"), "959", "1")
    reloj.avanzar(1)
    assert cb.estado == "SEMIABIERTO"
    cb.iniciar_cobro(None, Decimal("10"), "959", "1")          # la prueba falla: vuelve a abrirse
    assert cb.estado == "ABIERTO"
    reloj.avanzar(1)
    prov.caido = False
    assert cb.iniciar_cobro(None, Decimal("10"), "959", "1").esta_confirmado()
    assert cb.estado == "CERRADO"


# ---------------------------------------------------------------- servicio + outbox (QA-09)
def test_caida_del_proveedor_deja_el_pedido_pendiente_en_la_outbox():
    yape = yape_caido()
    app = crear_servicio_pedidos(yape=yape, reloj=Reloj())
    p, papa = nuevo_pedido()
    assert app.servicio.confirmar_y_pagar(p, "YAPE") == "PENDIENTE_PAGO"
    assert [x.pedido_id for x in app.pendientes.pendientes()] == [p.id]
    assert papa.stock_disponible == Decimal("96")             # el stock sigue reservado
    assert "pedido_pagado" not in " ".join(app.eventos)


def test_con_el_circuito_abierto_no_se_llama_al_proveedor_y_nada_se_pierde():
    yape, reloj = yape_caido(), Reloj()
    app = crear_servicio_pedidos(yape=yape, reloj=reloj)
    pedidos = [nuevo_pedido()[0] for _ in range(10)]
    for p in pedidos:
        app.servicio.confirmar_y_pagar(p, "YAPE")
    assert yape.llamadas == 9                                 # 3 pedidos x 3 intentos; luego se abre
    assert len(app.pendientes.pendientes()) == 10
    assert all(p.estado == "PENDIENTE_PAGO" for p in pedidos)


def test_al_recuperarse_el_worker_cobra_los_pendientes():
    yape, reloj = yape_caido(), Reloj()
    app = crear_servicio_pedidos(yape=yape, reloj=reloj)
    pedidos = [nuevo_pedido()[0] for _ in range(5)]
    for p in pedidos:
        app.servicio.confirmar_y_pagar(p, "YAPE")
    reloj.avanzar(2)
    recuperar(yape)
    assert app.servicio.reintentar_pagos_pendientes() == 5
    assert all(p.estado == "PAGADO" for p in pedidos)
    assert app.pendientes.pendientes() == []


def test_si_sigue_caido_el_worker_no_insiste():
    yape, reloj = yape_caido(), Reloj()
    app = crear_servicio_pedidos(yape=yape, reloj=reloj)
    for _ in range(5):
        app.servicio.confirmar_y_pagar(nuevo_pedido()[0], "YAPE")
    llamadas = yape.llamadas
    reloj.avanzar(0.5)                                        # el circuito sigue ABIERTO
    assert app.servicio.reintentar_pagos_pendientes() == 0
    assert yape.llamadas == llamadas


def test_pasada_la_ventana_de_15_min_se_cancela_y_libera_stock():
    yape, reloj = yape_caido(), Reloj()
    app = crear_servicio_pedidos(yape=yape, reloj=reloj)
    p, papa = nuevo_pedido()
    app.servicio.confirmar_y_pagar(p, "YAPE")
    reloj.avanzar(16)
    app.servicio.reintentar_pagos_pendientes()
    assert p.estado == "CANCELADO"
    assert papa.stock_disponible == Decimal("100")
    assert app.pendientes.pendientes() == []


def test_si_el_webhook_ya_resolvio_el_pago_el_worker_lo_descarta():
    yape, reloj = yape_caido(), Reloj()
    app = crear_servicio_pedidos(yape=yape, reloj=reloj)
    p, _ = nuevo_pedido()
    app.servicio.confirmar_y_pagar(p, "YAPE")
    app.servicio.procesar_webhook_pago(p, Pago(p.id, p.total(), "YP-77", EstadoPago.CONFIRMADO))
    reloj.avanzar(2)
    recuperar(yape)
    llamadas = yape.llamadas
    assert app.servicio.reintentar_pagos_pendientes() == 0
    assert yape.llamadas == llamadas                          # no se cobra dos veces
    assert p.estado == "PAGADO"

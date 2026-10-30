"""Pruebas de CARACTERIZACIÓN (Lab 07, E1): describen lo que el flujo hace hoy.

Las mismas pruebas se ejecutan sobre la versión antes y la versión con patrones gracias al
fixture parametrizado. Si pasan en ambas, el refactor conservó el comportamiento observable
(estado, eventos, montos cobrados, stock y excepciones). Ninguna prueba usa servicios reales.
"""
import importlib
from decimal import Decimal

import pytest

from catalogo.modelos import Comerciante, Producto
from pedidos.externos import ClienteClaudeSimulado, ModeloLocalSimulado, PlinClient, YapeSDK

VERSIONES = ["pedidos.antes.servicio", "arranque"]
CATALOGO = ["Papa amarilla", "Queso paria", "Rocoto", "Choclo"]


@pytest.fixture(params=VERSIONES)
def m(request):
    return importlib.import_module(request.param)


@pytest.fixture
def puestos():
    rosa = Comerciante("Rosa", "P-12", "911000001")
    juan = Comerciante("Juan", "P-40", "922000002")
    papa = Producto("Papa amarilla", Decimal("3.50"), "kg", Decimal("20"), rosa)
    queso = Producto("Queso paria", Decimal("22.00"), "kg", Decimal("5"), juan)
    return rosa, juan, papa, queso


def pedido_dos_puestos(m, puestos, tipo="RECOJO_MERCADO", distrito=None, kg_papa="4", kg_queso="1"):
    _, _, papa, queso = puestos
    p = m.Pedido(m.Cliente("Cliente demo", "959000111", "Calle Demo 123"), tipo, distrito, codigo="SC-0001")
    p.agregar_linea(papa, Decimal(kg_papa))
    p.agregar_linea(queso, Decimal(kg_queso))
    return p


# ---------------------------------------------------------------- pagos aprobados
def test_pago_yape_aprobado_recibe_subpedidos_y_avisa(m, puestos):
    app = m.crear_servicio_pedidos()
    p = pedido_dos_puestos(m, puestos)
    assert app.servicio.confirmar_y_pagar(p, "YAPE") == "PAGADO"
    assert [s.estado for s in p.subpedidos] == ["RECIBIDO", "RECIBIDO"]
    assert app.eventos == [
        "whatsapp:911000001:Pedido SC-0001 - 1 producto(s) para el puesto P-12",
        "whatsapp:922000002:Pedido SC-0001 - 1 producto(s) para el puesto P-40",
        "whatsapp:959000111:Pedido SC-0001 pagado: S/ 36.00",
    ]


def test_pago_plin_cobra_en_centimos(m, puestos):
    plin = PlinClient()
    app = m.crear_servicio_pedidos(plin=plin)
    assert app.servicio.confirmar_y_pagar(pedido_dos_puestos(m, puestos), "PLIN") == "PAGADO"
    assert plin.montos == [3600]


def test_un_solo_cobro_por_el_total_del_pedido(m, puestos):
    yape = YapeSDK()
    m.crear_servicio_pedidos(yape=yape).servicio.confirmar_y_pagar(pedido_dos_puestos(m, puestos), "YAPE")
    assert yape.montos == [Decimal("36.00")]


# ---------------------------------------------------------------- pagos rechazados y reintentos
def test_pago_rechazado_cancela_libera_stock_y_no_avisa(m, puestos):
    _, _, papa, queso = puestos
    app = m.crear_servicio_pedidos()
    p = pedido_dos_puestos(m, puestos)
    assert app.servicio.confirmar_y_pagar(p, "YAPE", codigo_aprobacion="000000") == "CANCELADO"
    assert [s.estado for s in p.subpedidos] == ["ANULADO", "ANULADO"]
    assert (papa.stock_disponible, queso.stock_disponible) == (Decimal("20"), Decimal("5"))
    assert app.eventos == []


def test_reintenta_tras_dos_timeouts(m, puestos):
    yape = YapeSDK(fallas=2)
    app = m.crear_servicio_pedidos(yape=yape)
    assert app.servicio.confirmar_y_pagar(pedido_dos_puestos(m, puestos), "YAPE") == "PAGADO"
    assert yape.llamadas == 3


def test_tres_timeouts_cancelan_el_pedido(m, puestos):
    plin = PlinClient(fallas=3)
    app = m.crear_servicio_pedidos(plin=plin)
    assert app.servicio.confirmar_y_pagar(pedido_dos_puestos(m, puestos), "PLIN") == "CANCELADO"
    assert plin.llamadas == 3


def test_un_rechazo_no_se_reintenta(m, puestos):
    yape = YapeSDK(limite=Decimal("10"))
    app = m.crear_servicio_pedidos(yape=yape)
    assert app.servicio.confirmar_y_pagar(pedido_dos_puestos(m, puestos), "YAPE") == "CANCELADO"
    assert yape.llamadas == 1


# ---------------------------------------------------------------- validaciones y transiciones inválidas
def test_no_se_paga_dos_veces(m, puestos):
    yape = YapeSDK()
    app = m.crear_servicio_pedidos(yape=yape)
    p = pedido_dos_puestos(m, puestos)
    app.servicio.confirmar_y_pagar(p, "YAPE")
    with pytest.raises(ValueError):
        app.servicio.confirmar_y_pagar(p, "YAPE")
    assert yape.llamadas == 1


def test_pedido_sin_productos_no_se_confirma(m):
    p = m.Pedido(m.Cliente("Cliente demo", "959000111", "Calle Demo 123"), "RECOJO_MERCADO", None, codigo="SC-0002")
    with pytest.raises(ValueError):
        m.crear_servicio_pedidos().servicio.confirmar_y_pagar(p, "YAPE")
    assert p.estado == "CREADO"


def test_stock_insuficiente_no_reserva_nada(m, puestos):
    _, _, papa, queso = puestos
    p = pedido_dos_puestos(m, puestos, kg_queso="9")
    with pytest.raises(ValueError):
        m.crear_servicio_pedidos().servicio.confirmar_y_pagar(p, "YAPE")
    assert (papa.stock_disponible, queso.stock_disponible) == (Decimal("20"), Decimal("5"))
    assert p.estado == "CREADO"


def test_medio_no_soportado_no_altera_el_pedido(m, puestos):
    if m.__name__ == "pedidos.antes.servicio":
        pytest.xfail("Error de la versión antes: valida el medio DESPUÉS de reservar stock y cambiar el estado")
    _, _, papa, _ = puestos
    p = pedido_dos_puestos(m, puestos)
    with pytest.raises(ValueError):
        m.crear_servicio_pedidos().servicio.confirmar_y_pagar(p, "TARJETA")
    assert p.estado == "CREADO"
    assert papa.stock_disponible == Decimal("20")


# ---------------------------------------------------------------- delivery
@pytest.mark.parametrize("distrito, envio", [("Cercado", "5"), ("Cayma", "8"), ("Socabaya", "12")])
def test_tarifa_de_delivery_por_zona(m, puestos, distrito, envio):
    yape = YapeSDK()
    p = pedido_dos_puestos(m, puestos, "DELIVERY", distrito)
    m.crear_servicio_pedidos(yape=yape).servicio.confirmar_y_pagar(p, "YAPE")
    assert p.costo_envio == Decimal(envio)
    assert yape.montos == [Decimal("36.00") + Decimal(envio)]


def test_delivery_gratis_desde_150_soles(m, puestos):
    p = pedido_dos_puestos(m, puestos, "DELIVERY", "Socabaya", kg_papa="20", kg_queso="4")  # 70 + 88
    m.crear_servicio_pedidos().servicio.confirmar_y_pagar(p, "YAPE")
    assert p.costo_envio == Decimal("0")


def test_delivery_pagado_genera_orden_de_reparto(m, puestos):
    app = m.crear_servicio_pedidos()
    app.servicio.confirmar_y_pagar(pedido_dos_puestos(m, puestos, "DELIVERY", "Cercado"), "YAPE")
    assert app.eventos[-1] == "reparto:SC-0001:Cercado"
    assert app.eventos[-2] == "whatsapp:959000111:Pedido SC-0001 pagado: S/ 41.00"


# ---------------------------------------------------------------- rechazo de un puesto (CA-3 del Lab 05)
def test_rechazo_de_un_puesto_reembolsa_solo_su_parte(m, puestos):
    _, juan, _, _ = puestos
    yape = YapeSDK()
    app = m.crear_servicio_pedidos(yape=yape)
    p = pedido_dos_puestos(m, puestos)
    app.servicio.confirmar_y_pagar(p, "YAPE")
    assert app.servicio.rechazar_puesto(p, juan, "sin queso") == "RECHAZADO"
    assert [s.estado for s in p.subpedidos] == ["RECIBIDO", "RECHAZADO"]
    assert yape.devoluciones == [("YP-0001", Decimal("22.00"))]
    assert app.eventos[-1] == "whatsapp:959000111:Puesto P-40 sin stock; se reembolsó S/ 22.00"


def test_reembolso_por_plin_en_centimos(m, puestos):
    _, juan, _, _ = puestos
    plin = PlinClient()
    app = m.crear_servicio_pedidos(plin=plin)
    p = pedido_dos_puestos(m, puestos)
    app.servicio.confirmar_y_pagar(p, "PLIN")
    app.servicio.rechazar_puesto(p, juan, "sin queso")
    assert plin.reembolsos == [("PL-0001", 2200)]


def test_no_se_rechaza_un_subpedido_no_pagado(m, puestos):
    _, juan, _, _ = puestos
    with pytest.raises(ValueError):
        m.crear_servicio_pedidos().servicio.rechazar_puesto(pedido_dos_puestos(m, puestos), juan, "x")


def requiere_ia(m):
    if not hasattr(m, "crear_normalizador"):
        pytest.skip("La IA de la versión con patrones se refactoriza en E5")


# ---------------------------------------------------------------- IA: normalizar nombres de productos
def test_ia_normaliza_un_nombre_mal_escrito(m):
    requiere_ia(m)
    claude = ClienteClaudeSimulado("Papa amarilla")
    n = m.crear_normalizador(CATALOGO, claude=claude)
    assert n.sugerir_nombre("papa amarila", "CLAUDE") == "Papa amarilla"
    assert claude.llamadas == 1


def test_ia_no_se_llama_si_el_nombre_ya_es_exacto(m):
    requiere_ia(m)
    claude = ClienteClaudeSimulado("Rocoto")
    assert m.crear_normalizador(CATALOGO, claude=claude).sugerir_nombre("rocoto", "CLAUDE") == "Rocoto"
    assert claude.llamadas == 0


@pytest.mark.parametrize("respuesta", [
    "Papa amarilla a S/ 3.50",            # inventa un precio
    "Papa huayro",                        # producto que no está en el catálogo
    "Papa amarilla seleccionada de primera calidad, recién cosechada",  # demasiado larga
])
def test_ia_respuesta_invalida_no_se_acepta(m, respuesta):
    requiere_ia(m)
    n = m.crear_normalizador(CATALOGO, local=ModeloLocalSimulado(respuesta))
    assert n.sugerir_nombre("papa amarila", "LOCAL") is None


def test_ia_limpia_comillas_y_punto_final(m):
    requiere_ia(m)
    n = m.crear_normalizador(CATALOGO, local=ModeloLocalSimulado('"queso paria."'))
    assert n.sugerir_nombre("keso paria", "LOCAL") == "Queso paria"


def test_ia_proveedor_no_soportado(m):
    requiere_ia(m)
    with pytest.raises(ValueError):
        m.crear_normalizador(CATALOGO).sugerir_nombre("choclo tierno", "GPT")

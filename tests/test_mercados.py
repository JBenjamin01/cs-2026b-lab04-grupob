"""Iteración 1 de ADD (Lab 08, QA-07 y QA-08): reglas por mercado como datos (ADR-006)."""
from decimal import Decimal

import pytest

from arranque import crear_servicio_pedidos
from catalogo.modelos import Comerciante, Producto
from comun.excepciones import ReglaNegocioError
from mercados import ConfiguracionInvalida, RepositorioMercadosEnMemoria, cargar_datos_iniciales
from pedidos.pedido import Cliente, Pedido


def pedido(mercado, kg=Decimal("4"), precio="3.50", tipo="RECOJO_MERCADO", distrito=None):
    papa = Producto("Papa amarilla", Decimal(precio), "kg", Decimal("500"), Comerciante("Rosa", "P-12", "911000001"))
    p = Pedido(Cliente("Cliente demo", "959000111", "Calle Demo 123"), tipo, distrito, mercado=mercado)
    p.agregar_linea(papa, kg)
    return p


def test_los_tres_mercados_se_cargan_desde_datos():
    assert RepositorioMercadosEnMemoria(cargar_datos_iniciales()).codigos() == ["ALTIPLANO", "RIO_SECO", "SAN_CAMILO"]


def test_altiplano_exige_su_pedido_minimo_y_no_toca_el_pedido():
    p = pedido("ALTIPLANO", kg=Decimal("4"))            # S/ 14 < S/ 20
    with pytest.raises(ReglaNegocioError, match="pedido mínimo"):
        crear_servicio_pedidos().servicio.confirmar_y_pagar(p, "YAPE")
    assert p.estado == "CREADO"


def test_altiplano_no_acepta_plin_pero_san_camilo_si():
    with pytest.raises(ReglaNegocioError, match="no acepta"):
        crear_servicio_pedidos().servicio.confirmar_y_pagar(pedido("ALTIPLANO", kg=Decimal("10")), "PLIN")
    assert crear_servicio_pedidos().servicio.confirmar_y_pagar(pedido("SAN_CAMILO"), "PLIN") == "PAGADO"


@pytest.mark.parametrize("mercado, distrito, envio", [
    ("SAN_CAMILO", "Cercado", Decimal("5")),
    ("ALTIPLANO", "Cercado", Decimal("8")),
    ("RIO_SECO", "Cerro Colorado", Decimal("6")),
    ("RIO_SECO", "Socabaya", Decimal("15")),           # distrito no listado: tarifa por defecto del mercado
])
def test_cada_mercado_cobra_su_delivery(mercado, distrito, envio):
    p = pedido(mercado, kg=Decimal("20"), tipo="DELIVERY", distrito=distrito)    # S/ 70
    crear_servicio_pedidos().servicio.confirmar_y_pagar(p, "YAPE")
    assert p.costo_envio == envio


@pytest.mark.parametrize("mercado, comision", [("SAN_CAMILO", "3.50"), ("ALTIPLANO", "2.80"), ("RIO_SECO", "2.10")])
def test_comision_de_cada_mercado(mercado, comision):
    p = pedido(mercado, kg=Decimal("20"))                # S/ 70
    crear_servicio_pedidos().servicio.confirmar_y_pagar(p, "YAPE")
    assert p.comision == Decimal(comision)


def test_cambiar_una_regla_no_afecta_a_otros_mercados():
    """QA-08: el administrador cambia el pedido mínimo de Altiplano; San Camilo no cambia."""
    repo = RepositorioMercadosEnMemoria(cargar_datos_iniciales())
    datos = next(d for d in cargar_datos_iniciales() if d["codigo"] == "ALTIPLANO")
    repo.guardar({**datos, "pedido_minimo": "10"})
    servicio = crear_servicio_pedidos(mercados=repo).servicio
    assert servicio.confirmar_y_pagar(pedido("ALTIPLANO", kg=Decimal("4")), "YAPE") == "PAGADO"   # S/ 14 >= 10
    assert repo.obtener("SAN_CAMILO").pedido_minimo == Decimal("0")


@pytest.mark.parametrize("cambio", [
    {"comision": "1.5"},                 # 150 %: error de tipeo frecuente (15 -> 1.5)
    {"pedido_minimo": "-5"},
    {"medios_pago": []},
    {"abre": "18:00", "cierra": "06:00"},
    {"codigo": "rio seco"},
])
def test_una_configuracion_invalida_se_rechaza_antes_de_guardarse(cambio):
    repo = RepositorioMercadosEnMemoria(cargar_datos_iniciales())
    datos = next(d for d in cargar_datos_iniciales() if d["codigo"] == "RIO_SECO")
    with pytest.raises(ConfiguracionInvalida):
        repo.guardar({**datos, **cambio})
    assert repo.obtener("RIO_SECO").comision == Decimal("0.03")   # sigue la configuración anterior


def test_mercado_no_registrado():
    with pytest.raises(ReglaNegocioError, match="no registrado"):
        crear_servicio_pedidos().servicio.confirmar_y_pagar(pedido("CHARACATO"), "YAPE")

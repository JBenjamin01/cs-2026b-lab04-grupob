"""Pruebas derivadas de estados-pedidopuesto.mmd (Lab 05): una por transición + negativas.

Lab 07: la máquina ahora está implementada con el patrón State (pedidos/estados.py). Como un
subpedido ya no permite asignar el estado a mano, cada prueba llega al estado de partida
recorriendo transiciones válidas.
"""
from decimal import Decimal
from uuid import uuid4

import pytest

from catalogo.modelos import Comerciante, Producto
from comun.excepciones import EstadoInvalidoError
from pedidos.pedido import Cliente, Pedido, PedidoPuesto

CAMINOS = {
    "PENDIENTE": [],
    "RECIBIDO": ["recibir"],
    "LISTO": ["recibir", "marcar_listo"],
    "RECOGIDO": ["recibir", "marcar_listo", "recoger"],
    "ENTREGADO": ["recibir", "marcar_listo", "recoger", "marcar_entregado"],
    "RECHAZADO": ["recibir", "rechazar"],
}


def aplicar(pp, operacion):
    if operacion == "recoger":
        pp.marcar_recogido(uuid4(), "QR-1")
    elif operacion == "rechazar":
        pp.rechazar("sin stock")
    else:
        getattr(pp, operacion)()


def subpedido_en(estado):
    pp = PedidoPuesto(Comerciante("Rosa", "P-12", "900000001"))
    for operacion in CAMINOS[estado]:
        aplicar(pp, operacion)
    return pp


def test_t1_agregar_linea_crea_subpedido_pendiente():
    com = Comerciante("Rosa", "P-12", "900000001")
    prod = Producto("Papa amarilla", Decimal("3.50"), "kg", Decimal("20"), com)
    pedido = Pedido(Cliente("Cliente demo", "900000000", "Cercado"), "DELIVERY", "Cercado")
    pedido.agregar_linea(prod, Decimal("2"))
    pedido.agregar_linea(prod, Decimal("1"))  # mismo puesto: no crea otro subpedido
    assert len(pedido.subpedidos) == 1
    assert pedido.subpedidos[0].estado == "PENDIENTE"


@pytest.mark.parametrize("desde, operacion, hacia", [
    ("PENDIENTE", "recibir", "RECIBIDO"),            # T2
    ("PENDIENTE", "anular", "ANULADO"),              # T3
    ("RECIBIDO", "marcar_listo", "LISTO"),           # T4
    ("RECIBIDO", "rechazar", "RECHAZADO"),           # T5
    ("LISTO", "recoger", "RECOGIDO"),                # T6
    ("RECOGIDO", "marcar_entregado", "ENTREGADO"),   # T7
])
def test_transiciones_validas(desde, operacion, hacia):
    pp = subpedido_en(desde)
    aplicar(pp, operacion)
    assert pp.estado == hacia


@pytest.mark.parametrize("desde, operacion", [
    ("RECHAZADO", "marcar_listo"),
    ("PENDIENTE", "recoger"),
    ("ENTREGADO", "rechazar"),
    ("RECIBIDO", "anular"),
])
def test_transiciones_invalidas(desde, operacion):
    with pytest.raises(EstadoInvalidoError):
        aplicar(subpedido_en(desde), operacion)

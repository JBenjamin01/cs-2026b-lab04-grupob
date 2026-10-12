"""Pruebas derivadas de estados-pedidopuesto.mmd: una por transición (+ pruebas negativas)."""
from decimal import Decimal

import pytest

from catalogo.modelos import Comerciante, Producto
from comun.excepciones import EstadoInvalidoError
from pedidos.dominio import Cliente, EstadoPedidoPuesto as E, Pedido, PedidoPuesto, TipoEntrega
from uuid import uuid4


def nuevo_subpedido(estado: E = E.PENDIENTE) -> PedidoPuesto:
    pp = PedidoPuesto(comerciante=Comerciante("Rosa", "P-12", "900000001"))
    pp.estado = estado
    return pp


def test_t1_agregar_linea_crea_subpedido_pendiente():
    com = Comerciante("Rosa", "P-12", "900000001")
    prod = Producto("Papa amarilla", Decimal("3.50"), "kg", Decimal("20"), com)
    pedido = Pedido(Cliente("Cliente demo", "900000000", "Cercado"), TipoEntrega.DELIVERY)
    pedido.agregar_linea(prod, Decimal("2"))
    pedido.agregar_linea(prod, Decimal("1"))  # mismo puesto: no crea otro subpedido
    assert len(pedido.subpedidos) == 1
    assert pedido.subpedidos[0].estado is E.PENDIENTE


@pytest.mark.parametrize(
    "desde, operacion, hacia",
    [
        (E.PENDIENTE, lambda pp: pp.recibir(), E.RECIBIDO),            # T2
        (E.PENDIENTE, lambda pp: pp.anular(), E.ANULADO),              # T3
        (E.RECIBIDO, lambda pp: pp.marcar_listo(), E.LISTO),           # T4
        (E.RECIBIDO, lambda pp: pp.rechazar("sin stock"), E.RECHAZADO),  # T5
        (E.LISTO, lambda pp: pp.marcar_recogido(uuid4(), "QR-1"), E.RECOGIDO),  # T6
        (E.RECOGIDO, lambda pp: pp.marcar_entregado(), E.ENTREGADO),   # T7
    ],
)
def test_transiciones_validas(desde, operacion, hacia):
    pp = nuevo_subpedido(desde)
    operacion(pp)
    assert pp.estado is hacia


@pytest.mark.parametrize(
    "desde, operacion",
    [
        (E.RECHAZADO, lambda pp: pp.marcar_listo()),
        (E.PENDIENTE, lambda pp: pp.marcar_recogido(uuid4(), "QR-1")),
        (E.ENTREGADO, lambda pp: pp.rechazar("tarde")),
        (E.RECIBIDO, lambda pp: pp.anular()),
    ],
)
def test_transiciones_invalidas(desde, operacion):
    with pytest.raises(EstadoInvalidoError):
        operacion(nuevo_subpedido(desde))

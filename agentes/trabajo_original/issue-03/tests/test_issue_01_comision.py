"""Issue 01 (Lab 10): la comisión de un pedido a varios puestos se cobra una sola vez."""
from decimal import Decimal

from pedidos.liquidacion import comision_del_pedido

TASA = Decimal("0.05")


def test_un_solo_puesto_cobra_el_cinco_por_ciento():
    assert comision_del_pedido({"PUESTO_12": Decimal("40.00")}, TASA) == Decimal("2.00")


def test_issue_01_pedido_a_dos_puestos_cobra_una_sola_comision():
    subtotales = {"PUESTO_12": Decimal("40.00"), "PUESTO_07": Decimal("60.00")}
    assert comision_del_pedido(subtotales, TASA) == Decimal("5.00")

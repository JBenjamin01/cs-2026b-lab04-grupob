"""Issue 03 (Lab 10): abonos + comisión = total pagado, al céntimo."""
from decimal import Decimal

from pedidos.liquidacion import abonos_a_puestos, comision_del_pedido

TASA = Decimal("0.05")


def test_issue_03_abonos_mas_comision_suman_el_total():
    subtotales = {"PUESTO_03": Decimal("2.50"), "PUESTO_15": Decimal("12.30")}
    abonos = abonos_a_puestos(subtotales, TASA)
    assert abonos == {"PUESTO_03": Decimal("2.37"), "PUESTO_15": Decimal("11.68")}
    assert sum(abonos.values()) + comision_del_pedido(subtotales, TASA) == Decimal("14.80")

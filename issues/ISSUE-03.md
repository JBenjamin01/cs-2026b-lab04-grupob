# Issue 03: Error de redondeo en céntimos al liquidar un pedido

**Reportado por:** tesorería del Mercado Río Seco
**Observado:** un pedido de S/ 14.80 (S/ 2.50 del puesto 3 y S/ 12.30 del puesto 15) se liquidó con
S/ 14.07 en abonos y S/ 0.75 de comisión: S/ 14.82, dos céntimos más de lo que pagó el cliente.
**Esperado:** abonos + comisión = total pagado, al céntimo. Cada abono es el subtotal del puesto menos
su comisión redondeada al céntimo (mitad hacia arriba), calculado con Decimal, nunca con float.
**Prueba que reproduce el error:** `tests/test_issue_03_centimos.py::test_issue_03_abonos_mas_comision_suman_el_total`

# Issue 01: Un pedido a varios puestos cobra dos veces la comisión

**Reportado por:** comerciantes del Mercado San Camilo (puestos 12 y 07)
**Observado:** un pedido de S/ 100 (S/ 40 del puesto 12 y S/ 60 del puesto 07) con comisión del 5 %
liquidó S/ 10.00 de comisión. Con un solo puesto la comisión sale bien.
**Esperado:** la comisión es el 5 % de lo vendido por cada puesto: S/ 2.00 + S/ 3.00 = S/ 5.00.
**Prueba que reproduce el error:** `tests/test_issue_01_comision.py::test_issue_01_pedido_a_dos_puestos_cobra_una_sola_comision`

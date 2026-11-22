# Issue 02: Un producto agotado sigue visible en la vitrina

**Reportado por:** clientes del Mercado Altiplano
**Observado:** la papa amarilla del puesto 5 tiene stock 0, pero sigue en la vitrina y en la búsqueda;
el cliente la agrega al pedido y el pago falla en la reserva de stock.
**Esperado:** la vitrina y la búsqueda solo muestran productos publicados (`disponible`) **con stock mayor que 0**.
**Prueba que reproduce el error:** `tests/test_issue_02_agotados.py::test_issue_02_producto_agotado_no_aparece_en_la_vitrina`

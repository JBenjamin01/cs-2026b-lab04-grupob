# Historia de usuario crítica — San Camilo en Línea (Lab 05)

Caso 7 de la Tabla 7 de la guía. Flujo para la secuencia (E2): **pedido a varios puestos con pago único**.
Trazabilidad con el Laboratorio 04: RF-03, RF-04, RF-05, QA-03, ADR-001 y ADR-002.

## HU-03: Pedido a varios puestos con pago único

**Como** cliente del Mercado San Camilo,
**quiero** reunir en un solo pedido productos de varios puestos y pagarlo una sola vez con Yape,
**para** recibir mi compra junta sin pagar puesto por puesto ni manejar efectivo.

## Criterios de aceptación

**CA-1 — Pago aprobado (camino feliz)**
- **Dado** un pedido en estado `CREADO` con productos de dos o más puestos y stock suficiente en cada uno,
- **cuando** el cliente lo confirma y el proveedor de pagos aprueba el cobro con Yape,
- **entonces** el pedido queda `PAGADO`, cada subpedido (`PedidoPuesto`) pasa a `RECIBIDO` y se encola
  un WhatsApp para cada comerciante con el detalle de su parte, sin bloquear la respuesta al cliente (QA-03).

**CA-2 — Pago rechazado o sin respuesta**
- **Dado** un pedido en `PENDIENTE_PAGO`,
- **cuando** el proveedor rechaza el cobro o pasan 15 minutos sin respuesta,
- **entonces** el pedido queda `CANCELADO`, sus subpedidos quedan `ANULADO` y el stock reservado se libera
  en cada puesto.

**CA-3 — Un puesto se queda sin producto**
- **Dado** un subpedido en `RECIBIDO`,
- **cuando** el comerciante lo marca como rechazado por falta de producto,
- **entonces** el subpedido queda `RECHAZADO`, se reembolsa al cliente el subtotal de ese puesto y se le avisa,
  sin cancelar los subpedidos de los demás puestos.

## Supuestos y límites del alcance

- El cobro con Yape se hace mediante un proveedor de pagos (R-05). El cliente ingresa su celular y el
  código de aprobación que genera su app de Yape; ese código **no se almacena**, solo se reenvía al proveedor.
- Los nombres de los estados siguen ADR-002 (`CREADO`, `PAGADO`, …); se agregó `PENDIENTE_PAGO` como
  refinamiento del diseño detallado.
- Fuera del alcance de esta historia: publicación de productos (RF-01) y calificación de puestos.

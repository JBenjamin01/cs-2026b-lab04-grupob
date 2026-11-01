# ADR-008: Pagos resilientes con circuit breaker y outbox de pagos pendientes en PostgreSQL

- Estado: Aceptado
- Fecha: 2026-10-30
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar
- Relacionado con: ADR-001 (outbox de avisos), ADR-005 (Decorator ConReintentos), iteración 3 de ADD

## Contexto

Con 3 mercados, una caída del proveedor de pagos en la hora pico del sábado afecta a todos a la vez.
QA-09 (H,H) exige 0 pedidos perdidos ante una caída de 10 min y el cobro en ≤ 15 min. La evaluación
ATAM-lite de la iteración 1 encontró que, con el código del Lab 07, cuando `ConReintentos` agota sus 3
intentos el pago queda EXPIRADO y el pedido **se cancela** (riesgo R2).

## Alternativas consideradas

1. **Más reintentos:** bloquean al cliente y multiplican las llamadas al proveedor caído.
2. **Segundo proveedor (failover):** nuevo convenio y costo; no cabe en 1 mes.
3. **Solo outbox, sin circuit breaker:** no pierde pedidos, pero cada pedido nuevo espera 3 timeouts.
4. **Outbox en Redis:** se pierde si Redis se reinicia sin persistencia.
5. **Reintentos + circuit breaker (Decorator) + outbox en PostgreSQL:** elegida.

## Decisión

- `ConCircuitBreaker` envuelve a `ConReintentos(adaptador)` sin modificarlo (Decorator, Lab 07):
  umbral de 3 fallas, espera de 60 s y un cobro de prueba en estado semiabierto.
- `FabricaPasarelas` conserva una instancia por medio de pago, porque el circuito debe recordar las
  fallas entre un cobro y el siguiente.
- Si el cobro expira o el circuito está abierto, `ServicioPedidos` **no cancela**: deja el pedido en
  `PENDIENTE_PAGO` y guarda el cobro en la tabla `pagos.pago_pendiente`, en la misma transacción que
  el pedido.
- El worker (Celery beat, cada minuto) ejecuta `reintentar_pagos_pendientes()`: cobra los pendientes
  cuando el circuito lo permite, descarta los que el webhook ya resolvió y cancela, liberando el
  stock, los que superan la ventana de 15 min.
- Los adaptadores de pago pasan a `pagos/adaptadores.py` y solo `arranque.py` los importa (FF-02).
- Fitness functions **FF-07** (0 pedidos perdidos con una caída de 10 min) y **FF-08** (el circuito
  reduce las llamadas al proveedor caído a menos de un tercio).

## Evidencia

Monte Carlo de un sábado con 1 310 pedidos y una caída de 10 min a las 08:30:

| Táctica | Pedidos perdidos | Llamadas al proveedor caído |
|---------|------------------|-----------------------------|
| Reintentos ×3 (Lab 07) | 44 | 132 |
| Reintentos + circuit breaker + outbox | 0 | 36 |

Detalle y sensibilidad en [`add/iteracion-3.md`](../add/iteracion-3.md).

## Consecuencias

- **Positivas:** 0 pedidos perdidos ante caídas de hasta 15 min; el proveedor caído recibe 73 % menos
  llamadas; el stock no se libera mientras el cobro esté pendiente.
- **Negativas / riesgos:**
  - **Cambio de comportamiento:** antes, 3 timeouts cancelaban el pedido; ahora queda pendiente. El
    cliente ve «pago pendiente» hasta 15 min (consistencia eventual). Se actualizó la prueba de
    caracterización del Lab 07.
  - Con caídas de más de 15 min se pierden pedidos (19 con 20 min; riesgo R6, aceptado).
  - Un reintento después de un timeout ambiguo podría cobrar dos veces si el proveedor no respeta la
    clave de idempotencia (riesgo R7; se debe confirmar con el proveedor).

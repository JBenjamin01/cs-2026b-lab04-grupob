# Revisión de consistencia C1–C5 (E7)

Se aplicó el **Prompt IA 3 (auditor de consistencia)** en dos rondas. Cada hallazgo de la IA fue verificado
por el equipo contra `clases.puml`, el código de `src/` y los ADR. Regla de oro: la IA propone, el equipo
decide y verifica.

| Regla | Qué verifica |
|-------|--------------|
| C1 | Cada mensaje del diagrama de secuencia dirigido a un objeto es una operación de su clase. |
| C2 | Cada transición del diagrama de estados la provoca una operación o un evento identificable de la clase. |
| C3 | Las multiplicidades reflejan las reglas del negocio (criterios de aceptación). |
| C4 | Las dependencias entre paquetes respetan ADR-001 y no forman ciclos. |
| C5 | Los nombres son los del dominio y son iguales en diagramas, código, historia y ADR. |

## Ronda 1 — Borrador inicial (primera versión de los diagramas)

| # | Regla | Elemento (archivo) | Hallazgo de la IA | Verificación del equipo | Decisión |
|---|-------|--------------------|-------------------|-------------------------|----------|
| 1 | C1 | `buscarPorId(pedidoId)` enviado a `p : Pedido` (secuencia) | La operación pertenece a `RepositorioPedidos`, que no era línea de vida. | Correcto: un pedido no se busca a sí mismo. | Se agregó la línea de vida `RepositorioPedidos` con `buscarPorId()` y `guardar()`. |
| 2 | C1 / C3 | Flujo de pago (secuencia) | Nunca se reserva ni se libera stock, aunque CA-2 dice "el stock reservado se libera". | Correcto. | Se agregaron `loop` con `Producto.reservar()` en `confirmar()` y `liberar()` en `cancelar()`. |
| 3 | C2 | `verificarStock()`, `consolidarConOtrosPuestos()`, `finalizarAtencion()`, `notificarClienteYReembolsar()`, `crearSubpedido()` (estados) | Ninguna existe en `PedidoPuesto`. | Correcto. | Se rediseñó la máquina con las operaciones reales: `recibir()`, `marcarListo()`, `rechazar()`, `marcarRecogido()`, `marcarEntregado()`, `anular()`. |
| 4 | C2 | Subestados `StockConfirmado` y `SinStock` dentro de `Recibido` | Estados sin salida dentro del estado compuesto. | Correcto (incumple la lista de verificación de E3). | Se eliminaron; la decisión de stock queda en la guarda `[sin stock físico]`. |
| 5 | C4 | `NotificadorMensajeria.notificarComerciante(subpedido: PedidoPuesto, …)` | El puerto de `notificaciones` usa una clase de `pedidos`: ciclo `pedidos ↔ notificaciones`. | Correcto. | Firmas con tipos neutrales (ADR-004). |
| 6 | C4 | Asociación `Pedido — Repartidor` sin dirección | Si `Pedido` navega a `Repartidor`, hay ciclo `pedidos ↔ reparto`. | Correcto: `reparto` ya depende de `pedidos`. | Navegación solo `Repartidor --> Pedido` (ADR-004). |
| 7 | C4 | Paquete "Módulo Usuarios" con `Cliente` | No existe ese módulo en ADR-001. | Correcto. | `Cliente` pasa al paquete `pedidos`. |
| 8 | C5 | `EstadoPedido.BORRADOR`, `EstadoPago.APROBADO` | ADR-002 usa `creado` y `confirmado`. | Correcto. | Se alinearon los nombres con ADR-002 en diagramas, historia y código. |
| 9 | C1 | `->> notificarComerciante` (secuencia) | "El mensaje asíncrono no tiene respuesta síncrona: debería ser una llamada bloqueante dentro del controlador". | **Falso positivo.** C1 solo exige que el mensaje sea una operación de la clase, y lo es. Volverlo síncrono violaría QA-03 y ADR-001 (outbox + Celery). | Se rechaza. |

## Ronda 2 — Diagramas finales

| # | Regla | Elemento (archivo) | Hallazgo de la IA | Verificación del equipo | Decisión |
|---|-------|--------------------|-------------------|-------------------------|----------|
| 10 | C1 | `P -> PR : reservar(cantidad)` (secuencia, mensaje 7) | "`Pedido` invoca `reservar()` en `Producto`, pero no existe asociación `Pedido–Producto`." | **Falso positivo.** `Pedido` llega a `Producto` navegando `Pedido *-- PedidoPuesto *-- LineaPedido --> Producto`; la operación sí existe en `Producto`. | Se rechaza. |
| 11 | C2 | `[*] --> PENDIENTE : Pedido.agregarLinea()` (estados) | "La transición inicial no es una operación de `PedidoPuesto`." | **Falso positivo.** C2 admite "una operación o un evento identificable": por la composición, el subpedido nace cuando `Pedido.agregarLinea()` agrega el primer producto de un puesto (así está en el código). | Se rechaza; se aclara en el diagrama. |
| 12 | C4 | `Repartidor --> Pedido` y `Repartidor.tomarPedido(pedido: Pedido)` | "Posible ciclo `reparto ↔ pedidos`." | **Falso positivo.** La dependencia va solo de `reparto` a `pedidos`; `pedidos` no importa nada de `reparto` (confirmado con pyreverse en `img/packages_sancamilo.png`). | Se rechaza. |
| 13 | C1 | Nota del webhook (secuencia) | "La nota dice que el webhook ejecuta la misma rama del `alt`, pero `ServicioPedidos` no tiene operación para recibirlo." | Correcto (aunque una nota no es un mensaje, el flujo debía existir). | Se agregó `procesarWebhookPago(pedidoId, pago)` al diagrama de clases y al código, con prueba de idempotencia. |
| 14 | C3 | `Pedido "1" *-- "1..*" PedidoPuesto` | "¿Un pedido puede tener 0 subpedidos mientras está en `CREADO`?" | Correcto en parte: un carrito vacío es posible, pero no se puede confirmar. | Se mantiene `1..*` para pedidos confirmados y `confirmar()` lo valida. |
| 15 | C5 | `codigoAprobacion` (secuencia y `PasarelaPago`) | "Podría confundirse con un dato sensible almacenado." | Correcto como advertencia: no se guarda, solo se reenvía al proveedor. | Se documenta en la historia y en el diagrama de clases (comentario). |
| 16 | C4 | `from catalogo.modelos import Producto` en `src/pedidos/dominio.py` (primer esqueleto) | "ADR-001 prohíbe importar los modelos de otro módulo." | Correcto. | Cada módulo expone su interfaz pública en `__init__.py`; `pedidos` importa `from catalogo import Producto`. En Django, `LineaPedido` guardará `producto_id` y una copia del precio. |

## Resultado

- C1, C2, C3, C4 y C5 se cumplen en la versión final.
- **4 falsos positivos** identificados y explicados (hallazgos 9, 10, 11 y 12).
- Si se hubiera aceptado el hallazgo 9 sin verificar, la confirmación del pago quedaría bloqueada por las
  demoras o caídas de WhatsApp, y un pedido ya cobrado podría quedar en error.

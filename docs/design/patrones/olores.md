# Olores de código de la versión antes (E1)

Flujo crítico: **confirmar y pagar un pedido multipuesto** (HU-03, secuencia del Lab 05), más el rechazo
de un puesto (CA-3) y la función de IA del caso 7 (normalizar nombres de productos, Tabla 7 de la guía).
Código analizado: `src/pedidos/antes/servicio.py`.

## 1. Red de seguridad

`tests/test_comportamiento.py`: **22 pruebas de caracterización** (26 casos al parametrizar las zonas y
las respuestas de la IA) sobre lo que el flujo hace hoy: pagos aprobados y rechazados con Yape y Plin,
reintentos ante timeouts, transiciones inválidas, stock, tarifas de delivery, reembolso de un puesto y
guardrails de la IA. Ninguna prueba llama a servicios reales: los SDK y los LLM están simulados en
`src/pedidos/externos.py`.

```text
$ python -m pytest -q tests/test_comportamiento.py      # solo la versión antes
25 passed, 1 xfailed
```

La prueba `test_medio_no_soportado_no_altera_el_pedido` queda como **xfail** en la versión antes: al
escribirla se descubrió que, con un medio de pago desconocido, el pedido queda en `PENDIENTE_PAGO` y con
el stock reservado, porque el medio se valida **después** de reservar el stock y cambiar el estado.

## 2. Métricas antes del refactor

```text
$ radon cc -s -a src/pedidos/antes/servicio.py
src/pedidos/antes/servicio.py
    M 70:4 ServicioPedidos.confirmar_y_pagar - D (29)
    C 61:0 ServicioPedidos - C (15)
    M 173:4 ServicioPedidos.sugerir_nombre - C (11)
    M 147:4 ServicioPedidos.rechazar_puesto - B (9)
    M 62:4 ServicioPedidos.__init__ - B (6)
    C 38:0 Pedido - A (4)
    M 51:4 Pedido.agregar_linea - A (4)
    ...
14 blocks (classes, functions, methods) analyzed.
Average complexity: B (6.071428571428571)

$ radon raw -s src/pedidos/antes/servicio.py   ->  SLOC: 182
$ radon mi -s src/pedidos/antes/servicio.py    ->  A (30.85)
```

`confirmar_y_pagar()` tiene complejidad **29 (D)**: casi el triple del umbral recomendado (10).

## 3. Olores detectados (Prompt IA 1) y decisión del equipo

| # | Líneas | Olor | Patrón propuesto | Principio SOLID | Costo de aplicarlo | Decisión |
|---|--------|------|------------------|-----------------|--------------------|----------|
| 1 | 107–129 | `if/elif` por medio de pago que crece con cada medio nuevo (R-05 ya anuncia Plin) | Strategy + Factory (registro) | O (abierto/cerrado) | Una interfaz, una fábrica | **Aceptado** (E2) |
| 2 | 109, 118, 164–167 | El servicio conoce los detalles de cada SDK: soles frente a céntimos, diccionario frente a tupla, `devolver` frente a `refund` | Adapter | D (inversión de dependencias), I | Un adaptador por SDK | **Aceptado** (E2) |
| 3 | 71–76, 154–158 | Condicionales anidados sobre `pedido.estado` y `sub.estado`; la máquina de estados del Lab 05 está dispersa en `if` | State | S, O, L | 14 clases pequeñas | **Aceptado** (E3) |
| 4 | 108–125 | Bucle de reintentos duplicado para Yape y Plin | Decorator | S, O | Una clase envoltorio | **Aceptado** (E4) |
| 5 | 131–138, 168–170 | El servicio arma a mano los WhatsApp de cada puesto, del cliente y la orden de reparto | Observer | S, O | Publicador + 3 suscriptores | **Aceptado** (E4) |
| 6 | 85–89 | El total del pedido multipuesto se calcula con bucles anidados sobre subpedidos y líneas | Composite | O | Una interfaz `ItemPedido` | **Aceptado** (E4; patrón sugerido para el caso 7) |
| 7 | 95–104 | `if/elif` de tarifas de delivery por zona dentro del método de pago | Strategy | S, O | Una interfaz y 2 tarifas | **Aceptado** (E4; patrón sugerido para el caso 7) |
| 8 | 179–197 | `if/elif` por proveedor de LLM y validaciones de la respuesta mezcladas con la llamada | Strategy + Adapter + Decorator (caché) + Chain of Responsibility | S, O, D | 4 adaptadores/eslabones | **Aceptado** (E5) |
| 9 | 61–197 | Clase dios: `ServicioPedidos` cobra, calcula envíos, avisa, reembolsa y llama a la IA | (se resuelve con 1–8) | S | — | **Aceptado**: la IA pasa a `catalogo/ia.py` |
| 10 | — | «`FabricaPasarelas` y `PublicadorEventos` deberían ser Singleton» | Singleton | — | Estado global | **Rechazado**: impide inyectar SDK simulados en las pruebas; se crean en `arranque.py` |
| 11 | — | «Usar Abstract Factory para crear familias (pasarela + reembolso + notificación) por proveedor» | Abstract Factory | — | Jerarquía de fábricas | **Rechazado**: no hay familias de productos; cobrar y reembolsar ya están en la misma interfaz |
| 12 | — | «Construir el `Pedido` con un Builder» | Builder | — | Una clase más | **Rechazado**: `agregar_linea()` ya construye el pedido paso a paso y valida el estado |
| 13 | — | «Encapsular cada cobro como Command para reintentarlo desde una cola» | Command | — | Cola y serialización | **Rechazado para el MVP**: los reintentos son síncronos y cortos; la cola ya existe para notificaciones (ADR-001) |
| 14 | — | «Validar la respuesta de la IA con otro LLM como juez» | (otro LLM) | — | Costo y latencia por cada nombre | **Rechazado**: reglas deterministas bastan para un nombre de producto |

Resumen: 9 olores aceptados y 5 propuestas rechazadas. El olor 9 no es un patrón aparte: desaparece
cuando se aplican los demás.

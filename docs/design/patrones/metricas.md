# Métricas antes y después del refactor (E6)

Herramienta: **radon 6.0.1**. «Antes» es `src/pedidos/antes/servicio.py`; «después» son los 13 archivos que
reemplazan su funcionalidad: `pedidos/{pedido, estados, tarifas, servicio, puertos}.py`,
`pagos/{modelos, pasarelas}.py`, `comun/eventos.py`, `notificaciones/{puertos, suscriptores}.py`,
`reparto/suscriptores.py`, `catalogo/ia.py` y `arranque.py`.

```bash
radon cc -s -a src/pedidos/antes/servicio.py
radon cc -s -a src/pedidos/pedido.py src/pedidos/estados.py ... src/arranque.py
radon cc --min B <archivos después>      # no imprime nada: ningún bloque supera A (5)
radon raw -s <archivos>                    # SLOC
```

## 1. Complejidad ciclomática

| Método | Antes | Después |
|--------|-------|---------|
| `confirmar_y_pagar()` | **29 (D)** | **2 (A)** |
| `rechazar_puesto()` | 9 (B) | 1 (A) |
| `sugerir_nombre()` | 11 (C) | 4 (A) |
| Clase `ServicioPedidos` | 15 (C) | 2 (A) |
| Bloque más complejo de todo el código | 29 (D) | 5 (A): `Creado.confirmar()` y `SinPreciosNiCantidades` |
| **Promedio** | **6,07 (B)** | **1,63 (A)** |
| Índice de mantenibilidad (radon mi) | 30,85 | 49,47 a 100 por archivo |

## 2. El costo del patrón (trade-off)

| Medida | Antes | Después |
|--------|-------|---------|
| Líneas de código (SLOC) | 182 | 596 |
| Archivos | 1 | 13 |
| Clases | 6 | 55 |
| Métodos a modificar para un medio de pago nuevo | 2 (`confirmar_y_pagar`, `rechazar_puesto`) | 0 (se registra en `arranque.py`) |
| Métodos a modificar para un proveedor de IA nuevo | 1 (`sugerir_nombre`) | 0 (un adaptador nuevo) |
| Métodos a modificar para un interesado nuevo en el pago | 1 (`confirmar_y_pagar`) | 0 (se suscribe) |
| Pruebas | 26 casos de caracterización | 26 casos × 2 versiones + 19 de patrones + 11 de la máquina de estados |

De las 596 líneas, unas 75 cubren funciones que la versión antes no tenía: el ciclo completo del
pedido hasta ENTREGADO (Lab 05), el webhook idempotente, la cancelación por tiempo agotado, el
repositorio y los adaptadores en memoria. Aun descontándolas, el código casi se triplica.

## 3. Lectura del trade-off

El método principal pasó de complejidad 29 a 2 y el promedio de 6,07 a 1,63; ningún método supera
5, y agregar un medio de pago, una tarifa, un proveedor de IA o un interesado en el pago ya no exige
modificar el servicio. A cambio, el código pasó de 182 a 596 líneas y de 1 a 13 archivos, y un
developer nuevo debe conocer siete patrones para seguir el flujo. Para San Camilo en Línea el cambio
se justifica porque las variaciones **ya están anunciadas**: Plin (R-05), más zonas de delivery y un
proveedor de IA que puede cambiar. Si el MVP solo cobrara con Yape, sin delivery y sin IA, la versión
antes (con pruebas) habría sido suficiente y más fácil de leer.

El refactor además corrigió dos errores reales que la versión antes conserva:

1. **Medio de pago no soportado:** el pedido quedaba en `PENDIENTE_PAGO` con el stock reservado. Con la
   Factory, el medio se valida antes de tocar el pedido (`test_medio_no_soportado_no_altera_el_pedido`).
2. **Montos con fracción de céntimo:** 0,75 kg × S/ 3,50 = S/ 2,625. La versión antes enviaba
   S/ 2,625 a Yape y 262 céntimos a Plin, es decir, montos distintos para el mismo pedido. Ahora
   `Pedido.total()` redondea al céntimo (`test_los_montos_se_redondean_al_centimo`).

## 4. Patrones que se decidió NO aplicar

| Patrón | Por qué no |
|--------|-----------|
| Singleton (fábrica, publicador) | Estado global: las pruebas no podrían inyectar SDK ni suscriptores simulados. Se crean una vez en `arranque.py` y se inyectan. |
| Abstract Factory | No hay familias de productos relacionados; cobrar y reembolsar ya comparten la interfaz `PasarelaPago`. |
| Builder para `Pedido` | `agregar_linea()` ya construye el pedido paso a paso y el estado `Creado` valida cada paso. |
| Command para los cobros | Los reintentos son síncronos y cortos; una cola de comandos solo se justificaría con pagos diferidos. |
| Template Method para los reintentos | Obligaría a heredar de una clase base; el Decorator los agrega por composición y sirve para cualquier pasarela. |
| Un LLM «juez» para validar la IA | Duplica costo y latencia por cada nombre; reglas deterministas bastan. |

## 5. Verificación del diagrama con pyreverse (E7)

```bash
cd src
pyreverse -o puml -p pedidos --ignore=antes,externos.py pedidos
pyreverse -o puml -p sancamilo --ignore=antes,externos.py comun catalogo pagos notificaciones pedidos reparto arranque
```

| Diferencia entre `clases.puml` y el código | Causa | Acción |
|--------------------------------------------|-------|--------|
| El diagrama de paquetes mostraba `pedidos.pedido → catalogo.modelos` y `pedidos.servicio → pagos.pasarelas`. | Al reescribir el código se importaron módulos internos de otros paquetes, lo que ADR-001 prohíbe. | **Corregir el código:** se importa la interfaz pública de cada paquete (`from pagos import ...`). |
| Las composiciones `Pedido *-- PedidoPuesto` y `PedidoPuesto *-- LineaPedido` aparecen como asociaciones (`subpedidos`, `lineas`). | pyreverse no deduce composición desde una lista. | Limitación conocida (Lab 05); el diseño se mantiene. |
| No aparece la asociación del contexto con su estado (`_estado`). | pyreverse oculta los atributos privados por defecto. | Documentar; con `-f ALL` aparece. |
| Los 14 estados concretos aparecen como subclases. | Es la estructura real del patrón State. | `clases.puml` muestra solo las clases abstractas y remite a `patrones/state.puml`. |

Resultado: no hay ciclos, y `pedidos` ya no depende de `notificaciones` ni de `reparto`. Desde el
Observer, esos módulos escuchan eventos y se conectan en `arranque.py`.

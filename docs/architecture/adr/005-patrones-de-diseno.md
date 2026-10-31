# ADR-005: Patrones de diseño en el flujo «confirmar y pagar» y en la IA del catálogo

- Estado: Aceptado
- Fecha: 2026-10-25
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar
- Relacionado con: ADR-001 (monolito modular), ADR-002 (estados), ADR-004 (puertos sin ciclos), Lab 07

## Contexto

La primera versión del flujo crítico (`src/pedidos/antes/servicio.py`) concentraba en un solo método
(`confirmar_y_pagar()`, complejidad ciclomática **29**) el cobro con Yape y Plin, los reintentos, el
cálculo del delivery, los cambios de estado y los avisos. Cada medio de pago (R-05 ya anuncia Plin),
cada zona de delivery o cada proveedor de IA obligaba a modificar ese método. Además:

- un medio de pago desconocido dejaba el pedido en `PENDIENTE_PAGO` con el stock reservado;
- con kilos fraccionados, Yape y Plin recibían montos distintos para el mismo pedido (S/ 2,625 frente
  a 262 céntimos);
- la respuesta del LLM que normaliza nombres de productos no es confiable: puede inventar precios o
  productos que no existen en el catálogo.

## Alternativas consideradas

1. **Mantener la versión antes con pruebas.** Es la más simple (182 SLOC) y sería suficiente con un
   solo medio de pago, sin delivery y sin IA, pero no con los cambios ya previstos.
2. **Tabla de transiciones para los estados** (como en el código del Lab 05). Válida, pero los estados
   tienen comportamiento propio (reservar y liberar stock, anular subpedidos, reembolsar).
3. **Patrones GoF guiados por los olores** (`docs/design/patrones/olores.md`). Elegida.

## Decisión

Aplicaremos solo los patrones que eliminan un olor concreto, cada uno con una prueba que lo demuestra:

| Patrón | Dónde | Olor que elimina |
|--------|-------|------------------|
| Strategy + Adapter + Factory (registro) | `pagos/pasarelas.py` | `if/elif` por medio de pago y detalles de cada SDK en el servicio |
| Decorator | `ConReintentos` (pagos), `ConCache` (IA) | Reintentos duplicados; llamadas repetidas al LLM |
| State | `pedidos/estados.py` | Condicionales sobre el estado del pedido y del subpedido (máquina del Lab 05) |
| Composite | `pedidos/pedido.py` | Bucles anidados para totalizar un pedido de varios puestos |
| Strategy | `pedidos/tarifas.py` | `if/elif` de tarifas de delivery por zona |
| Observer | `comun/eventos.py` + suscriptores | Avisos a comerciantes, cliente y reparto armados a mano |
| Chain of Responsibility | `catalogo/ia.py` | Validaciones de la salida del LLM mezcladas con la llamada |

Además:
- Las clases concretas se conectan en `src/arranque.py` (raíz de composición). `pedidos` publica eventos
  con datos neutrales y ya no depende de `notificaciones` ni de `reparto` (refuerza ADR-004).
- Los montos se redondean al céntimo en `Pedido.total()`.
- Se rechazan **Singleton** (estado global que impide inyectar dobles de prueba), **Abstract Factory**
  (no hay familias de productos), **Builder**, **Command** y un **LLM juez** (ver `olores.md` y
  `metricas.md`).

## Consecuencias

- **Positivas:**
  - `confirmar_y_pagar()` baja de complejidad 29 (D) a 2 (A); el promedio, de 6,07 a 1,63, y ningún
    bloque supera 5.
  - Un medio de pago, una tarifa, un proveedor de IA o un interesado en el pago nuevos no requieren
    modificar el servicio.
  - La IA se prueba sin clave de API ni red, con LLM simulados, y su salida se valida antes de mostrarse.
  - Se corrigen los dos errores de la versión antes, cubiertos por pruebas.
- **Negativas / riesgos:**
  - El código pasa de 182 a 596 líneas y de 1 a 13 archivos; hay más indirección y el equipo debe
    conocer los patrones para seguir el flujo.
  - Los 14 estados concretos son clases pequeñas que se deben mantener sincronizadas con
    `estados-pedidopuesto.mmd`; las pruebas de la máquina del Lab 05 son la red de seguridad.
  - La versión antes se conserva solo para comparar; no debe usarse en producción.

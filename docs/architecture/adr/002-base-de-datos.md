# ADR-002: Usar PostgreSQL con un esquema por módulo

- Estado: Aceptado
- Fecha: 2026-10-04
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar

## Contexto

Un pedido multipuesto (RF-03) genera un subpedido por puesto y un único cobro (RF-04). No se
puede cobrar un pedido que no quedó registrado, ni registrar un pago dos veces si el proveedor
reenvía su confirmación. Por eso se necesitan transacciones ACID.

El sistema corre en un solo VPS (R-03) y el equipo usa el ORM de Django (R-02). La arquitectura
es un monolito modular cuyos módulos deben ser dueños de sus datos. Para cumplir QA-03, la
notificación pendiente debe guardarse en la misma transacción que confirma el pago. Se
almacenan datos personales de clientes y comerciantes (nombre, teléfono, dirección), protegidos
por la Ley N.º 29733 (R-04). El catálogo se lee intensamente en hora pico (QA-04).

## Alternativas consideradas

1. **PostgreSQL con un esquema por módulo:** una sola instancia, transacciones ACID entre
   módulos y límites visibles en la base de datos.
2. **MongoDB (documental):** catálogo flexible, pero las transacciones entre colecciones son
   más complejas y el soporte en el ORM de Django es limitado.
3. **Una base de datos PostgreSQL independiente por módulo:** aislamiento máximo, pero 5
   instancias consumen la RAM del VPS, complican los respaldos e impiden guardar el pago y su
   notificación en una sola transacción.

## Decisión

Usaremos una instancia de PostgreSQL en el mismo VPS, con una base `sancamilo` y un esquema por
módulo: `catalogo`, `pedidos`, `pagos`, `notificaciones` y `reparto`.

1. **Sin claves foráneas entre esquemas:** los módulos se referencian por ID y la consistencia
   entre módulos se mantiene mediante sus interfaces públicas.
2. **Estados separados:**
   - El pedido usa `estado_pedido`: `creado → pagado → preparado → en_camino → entregado`
     o `cancelado`.
   - El pago usa `estado_pago`: `pendiente → confirmado` o `rechazado`.
   - El pedido solo pasa a `pagado` cuando el pago está `confirmado`.
3. **Pagos idempotentes:** el identificador de transacción del proveedor tiene una restricción
   `UNIQUE`; si el webhook llega dos veces, el segundo se ignora.
4. **Transacción pago + notificación:** la confirmación del pago y el registro de la
   notificación pendiente se guardan en una sola transacción (esquemas `pagos` y
   `notificaciones` de la misma base).
5. **Respaldos:** `pg_dump` diario programado con cron, copiado fuera del VPS. Antes del
   lanzamiento y luego una vez al mes se prueba una restauración completa en un entorno local.
6. **Datos personales:** se guardan solo los necesarios para la entrega (nombre, teléfono,
   dirección), y solo los leen los módulos `pedidos`, `notificaciones` y `reparto` (R-04).

## Consecuencias

- **Positivas:**
  - Consistencia transaccional para pedidos, pagos y notificaciones.
  - Un solo motor que operar y respaldar.
  - Integración natural con Django.
  - Si en el futuro se extrae un módulo, su esquema se mueve completo.
- **Negativas / riesgos:**
  - Django no soporta esquemas de PostgreSQL de forma nativa. Se nombrarán las tablas con su
    esquema (`db_table = 'catalogo"."producto'`) y se creará cada esquema con una migración
    inicial (`CREATE SCHEMA`). Si esto complica las migraciones, se usarán prefijos de tabla
    por módulo.
  - Sin claves foráneas entre esquemas, la integridad referencial entre módulos depende del
    código.
  - La base de datos comparte CPU y RAM con la aplicación en el mismo VPS.
  - Un respaldo diario implica que, ante una pérdida total del disco, se podría perder hasta
    un día de datos.
# ADR-001: Adoptar un monolito modular en Django para el MVP de San Camilo en Línea

- Estado: Aceptado
- Fecha: 2026-10-04
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar

## Contexto

El MVP debe estar en producción en 1 mes (R-01). El equipo son 2 developers que dominan
Python/Django y no tienen experiencia en DevOps (R-02), y se dispone de un único VPS de bajo
costo (R-03).

El pedido multipuesto (RF-03) involucra catálogo, pedidos, pagos y notificaciones. La
confirmación por WhatsApp al comerciante (RF-05) no debe hacer perder pedidos si el servicio
externo falla: 0 pedidos perdidos y reintentos cada ≤ 5 min (QA-03). Además, ya se prevé
agregar Plin u otra pasarela (R-05). La carga esperada es moderada: 200 clientes concurrentes
en hora pico (QA-04).

## Alternativas consideradas

**Estilo arquitectónico** (puntajes de la matriz ponderada):

1. **Monolito en capas (4,00):** el más rápido de construir, pero comparte servicios y modelos
   entre todas las funcionalidades; agregar una pasarela o cambiar el pedido multipuesto toca
   código común.
2. **Microservicios (2,60):** escalabilidad y despliegue independientes, pero requiere API
   Gateway, broker, 5 despliegues y monitoreo distribuido; excede R-01, R-02 y R-03.
3. **Monolito modular (4,10):** elegido.

**Envío de notificaciones** (decisión complementaria dentro del monolito):

1. **Llamada síncrona dentro de la petición:** si WhatsApp tarda o falla, la petición del
   cliente se bloquea o falla.
2. **Hilos en memoria (`ThreadPoolExecutor`):** si el proceso se reinicia, las notificaciones
   pendientes se pierden; incumple QA-03.
3. **Cola sobre la base de datos (Django-Q2):** un servicio menos, pero no aprovecha Redis,
   que igual se necesita como caché del catálogo (QA-04).
4. **Registro pendiente en PostgreSQL + Celery/Redis como ejecutor:** elegido.

## Decisión

Usaremos un monolito modular en Django con 5 módulos (apps): `catalogo`, `pedidos`, `pagos`,
`notificaciones` y `reparto`.

1. **Límites entre módulos:** cada módulo expone una interfaz pública (`services.py`) y ningún
   módulo importa los modelos de otro. Las reglas se verifican con import-linter en la CI
   (GitHub Actions).
2. **Datos:** cada módulo tiene su propio esquema en PostgreSQL (ver ADR-002).
3. **Integraciones externas:** se implementan como puertos (`PasarelaPago`, `Mensajeria`) con
   adaptadores (Yape mediante un proveedor de pagos; WhatsApp Business Platform).
4. **Notificaciones (patrón outbox):**
   - Al confirmarse un pago, en la misma transacción se crea un registro de notificación con
     estado `pendiente`.
   - Celery lo envía con reintentos y espera creciente entre intentos.
   - Una tarea periódica (Celery beat) vuelve a encolar cada 5 minutos las notificaciones que
     sigan pendientes. Así, aunque Redis pierda un mensaje, la notificación no se pierde.
5. **Idempotencia:** las operaciones críticas (publicar producto, confirmar pedido, webhook de
   pago) aceptan una clave única generada por el cliente o el proveedor, y el servidor ignora
   las repeticiones.
6. **Operación mínima:**
   - Gunicorn y Celery corren como servicios systemd con reinicio automático.
   - Los logs rotan con logrotate.
   - Un monitoreo básico alerta si la aplicación deja de responder.

## Consecuencias

- **Positivas:**
  - Un solo despliegue en un VPS, con costo mínimo, en la tecnología que el equipo domina.
  - Agregar Plin solo requiere un nuevo adaptador de `PasarelaPago`, sin tocar los demás
    módulos.
  - Una falla de WhatsApp no impide registrar ni pagar pedidos, y ninguna notificación se
    pierde.
  - Los reintentos de red 3G no generan productos ni pedidos duplicados.
  - Los módulos pueden extraerse como servicios en el futuro si la carga lo exige.
- **Negativas / riesgos:**
  - El equipo debe respetar los límites entre módulos; sin import-linter, el sistema degenera
    en un "monolito de barro".
  - Celery y Redis son dos procesos más que el equipo debe aprender a operar.
  - Una falla grave (p. ej., memoria agotada) afecta a todo el sistema; se mitiga con el
    reinicio automático y el monitoreo, pero sigue siendo un punto único de falla.
  - Solo se puede escalar verticalmente.
  - La ventaja sobre el monolito en capas es estrecha (0,10) y depende del peso dado a la
    modificabilidad.
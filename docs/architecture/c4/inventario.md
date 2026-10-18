# Inventario del modelo C4 — San Camilo en Línea (E1)

Todo lo que aparece en `workspace.dsl` sale de lo ya construido en los Laboratorios 04 y 05.
Si algún nombre cambia, se corrige primero aquí y en el DSL (regla C5: los mismos nombres en
todos los artefactos).

| Elemento | Tipo C4 | Origen |
|----------|---------|--------|
| Cliente | Persona | `docs/architecture/drivers.md` (actores del caso, RF-02 a RF-04, RF-08) |
| Comerciante | Persona | `docs/architecture/drivers.md` (RF-01, RF-05, RF-06) |
| Repartidor | Persona | `docs/architecture/drivers.md` (RF-07) |
| San Camilo en Línea | Sistema de software | Caso 7 de la guía; `docs/architecture/drivers.md` |
| Proveedor de pagos (cobro con Yape) | Sistema externo | `drivers.md` (RF-04, R-05); ADR-001 (puerto `PasarelaPago`) |
| WhatsApp Business Platform | Sistema externo | `drivers.md` (RF-05, R-05); ADR-001 (puerto de mensajería) |
| PWA offline-first | Contenedor | ADR-003; `despliegue.py` |
| API San Camilo (Django + Gunicorn) | Contenedor | ADR-001; `despliegue.py` |
| Worker de notificaciones (Celery) | Contenedor | ADR-001; `despliegue.py` |
| Planificador (Celery beat) | Contenedor | ADR-001 (reencola cada 5 min); `despliegue.py`; Lab 05 (`cancelarPorTiempoAgotado()` a los 15 min) |
| Cola y caché (Redis) | Contenedor | ADR-001; `despliegue.py` |
| Base de datos (PostgreSQL, un esquema por módulo) | Contenedor | ADR-002; `despliegue.py` |
| Módulo Catálogo | Componente (de la API) | `docs/design/paquetes.puml` (paquete `catalogo`) |
| Módulo Pedidos | Componente (de la API) | `docs/design/paquetes.puml` (paquete `pedidos`) |
| Módulo Pagos | Componente (de la API) | `docs/design/paquetes.puml` (paquete `pagos`) |
| Módulo Notificaciones | Componente (de la API) | `docs/design/paquetes.puml` (paquete `notificaciones`) |
| Módulo Reparto | Componente (de la API) | `docs/design/paquetes.puml` (paquete `reparto`) |
| Flujo «confirmar y pagar» | Vista dinámica | `docs/design/secuencia-confirmar-pagar.puml` |
| Celular Android de gama baja, VPS único, Nginx, monitoreo, respaldo externo | Nodos de despliegue / infraestructura | `despliegue.py`; ADR-001 (systemd); ADR-002 (respaldo fuera del VPS); R-03 y R-06 |

## Decisiones de modelado

- **`comun` no es un componente.** El paquete `comun` solo contiene tipos base y excepciones; se
  omite para que el diagrama muestre responsabilidades de negocio y no una flecha de cada módulo
  hacia una biblioteca compartida.
- **Plin no se modela.** Es una extensión futura (R-05): se agregaría un adaptador más del puerto
  `PasarelaPago` sin cambiar la estructura de contenedores.
- **Nginx, monitoreo y respaldo** no son contenedores de la aplicación: son infraestructura y
  aparecen solo en la vista de despliegue.
- **Celery beat es un contenedor aparte** porque se ejecuta como servicio independiente
  (`despliegue.py`) y es quien dispara los reintentos y la cancelación por tiempo agotado.
- **El webhook del proveedor de pagos entra por `Pedidos`**, que es donde Lab 05 definió
  `procesarWebhookPago()`.
- **Los contenedores C4 no son contenedores Docker.** El MVP se despliega con systemd en un VPS
  (ADR-001), no con Docker.

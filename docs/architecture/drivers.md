# Drivers arquitectónicos — San Camilo en Línea

> Caso 7 · Pedidos a los puestos del Mercado San Camilo (Arequipa), con recojo o delivery.
> Actores: Cliente, Comerciante, Repartidor.

## 1. Requisitos funcionales clave

| ID    | Requisito                                                                                              | Actor        | Prioridad |
|-------|--------------------------------------------------------------------------------------------------------|--------------|-----------|
| RF-01 | El comerciante publica un producto (foto, nombre, precio y unidad de venta) en el catálogo de su puesto | Comerciante  | Alta      |
| RF-02 | El cliente navega el catálogo por puesto y por categoría (frutas, carnes, abarrotes, etc.)             | Cliente      | Alta      |
| RF-03 | El cliente arma un único pedido con productos de varios puestos y elige recojo o delivery              | Cliente      | Alta      |
| RF-04 | El cliente paga el pedido con Yape a través de un proveedor de pagos autorizado                        | Cliente      | Alta      |
| RF-05 | El sistema envía por WhatsApp al comerciante la confirmación con el detalle de su parte del pedido     | Comerciante  | Alta      |
| RF-06 | El comerciante marca un producto como agotado o disponible                                             | Comerciante  | Media     |
| RF-07 | El repartidor recibe la asignación del pedido, la lista de puestos a recorrer y marca la entrega       | Repartidor   | Media     |
| RF-08 | El cliente consulta el estado de su pedido (pagado, preparado, en camino, entregado)                   | Cliente      | Media     |

## 2. Atributos de calidad (ordenados por prioridad)

1. **Capacidad de interacción (usabilidad)**: es el atributo crítico del caso. Si un comerciante
   con poca experiencia digital no logra publicar sus productos en ≤ 3 toques, el catálogo queda
   vacío y la plataforma no tiene valor para nadie.
2. **Fiabilidad (tolerancia a fallos de red)**: los comerciantes trabajan dentro del mercado con
   señal 3G intermitente, así que lo que registran no puede perderse cuando se cae la conexión.
3. **Disponibilidad ante fallas de servicios externos**: WhatsApp y el proveedor de pagos son
   externos. Si alguno falla, el pedido igual debe quedar registrado y no perderse.
4. **Eficiencia de desempeño**: el catálogo debe cargar aceptablemente en celulares de gama baja
   con 3G, sobre todo en la hora pico de compras (sábado y domingo por la mañana).
5. **Mantenibilidad (modificabilidad)**: más adelante se agregarán Plin u otras pasarelas, así que
   el módulo de pagos debe poder extenderse sin tocar el resto del sistema.

## 3. Restricciones

| ID   | Tipo         | Restricción                                                                                                      |
|------|--------------|------------------------------------------------------------------------------------------------------------------|
| R-01 | Plazo        | MVP en producción en 1 mes                                                                                       |
| R-02 | Equipo       | 2 developers con experiencia en Python/Django; sin experiencia en DevOps ni en orquestación de contenedores      |
| R-03 | Presupuesto  | Un solo servidor VPS de bajo costo (p. ej., 2 vCPU / 4 GB RAM); todo servicio de pago adicional debe justificarse |
| R-04 | Normativa    | Ley N.º 29733, de Protección de Datos Personales: nombres, teléfonos y direcciones de clientes y comerciantes     |
| R-05 | Integración  | Yape no ofrece una API pública abierta: el cobro debe hacerse mediante un proveedor de pagos o convenio. Los mensajes de WhatsApp iniciados por el negocio requieren plantillas aprobadas en WhatsApp Business Platform |
| R-06 | Dispositivos | Comerciantes con celulares Android de gama baja (≈ 2 GB RAM, poco almacenamiento) y conectividad 3G intermitente; no se puede exigir instalar una app pesada |

## 4. Escenarios de atributos de calidad

| ID    | Atributo                         | Fuente                                                         | Estímulo                                                                   | Entorno                                                                          | Artefacto                                                  | Respuesta                                                                                              | Medida                                                                                                   |
|-------|----------------------------------|----------------------------------------------------------------|----------------------------------------------------------------------------|----------------------------------------------------------------------------------|------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| QA-01 | Capacidad de interacción (usabilidad) | Comerciante con poca experiencia digital (con sesión iniciada) | Quiere publicar un producto nuevo en su puesto                              | Celular Android gama baja (≈ 2 GB RAM), red 3G, operación normal                   | PWA, pantalla "Publicar producto" (módulo Catálogo)         | El producto queda visible en el catálogo del puesto, con foto y precio                                  | ≤ 3 toques desde la pantalla de inicio; ≥ 8 de 10 comerciantes de prueba lo logran sin ayuda en ≤ 60 s     |
| QA-02 | Fiabilidad (tolerancia a fallos de red) | Comerciante                                                | Publica un producto o lo marca como agotado mientras no tiene señal         | Sin conexión durante hasta 30 min dentro del mercado                               | PWA (service worker + cola local en IndexedDB)              | La acción se guarda localmente, se muestra como "pendiente" y se sincroniza al recuperar la señal       | 0 acciones perdidas; sincronización ≤ 60 s después de recuperar la conexión                               |
| QA-03 | Disponibilidad (servicios externos) | WhatsApp Business API                                      | No responde o devuelve error al enviar la confirmación al comerciante       | Operación normal, pedido ya pagado                                                 | Módulo Notificaciones                                       | El pedido se registra igual, la notificación se encola y se reintenta; el pedido aparece en la PWA del comerciante | 0 pedidos perdidos; reintento cada ≤ 5 min; confirmación entregada ≤ 15 min después de que WhatsApp se recupere |
| QA-04 | Eficiencia de desempeño          | 200 clientes concurrentes                                      | Abren el catálogo de un puesto                                              | Hora pico (sábado y domingo, 7:00–10:00 a. m.), red 3G                              | Módulo Catálogo (API + PWA)                                 | Muestra la lista de productos del puesto con imágenes comprimidas                                       | p95 del tiempo de respuesta de la API ≤ 2 s; primera carga de la PWA ≤ 5 s en 3G simulada                  |

### Definición de "toque" (QA-01)

Se cuenta como toque cada pulsación de navegación o confirmación desde la pantalla de inicio de la
PWA, con la sesión ya iniciada. Ejemplo del flujo objetivo:
(1) "+ Producto" → (2) elegir el producto de una lista predefinida con foto (o tomar la foto) →
(3) "Publicar". El precio se precarga (último precio usado o precio sugerido) y solo se edita si cambió.

## 5. ¿Cómo se verifica cada escenario?

| ID    | Método de verificación                                                                                                    |
|-------|---------------------------------------------------------------------------------------------------------------------------|
| QA-01 | Prueba de usabilidad con 10 comerciantes (o personas con perfil similar) en un celular de gama baja; se cuentan toques y tiempo |
| QA-02 | Prueba manual con el modo avión activado en Chrome DevTools/celular; se revisa que la cola local se vacíe al reconectar    |
| QA-03 | Prueba de integración con un *mock* de WhatsApp que devuelve error 500; se revisan la cola de reintentos y los registros del pedido |
| QA-04 | Prueba de carga con Locust (200 usuarios) + Lighthouse con *throttling* "Slow 3G" para medir la primera carga             |
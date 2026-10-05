# Arquitectura MVP San Camilo

**Created:** 10/4/2026 23:02:50  
**Updated:** 10/4/2026 23:02:50  
**Exported:** 10/4/2026 23:03:14  
**Link:** [https://gemini.google.com/app/ad45c9419a3e178d](https://gemini.google.com/app/ad45c9419a3e178d)  

## User:

> 10/4/2026 23:02:50

Actúa como arquitecto de software senior con experiencia en sistemas para PYMES y mercados tradicionales.
Contexto: plataforma "San Camilo en Línea" para los puestos del Mercado San Camilo (Arequipa).
Los comerciantes publican productos por puesto; los clientes arman un pedido con productos de varios puestos, eligen recojo o delivery y pagan con Yape; el comerciante recibe la confirmación por WhatsApp; un repartidor recoge en los puestos. ~200 clientes concurrentes en hora pico (sábado y domingo por la mañana).
Restricciones: MVP en producción en 1 mes; 2 developers con experiencia en Python/Django y sin experiencia en DevOps; presupuesto bajo (un solo VPS); comerciantes con poca experiencia digital, celulares Android de gama baja y 3G intermitente. Atributo crítico: un comerciante publica un producto en ≤ 3 toques.
Tarea: propón 3 alternativas de estilo arquitectónico. Para cada una indica fortalezas,
debilidades, riesgos y qué atributos de calidad favorece o penaliza.
Formato: tabla comparativa en Markdown y, al final, tu recomendación justificada.
No inventes APIs ni capacidades de servicios; si no estás seguro, indícalo.

## Gemini:

> 10/4/2026 23:02:50

| Alternativa Arquitectónica | Fortalezas | Debilidades | Riesgos | Atributos de Calidad |
| :--- | :--- | :--- | :--- | :--- |
| **1. Monolito Modular SSR (Django + HTMX + PWA Ligeros)** | • Aprovechamiento al 100% del stack actual de los 2 devs.<br>• Carga de páginas e intercambios fragmentados ultra livianos (solo HTML en la red, sin grandes bundles JS).<br>• Un solo proceso de despliegue y baja carga de RAM en el VPS.<br>• Garantiza la salida del MVP en 1 mes. | • Acoplamiento de interfaz y backend si no se estructuran bien las aplicaciones de Django.<br>• Escalamiento limitado a la capacidad vertical del VPS único. | • Bloqueo de peticiones HTTP si la integración de WhatsApp o Yape se ejecuta de manera síncrona en la vista. | **Favorece:** Tiempo de salida al mercado (*Time-to-Market*), Rendimiento en redes móviles (Latencia/Carga en 3G), Usabilidad, Simplicidad Operativa.<br>**Penaliza:** Escalabilidad horizontal masiva, Aislamiento de fallos entre módulos. |
| **2. Arquitectura Desacoplada (Django REST Framework + Frontend SPA/PWA en React/Vue)** | • Separación clara entre lógica de negocio (API) y cliente web.<br>• Permite reutilizar endpoints si a futuro se desarrolla una App nativa Android.<br>• Capacidad de cachear datos en el cliente para operaciones sin conexión. | • Duplicación de trabajo (creación de API, contratos JSON, serializadores y estado en cliente).<br>• Carga inicial pesada en el celular gama baja al descargar bundles JS.<br>• Gestión adicional de seguridad (CORS, tokens JWT). | • Incumplimiento drástico del plazo de 1 mes por sobrecarga de desarrollo en 2 devs sin especialista en frontend. | **Favorece:** Reusabilidad de APIs, Desacoplamiento.<br>**Penaliza:** Tiempo de salida al mercado, Rendimiento (*First Contentful Paint* en 3G y gama baja), Mantenibilidad para un equipo reducido. |
| **3. Monolito Orientado a Eventos y Tareas Asíncronas (Django + Celery / Redis + Webhooks)** | • Resiliencia ante fallos de conectividad 3G y APIs externas lentas (WhatsApp/Yape).<br>• Respuesta inmediata en interfaz (las tareas lentas pasan a colas de fondo).<br>• Manejo desacoplado de notificaciones masivas. | • Complejidad de infraestructura añadida (múltiples servicios a supervisar: Redis, Celery workers, broker).<br>• Mayor dificultad de depuración y pruebas para el equipo. | • Caídas de servicios por consumo excesivo de memoria RAM en un VPS único sin tuning de DevOps.<br>• Fallos silenciosos en la cola de tareas sin monitoreo adecuado. | **Favorece:** Disponibilidad, Fiabilidad/Resiliencia, Tiempo de respuesta HTTP.<br>**Penaliza:** Operabilidad (sin experiencia DevOps), Eficiencia de recursos (RAM en VPS), Simplicidad de desarrollo. |

---

### Recomendación Justificada

La arquitectura recomendada es el **Monolito Modular SSR (Django + HTMX + PWA) con Cola de Tareas Asíncrona Ligera (Huey / Django-Q2)**.

#### Fundamentación Técnica

1. **Alineación con las Restricciones del Proyecto:**
   * **Equipo y Tiempo (1 mes / 2 Devs):** Desarrollar un monolito modular con vistas y plantillas tradicionales de Django elimina la necesidad de crear APIs REST, serializadores y gestionar estado complejo de SPA. El equipo produce directamente sobre su área de fortaleza.
   * **Infraestructura (VPS Único sin DevOps):** Ejecutar una sola pila (Nginx + Gunicorn + Django + PostgreSQL) en Ubuntu/Debian es mantenible con un script simple o *Docker Compose* básico. ~200 usuarios concurrentes en hora pico representan una carga ligera (~30-50 req/seg max) que un VPS estándar de 2 vCPU / 4 GB RAM maneja holgadamente si PostgreSQL está correctamente indexado.

2. **Cumplimiento del Atributo Crítico (Publicar en ≤ 3 toques sobre 3G):**
   * **Carga liviana:** HTMX envía pequeños fragmentos de HTML formateado directamente desde el servidor en lugar de transferir grandes payloads JSON manipulados por JavaScript. Esto minimiza el consumo de CPU en celulares Android de gama baja y responde fluido bajo redes 3G intermitentes.
   * **Flujo UX sugerido para 3 toques:**
     1. *Toque 1:* Abrir PWA y presionar botón flotante "+ Producto" (despliega captura directa usando la cámara del navegador vía HTML5).
     2. *Toque 2:* Tomar la foto (una librería JS liviana en cliente comprime la imagen a < 100 KB antes de subir).
     3. *Toque 3:* Seleccionar precio/categoría rápida preconfigurada y presionar "Publicar".

3. **Manejo de Integraciones externas y Redes Inestables:**
   * No se debe bloquear el flujo HTTP enviando mensajes de WhatsApp o validando pagos de Yape en tiempo real dentro del hilo principal de Django.
   * En lugar de instalar Celery/Redis (que agrega consumo de RAM y complejidad operativa), se recomienda usar una cola ligera sobre la misma base de datos como **Django-Q2** o un **Huey** ligero con Redis. La petición HTTP responde de inmediato al comerciante/cliente y el worker en segundo plano reintenta el envío por WhatsApp mediante la Meta Cloud API (o BSP) si la red 3G del comerciante parpadea.

4. **Consideración sobre Integraciones de Pago y Notificaciones:**
   * *Yape:* Yape no cuenta con una API abierta pública directa para comercios individuales sin pasarela intermedia (como Culqi o Izipay). Para el MVP, el flujo debe soportar la subida del captura de pantalla/código de aprobación o la integración vía pasarela de pago autorizada.
   * *WhatsApp:* Debe usarse un webhook oficial (Meta Cloud API) para garantizar entregas en segundo plano, evitando simular sesiones web de WhatsApp que son inestables para un entorno de producción.

## User:

> 10/4/2026 23:02:50

Ahora actúa como "abogado del diablo". Critica duramente la alternativa que recomendaste: ¿qué supuestos no se cumplen con nuestras restricciones?, ¿qué podría fallar en producción?, ¿qué costo oculto tiene? Enumera los 5 riesgos más graves y, para cada uno, una táctica arquitectónica de mitigación.

## Gemini:

> 10/4/2026 23:02:50

Voy a ser destructivo con la propuesta. La solución planteada en papel suena idílica para el equipo de desarrollo, pero asume escenarios idealizados que en el contexto real del Mercado San Camilo y en la ejecución técnica van a estallar durante el primer sábado en producción.

---

### Supuestos Falsos e Idealizados

1. **"HTMX + PWA es trivial y no requiere aprendizaje":**
   Asumir que dos desarrolladores de Django dominarán en 4 semanas los casos de borde de HTMX (*swapping* de fragmentos, eventos en el cliente, gestión de historial con el botón "atrás" del navegador) y la gestión de *Service Workers* de una PWA es un error. Los errores de sincronización de estado de la interfaz consumirán la mitad del tiempo de desarrollo.
2. **"3G e HTMX son la combinación perfecta":**
   HTMX exige un viaje de ida y vuelta al servidor por cada interacción dinámica. Si la señal 3G parpadea a mitad del envío de una actualización en el estand, la interfaz se quedará "colgada" sin respuesta explícita al usuario, provocando que el comerciante presione el botón múltiples veces y genere solicitudes duplicadas.
3. **"El celular gama baja puede comprimir la foto antes de subirla":**
   Un Android de gama entrada ($80 USD) con 1 GB o 2 GB de RAM ejecutando un script de compresión de imágenes en el hilo principal del navegador web (vía `canvas`) sufrirá cierres intempestivos (*crashes*) de la pestaña por consumo de memoria, o congelará el teléfono por 8-10 segundos. Adicionalmente, la PWA perderá el contexto de la cámara si el sistema operativo mata la pestaña en segundo plano para liberar memoria.
4. **"No se necesita DevOps para un VPS de producción":**
   Correr Gunicorn, Nginx, PostgreSQL y un worker de tareas en la misma máquina sin aislar recursos implica que un pico de consumo de RAM por parte de una imagen pesada activará el *OOM Killer* de Linux, el cual terminará matando la base de datos o el servidor web sin aviso.

---

### Costos Ocultos y Puntos de Fallo en Producción

* **Costo de soporte operativo humano:** Los comerciantes no llamarán a una mesa de ayuda; si la app falla o el flujo de "3 toques" no se entiende al primer intento, abandonarán la herramienta y volverán a la venta presencial/teléfono. El costo de re-capacitación y fricción no está considerado.
* **Consumo descontrolado de disco en el VPS:** El almacenamiento local de imágenes subidas por los comerciantes, sumado a logs de Django y Nginx sin rotación (`logrotate`), llenará el disco duro del VPS en semanas, dejando la base de datos en estado de solo lectura.
* **Costos y bloqueos de la API de WhatsApp:** La API oficial de WhatsApp (Meta Cloud API) cobra por conversaciones iniciadas y requiere plantillas pre-aprobadas. Si se intenta usar una biblioteca no oficial (web scraping/Node wrappers) para ahorrar, Meta bloqueará el número de teléfono del mercado en cuestión de horas.

---

### Los 5 Riesgos Más Graves y Tácticas Arquitectónicas de Mitigación

#### 1. Colapso del VPS por consumo de memoria al procesar imágenes
* **El riesgo:** Dos o tres comerciantes subiendo fotos de productos simultáneamente en hora pico saturarán la RAM de la máquina al procesarlas con Pillow/Python, provocando la caída de PostgreSQL por falta de memoria.
* **Táctica de mitigación:** **Subida directa mediante URLs firmadas (Direct-to-Storage Upload).** Eliminar el paso de las fotos por el servidor Django. El cliente solicita una URL de subida prelanzada y la foto viaja directamente desde el navegador a un almacenamiento de objetos externo (ej. Cloudflare R2 o AWS S3). La compresión pesada se delega a una función *serverless* gratuita/de bajo costo o a las reglas automáticas del almacenamiento.

#### 2. Duplicación de pedidos y registros por desconexión en redes 3G
* **El riesgo:** La latencia del 3G provocará que el comerciante o cliente presione repetidamente los botones de "Publicar" o "Pagar", creando productos duplicados o registros múltiples en la cola de notificaciones.
* **Táctica de mitigación:** **Idempotencia estricta en Backend con Tokens UUID.** Cada formulario crítico generado por Django incluirá un token de idempotencia único en un campo oculto o cabecera `X-Idempotency-Key`. Django rechazará o ignorará cualquier petición subsecuente que contenga un token ya procesado en los últimos 15 minutos.

#### 3. Saturación de conexiones HTTP en Gunicorn durante hora pico
* **El riesgo:** 200 usuarios concurrentes navegando el catálogo en hora pico agotarán el grupo de procesos (*workers*) de Gunicorn. Si cada petición tarda 500ms por latencia de red 3G, la cola de peticiones de Nginx se llenará y responderá con errores `504 Gateway Timeout`.
* **Táctica de mitigación:** **Cacheado de fragmentos a nivel de aplicación e Hilos Asíncronos en Nginx.** Aplicar la etiqueta `{% cache %}` de Django respaldada por memoria (LocMemCache o un Redis ultra compacto de 50MB) sobre los bloques de catálogo de productos. Esto permite que Django sirva las peticiones en <20ms directamente desde memoria sin golpear la base de datos.

#### 4. Fallo total del flujo de "3 toques" por incompatibilidad de PWA/Navegador
* **El riesgo:** Las restricciones de permisos de la PWA o del Service Worker fallarán en navegadores desactualizados (ej. Android WebView antiguo de celulares gama baja), impidiendo el acceso a la cámara o la instalación del acceso directo.
* **Táctica de mitigación:** **Degradación Progresiva Reversible (Graceful Degradation).** El sistema debe ser utilizable como una aplicación web móvil tradicional en HTML puro (`<input type="file" accept="image/*" capture="environment">`). Si el Service Worker o el JavaScript del cliente fallan por completo, el formulario HTML sigue enviando datos nativamente sin depender del estado del lado del cliente.

#### 5. Retraso del MVP por sobre-ingeniería con HTMX y trabajadores asíncronos
* **El riesgo:** Intentar implementar HTMX en todo el sitio y configurar un entorno de colas asíncronas desde el día 1 sobrepasará la capacidad de desarrollo de los 2 ingenieros en las 4 semanas disponibles.
* **Táctica de mitigación:** **Reducción a Arquitectura Síncrona Estricta para V1 (MVP simplificado).** Limitar HTMX exclusivamente al botón de "Añadir al carrito" y al selector de "Publicación rápida". El resto de las vistas se desarrollarán con recargas de página tradicionales de Django. Reemplazar la cola de tareas externa por un procesamiento en background simple basado en hilos nativos de Python (`concurrent.futures.ThreadPoolExecutor`) únicamente para el disparo de notificaciones no críticas.

Powered by Gemini Exporter (https://www.ai-chat-exporter.com)

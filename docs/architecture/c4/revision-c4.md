# Revisión de las vistas con la lista oficial de c4model.com (E7)

Lista aplicada: Tabla 3 de la guía (General, Elementos, Relaciones). Las cinco vistas salen de
`workspace.dsl`.

## 1\. Resultado por vista

|Vista|General: ¿título, tipo, alcance y leyenda?|Elementos: ¿nombre, tipo, descripción y tecnología?|Relaciones: ¿etiqueta con intención, dirección correcta y protocolo?|
|-|-|-|-|
|Contexto|Sí. Título «System Context View», descripción de nivel 1 y leyenda|Sí. 3 personas, el sistema y 2 externos con descripción; sin tecnologías internas|Sí. Cada flecha tiene un verbo («Solicita el cobro del pedido»); las de los externos indican HTTPS/JSON|
|Contenedores|Sí. Título, descripción de nivel 2, límite del sistema y leyenda|Sí. Los 6 contenedores muestran tecnología (Django + Gunicorn, Celery, Redis, PostgreSQL…)|Sí. Todas con protocolo (HTTPS/JSON, SQL/TCP, Redis protocol)|
|Componentes|Sí. Título, descripción y leyenda|Sí. 5 módulos «Django app» con su responsabilidad|Sí. Las dependencias entre módulos coinciden con `paquetes.puml`: `reparto → pedidos → {catalogo, pagos, notificaciones}`, sin ciclos|
|Dinámica|Sí. Título «Dynamic View» y leyenda|Sí. Mismos elementos del modelo|Sí. 10 pasos numerados; cada uno corresponde a una relación ya declarada|
|Despliegue|Sí. Título, entorno «Producción» y leyenda|Sí. Nodos con sistema operativo y tamaño (2 vCPU / 4 GB), instancias de los 6 contenedores|Sí. Etiquetas en las relaciones entre nodos de infraestructura|

## 2\. Hallazgos del Prompt IA 2 y verificación del equipo

|Vista|Hallazgo de la IA|Verificación del equipo|
|-|-|-|
|Contenedores|«El proveedor de pagos y WhatsApp están definidos como `System`, no como `System_Ext`»|**Correcto:** en el PNG se ven en azul, igual que un sistema propio, y la leyenda no incluye «external system». Quedan fuera del límite del sistema, pero no se distinguen por color. Se anota como limitación del exportador.|
|Contenedores|«La etiqueta de la flecha Comerciante → PWA se superpone con el título del límite del sistema»|**Correcto:** se ve en el PNG; es un problema de disposición automática que no afecta al contenido del modelo.|
|Contenedores|«La PWA no tiene forma de navegador»|**Correcto:** C4-PlantUML no tiene forma de navegador; la PWA se identifica por su tecnología («Service Worker, IndexedDB»). Se corrige la frase del informe.|
|Contenedores|«El Planificador dice que cancela pedidos sin pago, pero solo tiene flecha hacia Redis»|**Correcto, observación:** el Planificador solo programa tareas por Redis; qué proceso las ejecuta queda por documentar.|
|Contenedores|«La flecha de la API hacia Redis mezcla caché y cola»|**Correcto:** se aceptan ambas porque comparten protocolo; queda explicado en la descripción.|
|Contenedores|«La relación WhatsApp → Comerciante no indica tecnología»|**Falso positivo:** es el aviso que le llega a una persona; la lista exige protocolo entre contenedores y sistemas, no hacia personas.|

Mínimo exigido: **al menos 1 falso positivo** identificado con su justificación.


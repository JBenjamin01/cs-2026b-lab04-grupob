# Revisión de las vistas con la lista oficial de c4model.com (E7)

Lista aplicada: Tabla 3 de la guía (General, Elementos, Relaciones). Las cinco vistas salen de
`workspace.dsl`.

> Después de generar los PNG, abran cada imagen y confirmen cada «Sí». Si algo no se ve bien
> (texto cortado, falta la leyenda), corrijan el DSL, vuelvan a exportar y cambien la fila.

## 1\. Resultado por vista

|Vista|General: ¿título, tipo, alcance y leyenda?|Elementos: ¿nombre, tipo, descripción y tecnología?|Relaciones: ¿etiqueta con intención, dirección correcta y protocolo?|
|-|-|-|-|
|Contexto|Sí. Título «System Context View», descripción de nivel 1 y leyenda|Sí. 3 personas, el sistema y 2 externos con descripción; sin tecnologías internas|Sí. Cada flecha tiene un verbo («Solicita el cobro del pedido»); las de los externos indican HTTPS/JSON|
|Contenedores|Sí. Título, descripción de nivel 2, límite del sistema y leyenda|Sí. Los 6 contenedores muestran tecnología (Django + Gunicorn, Celery, Redis, PostgreSQL…)|Sí. Todas con protocolo (HTTPS/JSON, SQL/TCP, Redis protocol)|
|Componentes|Sí. Título, descripción y leyenda|Sí. 5 módulos «Django app» con su responsabilidad|Sí. Las dependencias entre módulos coinciden con `paquetes.puml`: `reparto → pedidos → {catalogo, pagos, notificaciones}`, sin ciclos|
|Dinámica|Sí. Título «Dynamic View» y leyenda|Sí. Mismos elementos del modelo|Sí. 10 pasos numerados; cada uno corresponde a una relación ya declarada|
|Despliegue|Sí. Título, entorno «Producción» y leyenda|Sí. Nodos con sistema operativo y tamaño (2 vCPU / 4 GB), instancias de los 6 contenedores|Sí. Etiquetas en las relaciones entre nodos de infraestructura|

## 2\. Hallazgos del Prompt IA 2 y verificación del equipo

> Reemplacen estas filas por la salida real de la IA. Dejo los tipos de hallazgo que suelen
> aparecer para que sepan cómo verificarlos; no los copien si la IA no los reportó.

|Vista|Hallazgo de la IA|Verificación del equipo|
|-|-|-|
|<<COMPLETAR>>|<<COMPLETAR>>|<<COMPLETAR: Correcto / Falso positivo y por qué>>|
|Contexto|(Si lo reporta) «Faltan las tecnologías de las relaciones con las personas»|**Falso positivo:** en el nivel 1 no se exigen tecnologías para las personas, y la guía pide que el contexto no muestre tecnologías internas|
|Contenedores|(Si lo reporta) «La flecha de `sc.api` hacia Redis mezcla caché y cola»|**Correcto:** se aceptan ambas porque comparten protocolo y quedan explicadas en la descripción|
|Despliegue|(Si lo reporta) «El monitoreo corre en el mismo VPS»|**Correcto, trade-off aceptado:** lo exige R-03 y está documentado en el nodo y en el informe del Lab 04|

Mínimo exigido: **al menos 1 falso positivo** identificado con su justificación.


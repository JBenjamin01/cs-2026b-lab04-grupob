# Matriz de decisión — San Camilo en Línea

## 1. Alternativas

Las tres alternativas se obtuvieron con apoyo de IA (ver [bitácora](bitacora-ia.md), entrada 1)
y fueron revisadas por el equipo.

- **A. Monolito en capas:** una sola aplicación Django organizada en presentación → lógica de
  negocio → acceso a datos. Servicios y modelos se comparten entre todas las funcionalidades
  (catálogo, pedidos, pagos, notificaciones y reparto) sobre una sola base de datos.
- **B. Monolito modular:** un solo despliegue Django dividido en 5 módulos de dominio (catálogo,
  pedidos, pagos, notificaciones, reparto) que se comunican solo mediante interfaces públicas.
  Cada módulo tiene su propio esquema en PostgreSQL, y las integraciones externas (Yape, WhatsApp)
  van detrás de puertos y adaptadores.
- **C. Microservicios:** cada funcionalidad es un servicio desplegable de forma independiente,
  con su propia base de datos, detrás de un API Gateway y comunicado mediante un broker de
  eventos (RabbitMQ), en contenedores.

## 2. Criterios y pesos (suman 100 %)

| Criterio                            | Peso      | Justificación (driver relacionado)                                                              |
|-------------------------------------|-----------|-------------------------------------------------------------------------------------------------|
| Tiempo de entrega                   | 25 %      | R-01: MVP en producción en 1 mes; R-02: solo 2 developers                                        |
| Costo operativo                     | 20 %      | R-03: un solo VPS de bajo costo; cada servicio de pago debe justificarse                         |
| Modificabilidad                     | 20 %      | Atributo 5 y R-05: se agregará Plin u otra pasarela; RF-03 (pedido multipuesto) cruza 4 módulos |
| Simplicidad operativa               | 15 %      | R-02: el equipo no tiene experiencia en DevOps ni en orquestación de contenedores                |
| Disponibilidad ante fallas externas | 10 %      | QA-03: 0 pedidos perdidos si WhatsApp o el proveedor de pagos fallan                              |
| Desempeño y escalabilidad           | 10 %      | QA-04: 200 clientes concurrentes en hora pico; carga moderada y predecible                       |
| **Total**                           | **100 %** |                                                                                                 |

> **Criterio excluido a propósito: capacidad de interacción (QA-01) y fiabilidad offline (QA-02).**
> Son los atributos más importantes del caso, pero no diferencian estas alternativas: los resuelve
> el *frontend* (PWA offline-first, ver ADR-003), que sería igual en A, B y C. Incluirlos daría el
> mismo puntaje a las tres y solo diluiría los demás pesos.

## 3. Matriz (puntaje 1 = muy malo … 5 = excelente)

| Criterio (peso)                            | A. Capas | B. Monolito modular | C. Microservicios | Razón del puntaje                                                                    |
|--------------------------------------------|:--------:|:-------------------:|:-----------------:|--------------------------------------------------------------------------------------|
| Tiempo de entrega (25 %)                   | 5        | 4                   | 1                 | B exige definir interfaces entre módulos; C exige gateway, broker y 5 pipelines      |
| Costo operativo (20 %)                     | 5        | 5                   | 2                 | A y B caben en un VPS; C necesita más RAM o varios nodos                              |
| Modificabilidad (20 %)                     | 2        | 4                   | 5                 | En A una nueva pasarela toca servicios compartidos; en B es solo un adaptador nuevo   |
| Simplicidad operativa (15 %)               | 5        | 4                   | 1                 | B agrega Celery y reglas de límites; C agrega observabilidad distribuida             |
| Disponibilidad ante fallas externas (10 %) | 3        | 4                   | 4                 | B aísla WhatsApp tras un puerto + cola con reintentos; C igual, con más puntos de falla |
| Desempeño y escalabilidad (10 %)           | 3        | 3                   | 4                 | 200 concurrentes son manejables en un VPS; C escala mejor, pero aún no se necesita   |
| **Total ponderado**                        | **4,00** | **4,10**            | **2,60**          |                                                                                      |

Total ponderado = Σ (peso × puntaje):

- A = 0,25×5 + 0,20×5 + 0,20×2 + 0,15×5 + 0,10×3 + 0,10×3 = **4,00**
- B = 0,25×4 + 0,20×5 + 0,20×4 + 0,15×4 + 0,10×4 + 0,10×3 = **4,10**
- C = 0,25×1 + 0,20×2 + 0,20×5 + 0,15×1 + 0,10×4 + 0,10×4 = **2,60**

![Matriz de decisión](diagramas/img/matriz-decision.png)

## 4. Análisis de sensibilidad

La diferencia entre B y A es pequeña (0,10), así que verificamos qué tan robusta es la decisión.
Si se traslada peso de *modificabilidad* a *tiempo de entrega*, A gana 3 décimas por cada 10 puntos
de peso trasladados, mientras que B no cambia. **A supera a B solo si el peso de modificabilidad
baja de ≈ 17 %.**

Mantenemos el 20 % por tres motivos:

1. R-05 ya anuncia una segunda pasarela (Plin).
2. El pedido multipuesto (RF-03) involucra catálogo, pedidos, pagos y notificaciones; en un
   monolito en capas esos cambios se cruzan en los mismos archivos.
3. Con 2 developers que generan código con apoyo de IA, los límites explícitos entre módulos
   reducen el riesgo de que el código generado mezcle responsabilidades.

Microservicios (C) queda último con cualquier distribución razonable de pesos, porque pierde en
los tres criterios ligados a R-01, R-02 y R-03, que suman el 60 % del peso.

## 5. Afirmaciones de la IA verificadas

| # | Afirmación de la IA | Cómo la verificamos | Resultado |
|---|---------------------|---------------------|-----------|
| 1 | <Recomendación de la IA en el Prompt 1, p. ej., "microservicios con Kubernetes por escalabilidad"> | Contraste con R-01 (1 mes), R-02 (2 devs sin DevOps) y R-03 (un VPS); la carga de QA-04 (200 concurrentes) no justifica un despliegue distribuido | <Rechazada / Aceptada> |
| 2 | <Riesgo o afirmación exagerada del Prompt 2 (crítica adversarial)> | <Cálculo, documentación oficial o restricción contrastada> | <Aceptada / Corregida / Rechazada> |
| 3 | "Yape no ofrece una API pública abierta; el cobro requiere un proveedor de pagos" (usada en R-05) | Revisión de la documentación oficial de Yape y de proveedores que ofrecen cobro con Yape | <Confirmada / Corregida: anotar la fuente> |

La decisión final la tomó el equipo. <Si la IA recomendó otra alternativa, explicar aquí en 1–2
líneas por qué el equipo se apartó de su recomendación.>

## 6. Conclusión

Elegimos el **monolito modular (B)** porque obtiene el mayor puntaje (4,10) y es la única
alternativa que equilibra la entrega en 1 mes con 2 developers y un VPS (R-01, R-02, R-03) con la
necesidad de agregar pasarelas y aislar las fallas de WhatsApp (R-05, QA-03). El monolito en capas
queda cerca, pero acopla los módulos que el pedido multipuesto necesita mantener separados.
Ver [ADR-001](adr/001-estilo-arquitectonico.md).
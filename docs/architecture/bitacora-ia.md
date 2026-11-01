# Bitácora de uso de IA — San Camilo en Línea

Registro de las interacciones con asistentes de IA durante el Laboratorio 04. Regla de trabajo: la IA propone, el equipo decide y verifica. No se incluyeron datos personales ni confidenciales en los prompts.

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Qué verificamos o corregimos | Decisión |
|---|-------|-------------|------------------|-------------------|------------------------------|----------|
| 1 | 04/10 | Gemini | Prompt 1: tres alternativas de estilo y recomendación | Monolito modular SSR (Django + HTMX + PWA), arquitectura desacoplada (DRF + SPA) y monolito orientado a eventos (Celery/Redis). Recomendó el monolito modular, con un flujo de publicación de 3 toques, validación del pago con captura de Yape y Django-Q2/Huey para evitar Celery | Se contó el flujo en un celular Android y dio 5 toques. Una captura de Yape puede falsificarse. Huey también usa Redis, así que la recomendación se contradice | Corregida |
| 2 | 04/10 | Gemini | Prompt 2: crítica adversarial (5 riesgos y mitigaciones) | Riesgos como saturación de RAM con Pillow (propuso R2/S3 + serverless) y envío de notificaciones con hilos (ThreadPoolExecutor) | Cálculo de RAM: una foto de 12 MP ocupa unos 48 MB decodificada, y tres simultáneas unos 150 MB de 4 GB, así que el riesgo estaba exagerado. Los hilos pierden tareas si el proceso se reinicia e incumplen QA-03. Se aceptaron la idempotencia y la degradación progresiva | Corregida (parcial) |
| 3 | 04/10 | ChatGPT | Prompt 1: tres alternativas de estilo y recomendación | Monolito modular, monolito con eventos ligeros y microservicios. Recomendó el monolito modular y sugirió postergar las tareas asíncronas hasta que haga falta | QA-03 exige reintentos desde el MVP, por lo que la cola entra en el MVP solo para notificaciones | Corregida |
| 4 | 04/10 | ChatGPT | Prompt 2: crítica adversarial (5 riesgos y mitigaciones) | Riesgos del monolito modular con tácticas de mitigación | Riesgos coherentes con R-03, R-05 y QA-03. Se incorporaron en ADR-001 y ADR-002 | Aceptada |
| 5 | 04/10 | Claude | Drivers del caso (E1) | Borrador de drivers.md | Se corrigió el tamaño del equipo: son 2 integrantes, no 3 (R-02) | Corregida |
| 6 | 04/10 | Claude | Matriz de decisión (E2) | Matriz ponderada con análisis de sensibilidad | Totales recalculados a mano. Se pidió registrar que la IA recomendó microservicios y Claude advirtió que eso no había ocurrido, por lo que no se registró | Aceptada |
| 7 | 04/10 | Claude | Diagrama Mermaid (E3) | Código de arquitectura.mmd | Validado en mermaid.live. Se ajustó visualmente la etiqueta de RF-06 | Corregida (visual) |
| 8 | 04/10 | Claude | Redacción de los 3 ADR (E4) | Borradores de ADR-001, ADR-002 y ADR-003 | Se comprobó que el patrón outbox es necesario para cumplir QA-03 | Aceptada |
| 9 | 04/10 | Claude | Diagrama PlantUML (E5) | Diagrama de una alternativa descartada | La guía exige diagramar la segunda mejor alternativa (monolito en capas, 4,00), no microservicios | Corregida |
| 10 | 04/10 | Claude | Script de despliegue para Colab (E6) | despliegue.py con Python Diagrams | Ejecutado en Google Colab y revisada la imagen generada | Aceptada / Corregida |

---

## Anexo: prompts

Conversaciones completas:

- ChatGPT: https://chatgpt.com/share/6ac2e168-5e40-83e9-8431-a5766a4a6b38
- Gemini: https://gemini.google.com/share/d/1iA6QQnZWR9xCvyRUkTl0eTbDfBiWRwK7?usp=sharing

### Prompt 1 — Generación de alternativas (interacciones 1 y 3)

```
Actúa como arquitecto de software senior con experiencia en sistemas para PYMES y
mercados tradicionales.
Contexto: plataforma "San Camilo en Línea" para los puestos del Mercado San Camilo
(Arequipa). Los comerciantes publican productos por puesto; los clientes arman un
pedido con productos de varios puestos, eligen recojo o delivery y pagan con Yape;
el comerciante recibe la confirmación por WhatsApp; un repartidor recoge en los
puestos. ~200 clientes concurrentes en hora pico (sábado y domingo por la mañana).
Restricciones: MVP en producción en 1 mes; 2 developers con experiencia en
Python/Django y sin experiencia en DevOps; presupuesto bajo (un solo VPS);
comerciantes con poca experiencia digital, celulares Android de gama baja y 3G
intermitente. Atributo crítico: un comerciante publica un producto en ≤ 3 toques.
Tarea: propón 3 alternativas de estilo arquitectónico. Para cada una indica
fortalezas, debilidades, riesgos y qué atributos de calidad favorece o penaliza.
Formato: tabla comparativa en Markdown y, al final, tu recomendación justificada.
No inventes APIs ni capacidades de servicios; si no estás seguro, indícalo.
```

### Prompt 2 — Crítica adversarial (interacciones 2 y 4)

```
Ahora actúa como "abogado del diablo". Critica duramente la alternativa que
recomendaste: ¿qué supuestos no se cumplen con nuestras restricciones?, ¿qué podría
fallar en producción?, ¿qué costo oculto tiene? Enumera los 5 riesgos más graves y,
para cada uno, una táctica arquitectónica de mitigación.
```

### Prompts a Claude (interacciones 5 a 10)

**Interacción 5 — Drivers (E1):**
Oye, vamos en orden, primero el E2 por favor, y ten en mente que yo, Jhonatan haré los primeros 4, es decir, de E1 a E4, asi que cuando lleguemos al readme y ello, intercambias roles

**Interacción 6 — Matriz de decisión (E2):**
Confirmado, puedes continuar (ya que tienes la base y ello, intenta hacer un buen trabajo con todo, y por cierto, solo seremos dos integrantes los que hacemos este trabajo)

**Interacción 7 — Diagrama Mermaid (E3):**
Sigamos con E3

**Interacción 8 — ADR (E4):**
vale, sigamos con E4

**Interacción 9 — Diagrama PlantUML (E5):**
Perfecto, sigamos con E5

**Interacción 10 — Script de despliegue (E6):**
Continuemos con el E6
---

# Laboratorio 08 — Diseño de la arquitectura con ADD (San Camilo en Línea 2.0)

Regla de oro: **la IA propone, el equipo decide con evidencia.** Ninguna táctica se adoptó sin un
escenario prioritario, evidencia cuantitativa (simulación, prototipo o fitness function) y un ADR.
No se ingresaron datos personales, credenciales ni claves en los prompts: los celulares y montos
de las pruebas son ficticios y los proveedores están simulados.

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Verificación del equipo | Decisión |
|---|-------|-------------|------------------|-------------------|-------------------------|----------|
| 11 | 27/10 | Claude | Prompt IA 1: escenarios de seis partes con (importancia, dificultad) para los 3 mercados | 11 escenarios; QA-04 como (H,H) «porque la carga se duplica», QA-05 como (M,L) «basta un WHERE» y uno de «10 000 usuarios concurrentes» | Utilización con 3 mercados: 20 req/s × 0,11 s / 5 workers = 0,44. Un solo reporte sin WHERE expone todo. Los 3 mercados suman unos 400 clientes en hora pico | **Corregida:** QA-04 (H,M), QA-05 (H,M); se descarta el de 10 000 usuarios; 9 escenarios en el árbol |
| 12 | 27/10 | Claude | Prompt IA 2 (iteración 1): tácticas para QA-07 y QA-08 | Un despliegue por mercado, `if/elif` por mercado, motor de reglas genérico, reglas como datos | Se prototipó el `if/elif` en una rama descartada: Altiplano costó 54 líneas en 3 archivos, Río Seco 11 más; 10 condicionales por mercado y 2 pruebas del Lab 07 rotas | **Aceptada** «reglas como datos» (ADR-006); las otras 3, rechazadas |
| 13 | 28/10 | Claude | Prompt IA 2 (iteración 2): multitenencia para QA-05 | Una BD por mercado, una librería de multitenencia con un esquema por mercado, o `mercado_id` + RLS | El esquema por mercado choca con ADR-002 (un esquema por módulo: serían 18). Se midió en PostgreSQL 16: sin RLS, un reporte sin filtro ve 15 028 a 23 971 filas ajenas; con RLS, 0 | **Aceptada** `mercado_id` + RLS + claim (ADR-007); esquemas por mercado, rechazados |
| 14 | 29/10 | Claude | Prompt IA 2 (iteración 3): tácticas para QA-09 | Primero «subir a 10 reintentos» y «basta con guardar el cobro pendiente» | Más reintentos bloquean al cliente y multiplican las llamadas al proveedor caído (132 con solo 3 reintentos). Una outbox sin circuito sigue llamando en cada pedido nuevo | **Corregida:** reintentos + circuit breaker + outbox en PostgreSQL (ADR-008) |
| 15 | 29/10 | Claude | Adaptar `disponibilidad.py` del docente a un sábado con 3 mercados | Simulación con un solo generador aleatorio para llegadas y fallas | Cada táctica recibía una cantidad distinta de pedidos (1 252, 1 271 y 1 280): la comparación no era justa | **Corregida:** dos generadores; las 3 tácticas reciben los mismos 1 310 pedidos |
| 16 | 30/10 | Claude | Escribir las fitness functions estructurales (`.importlinter`) | Contrato FF-02 que prohíbe `pagos.adaptadores` | Al ejecutarlo sobre el código del Lab 07, el contrato prohibiendo `pagos.pasarelas` quedó BROKEN: `pagos/__init__.py` reexportaba los adaptadores. Y un contrato sobre un módulo inexistente pasa en silencio | **Corregida:** adaptadores en `pagos/adaptadores.py` y prueba de que el módulo exista |
| 17 | 30/10 | Claude | Prompt IA 3: evaluador ATAM adversario | 8 riesgos, 3 puntos de sensibilidad y 3 trade-offs; además: «RLS degrada el rendimiento del catálogo» y «con el circuito abierto se pierden pagos» | Medición: 0,19 ms sin RLS y 0,21 ms con RLS + índice. `test_con_el_circuito_abierto_..._nada_se_pierde` y FF-07 en verde | **Falsos positivos refutados** con evidencia; el resto, en `atam-lite.md` |
| 18 | 30/10 | Claude | Redactar ADR-006 a 008, iteraciones, README e informe | Borradores | Cifras recalculadas con las simulaciones, pytest y PostgreSQL; revisión de ambos integrantes | Aceptada con correcciones |

## Anexo Lab 08: prompts

### Prompt IA 1 — Escenarios para el árbol de utilidad (interacción 11)

```
Actúa como arquitecto de software. Contexto: [pegar drivers.md, ADR-001 y el nuevo contexto:
se suman los mercados Altiplano y Río Seco, cada uno con sus reglas y comerciantes; 1 mes;
2 developers Django; un VPS]. Tarea: propón escenarios de calidad de seis partes (fuente,
estímulo, entorno, artefacto, respuesta, medida) para rendimiento, disponibilidad, seguridad
y modificabilidad. Para cada uno sugiere (importancia, dificultad) con H/M/L y justifícalo.
Restricciones: medidas numéricas; no propongas soluciones todavía.
```

### Prompt IA 2 — Tácticas candidatas (interacciones 12 a 14)

```
Para el escenario [QA-07 | QA-05 | QA-09] [pegar], propón 4 tácticas candidatas del catálogo de
Bass et al. Para cada una indica: qué mejora, qué empeora, costo aproximado y complejidad para
un equipo de 2 developers con Django en 1 mes. Respeta ADR-001 (monolito modular en un VPS) y
ADR-002 (un esquema por módulo); si recomiendas cambiar el estilo, justifícalo con números.
```

### Prompt IA 3 — Evaluador adversario (interacción 17)

Ver [`atam-lite.md`](atam-lite.md), sección 1.

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
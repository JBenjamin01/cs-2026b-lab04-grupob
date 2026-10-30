# Bitácora de uso de IA — Laboratorio 06 (Modelo C4)

Regla de trabajo: **la IA propone, el equipo decide y verifica**. No se ingresaron datos
personales ni confidenciales en los prompts.

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Verificación del equipo | Decisión |
|---|-------|-------------|------------------|-------------------|-------------------------|----------|
| 1 | 17/10 | Claude | Prompt IA 1 adaptado: inventario, ADR-001 a ADR-004, `paquetes.puml`, secuencia y `despliegue.py` → borrador de `workspace.dsl` | Modelo con 3 personas, 2 externos, 6 contenedores (PWA, API, worker, beat, Redis, PostgreSQL), 5 componentes y vistas de contexto, contenedores, componentes, dinámica y despliegue | Se contrastó con el ejemplo del docente (AgroConecta) y con los ADR: el ejemplo usaba Docker Compose, el módulo Reportes, Plin, React y PostgreSQL 16, y nada de eso está en los ADR de San Camilo | Corregida: despliegue con systemd en un VPS único, módulo Reparto en lugar de Reportes, solo Yape, PWA con plantillas Django + JavaScript (ADR-003) y PostgreSQL sin versión |
| 2 | 17/10 | Claude | Revisar coherencia del modelo con Lab 04 y Lab 05 (regla C5 y regla C4 de dependencias) | El puerto de mensajería se llama «Mensajeria» en el ADR-001 y en `arquitectura.mmd`, pero `NotificadorMensajeria` en `clases.puml` y `paquetes.puml`; el paquete `comun` agregaría una flecha desde cada módulo | Se comprobó en `clases.puml`, `paquetes.puml` y el código de `src/`; el DSL usa `NotificadorMensajeria` y omite `comun` (documentado en `inventario.md`) | Aceptada |
| 3 | 17/10 | Claude | Decidir qué parte del DSL es suposición: sistema operativo del VPS y monitoreo | El sistema operativo no figura en los ADR; se tomó Ubuntu Server 24.04 LTS (como en el ejemplo del docente) y Grafana como monitoreo (`despliegue.py`) | Se marcó como supuesto en el DSL; `despliegue.py` sí fija Nginx, Grafana, Celery beat y respaldo `pg_dump` | Aceptada con supuesto Ubuntu 24.04 LTS, a confirmar con el servidor real |
| 4 | 30/10 | Claude | Prompt IA 2 (auditor C4) sobre la vista de contenedores exportada (.puml) | 6 hallazgos: externos sin forma `System_Ext`, PWA sin forma de navegador, Planificador sin flecha hacia lo que cancela, flecha API→Redis mezcla caché y cola, WhatsApp→Comerciante sin tecnología, etiqueta superpuesta con el título del límite | Cada hallazgo se contrastó con `img/structurizr-Contenedores.png` y con la lista oficial; resultado en `revision-c4.md` | Aceptada parcialmente: se aceptaron los hallazgos 1 a 4 y 6, y se descartó el 5 como falso positivo |
| 5 | 30/10 | Claude | Prompt IA 3: explicación del contexto para un público no técnico (máx. 120 palabras) | Devolvió una versión de 86 palabras sin mencionar el funcionamiento sin conexión ni la reintento de avisos | Se comparó con `explicacion.md` frase por frase contra el modelo; la última frase afirmaba que el pedido no se pierde si falla "alguno de esos servicios", pero solo es cierto para WhatsApp (el pedido sin pago se cancela a los 15 min) | Corregida: se separó la frase en WhatsApp y pago |
---

## Anexo: prompts utilizados

### Prompt IA 1 — Borrador del modelo en Structurizr DSL (interacciones 1 a 3)

```
Actúa como arquitecto de software experto en el modelo C4 y en Structurizr DSL.
Contexto: [pegar inventario.md, ADR-001 a ADR-004, paquetes.puml, secuencia-confirmar-pagar.puml y despliegue.py].
Tarea: escribe un workspace de Structurizr DSL con personas, el sistema, sus contenedores (con tecnología),
los componentes del contenedor API, los sistemas externos (con la etiqueta "Externo") y relaciones con
descripción y protocolo. Incluye las vistas systemContext, container, component, dynamic (confirmar y pagar)
y deployment (entorno "Producción").
Restricciones: usa SOLO las tecnologías de los ADR; no confundas contenedor C4 con contenedor Docker;
el despliegue es con systemd en un VPS único; usa !identifiers hierarchical. Formato: solo el código DSL.
```

### Prompt IA 2 — Auditor C4 (interacción 4)

```
Actúa como revisor de diagramas de arquitectura. Evalúa estas vistas exportadas de un modelo C4
[pegar los .puml o adjuntar las imágenes] con la lista de revisión de c4model.com: generales, elementos y relaciones.
Responde en una tabla (vista, pregunta de la lista, cumple sí/no, evidencia, corrección sugerida).
No inventes problemas: si algo cumple, indícalo.
```

### Prompt IA 3 — Explicación para un público no técnico (interacción 5)

```
Explica el siguiente diagrama de contexto a un comerciante del Mercado San Camilo, que no es
técnico, en máximo 120 palabras: qué hace el sistema, quién lo usa y de qué servicios externos depende.
Evita la jerga técnica. [pegar la vista de contexto]
```

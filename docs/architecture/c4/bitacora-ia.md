# Bitácora de uso de IA — Laboratorio 06 (Modelo C4)

Regla de trabajo: **la IA propone, el equipo decide y verifica**. No se ingresaron datos
personales ni confidenciales en los prompts.

> Completen las filas marcadas con `<<COMPLETAR>>` con lo que realmente ocurra al ejecutar los
> prompts. No registren interacciones que no hicieron: la bitácora debe poder auditarse.

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Verificación del equipo | Decisión |
|---|-------|-------------|------------------|-------------------|-------------------------|----------|
| 1 | 17/10 | Claude | Prompt IA 1 adaptado: inventario, ADR-001 a ADR-004, `paquetes.puml`, secuencia y `despliegue.py` → borrador de `workspace.dsl` | Modelo con 3 personas, 2 externos, 6 contenedores (PWA, API, worker, beat, Redis, PostgreSQL), 5 componentes y vistas de contexto, contenedores, componentes, dinámica y despliegue | Se contrastó con el ejemplo del docente (AgroConecta) y con los ADR: el ejemplo usaba Docker Compose, el módulo Reportes, Plin, React y PostgreSQL 16, y nada de eso está en los ADR de San Camilo | Corregida: despliegue con systemd en un VPS único, módulo Reparto en lugar de Reportes, solo Yape, PWA con plantillas Django + JavaScript (ADR-003) y PostgreSQL sin versión |
| 2 | 17/10 | Claude | Revisar coherencia del modelo con Lab 04 y Lab 05 (regla C5 y regla C4 de dependencias) | El puerto de mensajería se llama «Mensajeria» en el ADR-001 y en `arquitectura.mmd`, pero `NotificadorMensajeria` en `clases.puml` y `paquetes.puml`; el paquete `comun` agregaría una flecha desde cada módulo | Se comprobó en `clases.puml`, `paquetes.puml` y el código de `src/`; el DSL usa `NotificadorMensajeria` y omite `comun` (documentado en `inventario.md`) | Aceptada |
| 3 | 17/10 | Claude | Decidir qué parte del DSL es suposición: sistema operativo del VPS y monitoreo | El sistema operativo no figura en los ADR; se tomó Ubuntu Server 24.04 LTS (como en el ejemplo del docente) y Grafana como monitoreo (`despliegue.py`) | Se marcó como supuesto en el DSL; `despliegue.py` sí fija Nginx, Grafana, Celery beat y respaldo `pg_dump` | Aceptada con supuesto <<CONFIRMAR el sistema operativo real>> |
| 4 | <<COMPLETAR>> | <<COMPLETAR>> | Prompt IA 2 (auditor C4) sobre las 5 vistas exportadas | <<COMPLETAR con la tabla que devuelva la IA>> | <<COMPLETAR: cada hallazgo contra `revision-c4.md` y las imágenes>> | <<COMPLETAR: incluir al menos 1 falso positivo>> |
| 5 | <<COMPLETAR>> | <<COMPLETAR>> | Prompt IA 3: explicación del contexto para un público no técnico (máx. 120 palabras) | <<COMPLETAR con el texto devuelto>> | `explicacion.md` quedó en 105 palabras y se comprobó cada afirmación contra el modelo | <<COMPLETAR: corregida / aceptada>> |
| 6 | <<COMPLETAR>> | <<COMPLETAR>> | Revisión del `.puml` exportado frente a `contexto-manual.puml` (opcional) | <<COMPLETAR>> | <<COMPLETAR>> | <<COMPLETAR>> |

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

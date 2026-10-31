# Bitácora de uso de IA — Laboratorio 07 (Patrones de diseño)

Regla de trabajo: **la IA propone, el equipo decide y verifica**. Ningún patrón entró al código sin un
olor concreto, pruebas en verde antes y después, una métrica que mostrara la mejora y un registro aquí.
No se ingresaron datos personales, credenciales ni claves de API en los prompts: los nombres, celulares
y montos de los ejemplos son ficticios, y los SDK y LLM están simulados.

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Verificación del equipo | Decisión |
|---|-------|-------------|------------------|-------------------|-------------------------|----------|
| 1 | 25/10 | Claude | Generar la versión antes del flujo «confirmar y pagar» desde `secuencia-confirmar-pagar.puml` (Lab 05), con SDK simulados de interfaces distintas | `antes/servicio.py` (1 archivo) y `externos.py` (Yape en soles con diccionario; Plin en céntimos con tupla; dos LLM con interfaces distintas) | Se escribieron 22 pruebas de caracterización. Una de ellas descubrió que un medio de pago desconocido deja el pedido en `PENDIENTE_PAGO` con el stock reservado | Aceptada; el error se documenta como `xfail` en la versión antes |
| 2 | 25/10 | Claude | Prompt IA 1: detector de olores sobre `antes/servicio.py` y la salida de radon (complejidad 29) | 14 propuestas: 9 olores con patrón y 5 patrones extra (Singleton, Abstract Factory, Builder, Command, LLM juez) | Se contrastó cada olor con las líneas del código y con los cambios previstos (R-05: Plin) | 9 aceptadas y 5 rechazadas (`olores.md`) |
| 3 | 25/10 | Claude | Prompt IA 2: aplicar ÚNICAMENTE Strategy + Adapter + Factory a los pagos | Adaptadores, fábrica por registro y servicio sin `if/elif` por medio | Las pruebas de caracterización de pagos, estados y delivery pasan en ambas versiones (las de IA se activan en E5); la Factory valida el medio antes de tocar el pedido, así que la prueba `xfail` pasa en la versión después | Aceptada. Por decisión del equipo, los reintentos quedan temporalmente en los adaptadores (paso pequeño) y se extraen en E4 |
| 4 | 25/10 | Claude | Reemplazar los condicionales de estado por el patrón State | El código del Lab 05 ya tenía una tabla de transiciones (`_transicion(desde, hacia)`); la IA ofreció mantenerla o pasar a State | La tabla funcionaba, pero los estados tienen comportamiento propio (reservar y liberar stock, anular subpedidos, reembolsar) | Se eligió State; las 11 pruebas de la máquina del Lab 05 se adaptaron y pasan |
| 5 | 25/10 | Claude | Prueba exploratoria con kilos fraccionados (0,75 kg × S/ 3,50) en ambas versiones | — | La prueba mostró que Yape recibía S/ 2,625 y Plin 262 céntimos: montos distintos para el mismo pedido | **Corrección detectada por las pruebas:** `Pedido.total()` redondea al céntimo; nueva prueba `test_los_montos_se_redondean_al_centimo` |
| 6 | 25/10 | Claude | E4: Observer para los avisos, Decorator para los reintentos, Composite para el pedido multipuesto y Strategy para la tarifa | Primera idea: que `ServicioPedidos` creara por defecto sus suscriptores (WhatsApp y reparto) | `reparto` ya depende de `pedidos`, así que `pedidos` importando `reparto` crea un ciclo (regla C4, ADR-004) | Corregida: el publicador va en `comun`, los suscriptores en sus módulos y la conexión en `arranque.py` |
| 7 | 25/10 | Claude | E5: aislar la normalización de nombres con Strategy + Adapter + caché + guardrails | Cadena de 4 guardrails; como alternativa, validar la respuesta con un segundo LLM | Las reglas deterministas cubren los casos de prueba (precio inventado, producto fuera del catálogo, texto largo, comillas) | Guardrails aceptados; el LLM juez se rechaza por costo y latencia |
| 8 | 25/10 | Claude | Generar un diagrama PlantUML por patrón y actualizar `clases.puml` | 7 diagramas y `clases.puml` actualizado | PlantUML falló en `state.puml` (línea 33: cuerpo de clase en una sola línea con `\n`) | Corregida la sintaxis y regenerados los PNG |
| 9 | 25/10 | Claude | Verificar con pyreverse que el diagrama coincide con el código | — | El diagrama de paquetes mostró imports a módulos internos de otros paquetes (`pagos.pasarelas`, `catalogo.modelos`), prohibidos por ADR-001 | **Corregido el código:** se importa la interfaz pública de cada paquete; 81 pruebas siguen en verde |
| 10 | 25/10 | Claude | Redactar ADR-005, `metricas.md`, la sección del README y el informe | Borradores | Cifras recalculadas con radon y pytest; revisión de ambos integrantes | Aceptada con correcciones |

---

## Anexo: prompts utilizados

### Prompt IA 1 — Detector de olores (interacción 2)

```
Actúa como revisor de código experto en refactorización (Fowler) y patrones GoF.
Contexto: flujo «confirmar y pagar un pedido multipuesto» de San Camilo en Línea (monolito modular
en Django, ADR-001; Yape mediante un proveedor de pagos y Plin previsto en R-05).
[pegar src/pedidos/antes/servicio.py y la salida de radon cc -s -a]
Tarea: identifica los olores de código. Para cada uno indica: líneas, olor, el patrón GoF que lo
resolvería (o "ninguno" si no se justifica), el principio SOLID que mejora y el COSTO de aplicarlo.
Restricciones: no escribas código todavía; no propongas patrones sin un olor concreto; no uses Singleton.
Formato: tabla Markdown.
```

### Prompt IA 2 — Refactor de un solo patrón (interacciones 3, 4, 6 y 7)

```
Aplica ÚNICAMENTE el patrón [Strategy + Adapter + Factory] al siguiente código [pegar].
Reglas: (1) no cambies el comportamiento observable; las pruebas [pegar test_comportamiento.py]
deben seguir pasando; (2) no introduzcas Singleton ni estado global; (3) no agregues patrones que no
te pedí; (4) respeta la regla de dependencias de ADR-004 (pedidos no importa notificaciones ni reparto);
(5) muestra los archivos completos y explica en 3 líneas qué olor elimina.
```

### Prompt IA 3 — Kata adversaria (reto opcional, no ejecutado)

```
Escribe una versión del flujo «confirmar y pagar» con la máxima cantidad de patrones GoF posible.
```

# Bitácora de uso de IA — Laboratorio 05 (Diseño UML)

Regla de trabajo: **la IA propone, el equipo decide y verifica**. No se ingresaron datos personales ni
confidenciales en los prompts: los celulares y nombres de los ejemplos son ficticios.

## Ronda 1 — Primer borrador (Jafet Llave)

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Verificación del equipo | Decisión |
|---|-------|-------------|------------------|-------------------|-------------------------|----------|
| 1 | 06–10/10 | Claude | Prompt IA 1 adaptado a HU-03: diagrama de clases | Clase `Tienda` y agregación débil entre pedido y subpedidos | El dominio habla de *comerciante* y *puesto* (C5); un subpedido no existe sin su pedido | Corregida: `Comerciante` y composición `Pedido *-- PedidoPuesto` |
| 2 | 06–10/10 | Gemini | Diagrama de secuencia del flujo crítico | Llamada síncrona a WhatsApp dentro del cobro | Contradice QA-03 y el outbox de ADR-001 | Corregida: mensaje asíncrono `->>` |
| 3 | 06–10/10 | ChatGPT | Máquina de estados de `PedidoPuesto` | Transiciones descritas en prosa ("cuando el comerciante termina…") | C2 exige operaciones de la clase | Corregida: transiciones con operaciones |
| 4 | 06–10/10 | Antigravity Agent | Prompt IA 2: esqueleto en Python | Código sin control de transiciones de estado | Cualquier método podía ejecutarse en cualquier estado | Corregida: se agregó `EstadoInvalidoError` |
| 5 | 06–10/10 | Antigravity Agent | Prompt IA 3: auditor C1–C5 | Pedía volver síncrona la notificación a WhatsApp | Falso positivo (ver `consistencia.md`, hallazgo 9) | Rechazada |

## Ronda 2 — Revisión y versión final (equipo)

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Verificación del equipo | Decisión |
|---|-------|-------------|------------------|-------------------|-------------------------|----------|
| 6 | 11/10 | Claude | Revisar el borrador completo con las reglas C1–C5, la guía y los ADR del Lab 04 | 8 hallazgos: `buscarPorId` enviado a `Pedido`, stock nunca reservado, 5 operaciones inexistentes en la máquina de estados, subestados sin salida, dos ciclos entre paquetes, módulo "Usuarios" fuera de ADR-001, nombres distintos a ADR-002, `title` de Mermaid que se dibujaba como 8 estados falsos | Se comprobó cada uno contra las imágenes, `clases.puml` y los ADR | Aceptada: hallazgos 1–8 de `consistencia.md` y ADR-004 |
| 7 | 11/10 | Claude | Prompt IA 1 (rehacer el diagrama de clases sin ciclos, con nombres de ADR-002) | Diagrama con 11 clases, 3 puertos, 4 enumeraciones y paquetes por módulo | Multiplicidades en ambos extremos; ningún puerto recibe clases de `pedidos` | Aceptada |
| 8 | 11/10 | Claude | Rehacer secuencia, estados, actividades y paquetes con las correcciones | Cinco diagramas renderizados con PlantUML y mermaid-cli | Se revisaron las imágenes; se quitó la advertencia de `skinparam ParticipantPadding` que aparecía en el PNG | Aceptada |
| 9 | 11/10 | Claude | Prompt IA 2: código Python desde `clases.puml`, con pruebas | Código por módulo y 15 pruebas | `pytest` aprobado; pyreverse confirmó que no hay ciclos | Corregida: `confirmar()` libera lo ya reservado si falla una reserva, y los imports directos a `modelos.py` de otro módulo se cambiaron por su interfaz pública (ADR-001) |
| 10 | 11/10 | Claude | Prompt IA 3 sobre los cinco diagramas finales (aplicación literal de las reglas) | 6 hallazgos (10–15 de `consistencia.md`) | 3 falsos positivos (navegación, creación por composición y dirección de dependencia) y 3 válidos | Parcial: se agregó `procesarWebhookPago()` |
| 11 | 11/10 | Claude | Redacción del informe y de `round-trip.md` | Borrador del informe con E1–E8 y cuestionario | Revisado por ambos integrantes antes de entregar | Aceptada |

---

## Anexo: prompts utilizados

### Prompt IA 1 — Diagrama de clases (interacciones 1 y 7)

```
Actúa como diseñador de software orientado a objetos. Contexto: módulos pedidos, pagos,
catalogo, notificaciones y reparto de un monolito modular en Django (ADR-001: puertos y
adaptadores para integraciones externas; ADR-002: estados separados de pedido y pago,
nombres creado/pagado/cancelado y pendiente/confirmado/rechazado).
Historia y criterios: [pegar docs/design/historia.md].
Tarea: genera un diagrama de clases en PlantUML con atributos tipados y visibilidad,
operaciones, multiplicidades en ambos extremos, enumeraciones para los estados del pedido,
del subpedido y del pago, e interfaces (puertos) para la pasarela de pagos, la mensajería y
el repositorio. Agrupa las clases en un paquete por módulo. Ningún puerto puede recibir
como parámetro una clase de otro módulo (evitar ciclos).
Formato: solo el código PlantUML. No agregues clases que no se deriven de la historia;
si asumes algo, indícalo en un comentario.
```

### Prompt IA 2 — Ingeniería directa (interacciones 4 y 9)

```
Genera el esqueleto en Python 3.10 (dataclasses y type hints) del siguiente diagrama de
clases, con un archivo por módulo (src/<modulo>/). Respeta exactamente los nombres de clases,
atributos y operaciones (en snake_case), las enumeraciones, las interfaces como clases
abstractas (ABC) y las multiplicidades. Cada operación de PedidoPuesto debe validar el estado
de origen y lanzar EstadoInvalidoError si no corresponde. Los adaptadores lanzan
NotImplementedError. Agrega pruebas pytest: una por transición del diagrama de estados.
[pegar clases.puml y estados-pedidopuesto.mmd]
```

### Prompt IA 3 — Auditor de consistencia (interacciones 5 y 10)

```
Actúa como revisor de diseño. Te paso cinco diagramas UML en PlantUML/Mermaid:
[pegar clases.puml, secuencia-confirmar-pagar.puml, estados-pedidopuesto.mmd,
actividades-consolidar-pedido.puml y paquetes.puml].
Verifica estas reglas y responde en una tabla (regla, elemento, problema, corrección sugerida):
C1 cada mensaje de secuencia es una operación de la clase receptora; C2 cada transición de
estados corresponde a una operación de la clase; C3 multiplicidades coherentes con los
criterios de aceptación; C4 paquetes sin ciclos; C5 nombres consistentes.
No reescribas los diagramas; solo reporta hallazgos y cita la línea.
```

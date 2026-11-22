# ADR-010: Arquitectura del sistema agéntico para corregir issues

- Estado: Aceptado
- Fecha: 2026-11-21
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar
- Relacionado con: ADR-005 (Strategy para el «cerebro» del agente), Lab 09 (prompts como código y grabaciones)

## Contexto

Queremos que un agente de IA ayude a corregir errores de San Camilo en Línea sin arriesgar el dinero de
los comerciantes (comisión y abonos) ni el código principal. Cada issue tiene una prueba que falla y que
define «resuelto». No usamos clave de API: las decisiones del modelo se graban (como en el Lab 09) y las
herramientas se ejecutan de verdad en un sandbox. Las métricas de los 3 issues están en
`agentes/observacion.md`.

## Alternativas consideradas

1. **Flujo de trabajo fijo** (script que siempre lee, edita y prueba lo mismo): no sirve para issues
   cuyos pasos no se conocen. Sí lo usamos para la liquidación de pedidos, que no se delega a un agente.
2. **Agente único con todas las herramientas y comandos libres:** barato, pero con exceso de agencia
   (OWASP LLM06). En el issue 01 el agente intentó crear una rama con `git`.
3. **Coordinación democrática** (tres revisores que votan): más robusta, pero triplica el costo del
   revisor para issues de una o dos funciones.
4. **Agente de código comercial con acceso completo al repositorio:** no permite ver ni probar la
   política ni el contrato, y requiere credenciales.
5. **ReAct + planificador-ejecutor, actor-crítico con revisor de solo lectura, contrato, política por
   rol y humano revisor:** elegida.

## Decisión

- **Arquetipo:** ReAct para issues acotados (01, 03); planificador + ReAct cuando el cambio toca más de
  una función o dinero (02).
- **Coordinación:** por gestor + actor-crítico con un máximo de 2 rondas. El revisor solo tiene
  `ver_cambios`, `leer_archivo`, `buscar` y `ejecutar_pruebas`.
- **Herramientas:** 7 del mini framework + `mapa_repo` (firmas con `ast`) + memoria de notas. Rutas
  limitadas al sandbox; `editar_archivo` exige un fragmento exacto.
- **Memoria:** historial de la tarea (corto plazo) y `notas.md` (pizarra), sin memoria entre ejecuciones.
- **Límites:** contrato JSON validado antes de actuar; 12 pasos para el ejecutor y 8 para el revisor;
  `tests/` protegida; comandos en lista permitida (`pytest`, `radon cc`, `lint-imports`, `git status/diff`).
- **Rol humano:** revisor. Aprueba cada edición (`--humano`, solo «s» o «n»), aplica el cambio al
  repositorio (`--aplicar`) y aprueba el Pull Request. Ningún agente fusiona su propio cambio.

## Consecuencias

- (+) Los 3 issues se resolvieron con las pruebas en verde y sin tocar `tests/`.
- (+) El revisor encontró lo que el agente único pasó por alto (la búsqueda del issue 02).
- (+) La política bloqueó la acción fuera de rol y la traza la deja auditada.
- (+) Las trazas JSONL generan el diagrama de la trayectoria y las métricas automáticamente.
- (−) El actor-crítico cuesta ~2,8 veces más contexto que el agente único (14 179 frente a 4 986 caracteres).
- (−) `mapa_repo` no redujo el contexto en un sandbox pequeño (issue 03); conviene en repositorios grandes.
- (−) Aprobar cada edición es lento: es el precio de la etapa «revisor» (`agentes/delegacion.md`).
- (−) Las decisiones grabadas no prueban cómo se comportaría otro modelo; para eso habría que usar `ModeloAnthropic` con clave.

# Bitácora de IA — Laboratorio 10 (sistemas agénticos)

Asistente: **Claude** (Anthropic), usado como «cerebro» del agente en modo interactivo (`ModeloInteractivo`:
el contexto se copió al asistente y su respuesta JSON quedó grabada en `trayectorias/` sin editarla) y como
apoyo para el diseño. Las herramientas (pytest, radon, edición de archivos) se ejecutaron de verdad en el
sandbox `agentes/trabajo/`. No se usó clave de API.

| # | Fecha | Para qué | Qué propuso la IA | Qué hicimos / evidencia |
|---|-------|----------|-------------------|-------------------------|
| 1 | 21/11 | E1: lienzo de diseño | Separar qué conviene a un agente y qué a un flujo fijo | **Aceptado:** agente para corregir issues (hay que explorar el código); flujo fijo para liquidar pedidos (siempre los mismos pasos, auditable). Decisión 1 del lienzo. |
| 2 | 21/11 | E2: issue 01 (ReAct) | En el paso 5, crear una rama con `git checkout -b fix/issue-01` | **Bloqueado por la política** (solo `git status/diff`). El agente siguió en el sandbox y lo reportó al humano. Traza: `trazas/issue-01/unico/ejecutor.jsonl`, paso 5. |
| 3 | 21/11 | E3: contrato | Decisiones inválidas típicas de un asistente (campo extra `confianza`, `args` como texto, acción vacía, comando en lugar de herramienta, lista en lugar de objeto) | **Aceptado** como 7 casos de prueba propios; el contrato rechaza las 7. `pruebas_agente/test_agente.py`. |
| 4 | 21/11 | E4: issue 03 | Primer arreglo con `quantize(CENTIMO)` sin modo de redondeo | **Error del agente detectado por la prueba del issue**: redondeo bancario (0.125 → 0.12) dio 2.38 en vez de 2.37. El agente lo anotó en `notas.md` y usó `ROUND_HALF_UP`. |
| 5 | 21/11 | E4: herramienta nueva | Diseño de `mapa_repo` con el módulo `ast`: solo firmas y primera línea del docstring | **Aceptado.** Una prueba verifica que el cuerpo de las funciones no aparece en el mapa. |
| 6 | 21/11 | E5: issue 02 (agente único) | Corregir solo `productos_visibles()` | **Incompleto**, con las pruebas en verde. El **revisor** (actor-crítico) encontró `buscar_productos()` con el criterio antiguo y pidió cambios. |
| 7 | 21/11 | E5: ronda 2 | Que `buscar_productos()` reutilice `productos_visibles()` | **Aceptado**: un solo criterio de visibilidad. El humano agregó `test_busqueda_tampoco_muestra_agotados`. |
| 8 | 21/11 | E6: humano en el circuito | Aprobación por consola que solo acepta «s» o «n» y que, sin respuesta válida, no edita | **Aceptado.** Prueba manual en `trazas/issue-01/humano/consola.txt` (se respondió «tal vez» y el sistema volvió a preguntar) y 4 pruebas automáticas. |
| 9 | 21/11 | E7: observación | Medir si mapa y notas redujeron pasos o contexto frente a E2 | **Resultado matizado:** menos archivos leídos, pero más contexto (10 033 frente a 7 181 caracteres). Se dejó escrito así en `observacion.md`. |

Ningún prompt, trayectoria ni traza contiene datos personales reales, credenciales ni claves de API.

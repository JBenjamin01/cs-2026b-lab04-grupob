# Lienzo de diseño del sistema agéntico — San Camilo en Línea (Lab 10, E1)

Tareas del agente: los 3 issues de `issues/` (comisión doble, producto agotado visible y redondeo en
céntimos). Cada issue tiene una prueba que falla en `tests/test_issue_0N_*.py`: es la definición
objetiva de «resuelto» (la misma idea de SWE-bench).

| # | Decisión de diseño | Elección para San Camilo en Línea | Justificación |
|---|--------------------|-----------------------------------|---------------|
| 1 | ¿Agente o flujo de trabajo? | **Agente** para corregir issues; **flujo fijo** para cobrar y liquidar | Para encontrar la causa hay que explorar el código y los pasos no se conocen de antemano (Sección 1.1). Liquidar un pedido, en cambio, siempre sigue los mismos pasos: ahí un flujo fijo es más barato, predecible y auditable, y no se usa un agente. |
| 2 | Arquetipo | **ReAct** (issues 1 y 3) y **planificador-ejecutor + ReAct** (issue 2) | ReAct sirve para explorar el repositorio y localizar un error (Tabla 3). En el issue 2 el plan corto del planificador deja explícito qué revisar después (vitrina y búsqueda), lo que facilita depurar y revisar. |
| 3 | Herramientas | `listar_archivos`, `leer_archivo`, `buscar`, `ejecutar_pruebas`, `editar_archivo`, `ver_cambios`, `ejecutar_comando` (lista permitida); en E4 se agregan `mapa_repo`, `anotar` y `leer_notas` | Lo mínimo para leer, cambiar y verificar (Tabla 5). `editar_archivo` exige un fragmento exacto, que es más seguro que «ejecutar cualquier comando». |
| 4 | Memoria | Corto plazo (historial de la tarea) + **notas** (`notas.md`) desde E4 | Las tareas son cortas. Las notas guardan hipótesis y archivos revisados sin releer todo el código (Tabla 6). |
| 5 | Coordinación | **Por gestor** (planificador) + **actor-crítico** (ejecutor y revisor de solo lectura) | Quien cambia el código no se revisa a sí mismo. El revisor no puede editar (mínimo privilegio, Sección 1.7). En E5 se compara con un agente único (parsimonia). |
| 6 | Rol humano | **Revisor**: aprueba cada edición en la consola (s/n) y aprueba el Pull Request | Primer uso del sistema con dinero de los comerciantes (comisión y abonos): la confianza todavía es baja (Sección 1.8). |
| 7 | Control | Contrato JSON de cada decisión; política por rol; `tests/` protegida; comandos en lista permitida; máximo 12 pasos (ejecutor), 8 (revisor) y 2 rondas | Evita acciones indebidas (exceso de agencia, OWASP LLM06), bucles infinitos y costos sin límite. El agente no puede «arreglar» las pruebas para que pasen. |

## Issues

| Issue | Módulo | Prueba que falla | Arquetipo y coordinación | Entregable |
|-------|--------|------------------|--------------------------|------------|
| 01 Comisión cobrada dos veces | `src/pedidos/liquidacion.py` | `test_issue_01_pedido_a_dos_puestos_cobra_una_sola_comision` | ReAct, agente único | E2 |
| 02 Producto agotado visible | `src/catalogo/vitrina.py` | `test_issue_02_producto_agotado_no_aparece_en_la_vitrina` | Agente único **y** planificador + actor-crítico | E5 |
| 03 Redondeo en céntimos | `src/pedidos/liquidacion.py` | `test_issue_03_abonos_mas_comision_suman_el_total` | ReAct con `mapa_repo` y notas | E4 |

Lo que **no** se delega al agente: fusionar el Pull Request, tocar `tests/`, ejecutar comandos fuera de la
lista permitida y cualquier acción con credenciales o datos reales de comerciantes.

# E6 — Humano en el circuito y delegación progresiva (San Camilo en Línea)

## Aprobación humana de ediciones (activa)

`python orquestador.py 01 --humano` activa `aprobar_edicion` en la política del **ejecutor** (el único
agente que puede editar). Antes de cada `editar_archivo`, `agente/humano.py` muestra la ruta, el fragmento
anterior y el nuevo, y pregunta `¿Aprueba esta edición? [s/n]`. Solo acepta «s» o «n» (mayúsculas y
espacios se normalizan); cualquier otra respuesta se vuelve a preguntar hasta 5 veces y, si no hay
respuesta válida, **no se edita**. Un «n» llega al agente como observación «El revisor humano rechazó la
edición». Evidencia: `trazas/issue-01/humano/consola.txt` (se respondió «tal vez», el sistema lo rechazó,
y luego «s»). Pruebas: 4 en `pruebas_agente/test_agente.py` (sección E6).

## Hoja de ruta: de ejecutor a gobernador

| Etapa (rol humano) | Qué hace el humano | Permisos del agente en San Camilo en Línea | Evidencia de las trazas para pasar a la siguiente etapa |
|--------------------|--------------------|--------------------------------------------|---------------------------------------------------------|
| 1. **Ejecutor** | Hace el cambio; el agente solo sugiere | Solo lectura: `leer_archivo`, `buscar`, `mapa_repo`, `ejecutar_pruebas` | 10 issues en los que el diagnóstico del agente (archivo y causa) coincide con el arreglo humano; 0 intentos de acciones fuera de su rol |
| 2. **Revisor** (hoy) | Aprueba cada edición (s/n) y el Pull Request | Edita fuera de `tests/` con aprobación por edición; comandos en lista permitida; máx. 12 pasos; revisor de solo lectura en cambios de dinero o stock | 20 ejecuciones seguidas con 0 ediciones rechazadas por el humano, 0 bloqueos por comandos peligrosos y 0 defectos encontrados después en módulos de pagos o liquidación |
| 3. **Colaborador** | Revisa el Pull Request completo, no cada edición | Edita sin aprobación por edición en `catalogo/` y `notificaciones/`; en `pagos/` y `pedidos/liquidacion` sigue pidiendo aprobación; abre el PR en una rama nueva | 3 meses sin regresiones atribuibles al agente; el revisor-agente detecta lo mismo que el humano en al menos el 90 % de los PR muestreados |
| 4. **Gobernador** | Define políticas, límites y presupuestos; audita trazas por muestreo | Resuelve issues de baja severidad de punta a punta (rama, pruebas, PR); **nunca** fusiona en `main` ni toca credenciales, datos reales de comerciantes ni la configuración de comisiones | Métricas de las trazas estables por trimestre (pasos, bloqueos, contexto) y auditorías sin hallazgos graves |

**Hoy dejamos al agente en la etapa 2 (revisor).** En nuestras trazas el agente intentó crear una rama
con `git` (issue 01) y entregó un arreglo incompleto con las pruebas en verde (issue 02, agente único): son
señales de que todavía necesita aprobación humana por edición. Los cambios de comisión y abonos tocan
dinero de los comerciantes, por eso son los últimos en delegarse.

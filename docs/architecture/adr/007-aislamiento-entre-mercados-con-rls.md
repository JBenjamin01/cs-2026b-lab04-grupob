# ADR-007: Aislamiento entre mercados con mercado_id, Row-Level Security y el claim del token

- Estado: Aceptado
- Fecha: 2026-10-29
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar
- Relacionado con: ADR-002 (un esquema por módulo), ADR-006, iteración 2 de ADD

## Contexto

Con 3 mercados en la misma base de datos, un comerciante o administrador de Altiplano no debe ver
nunca los pedidos, ventas ni datos de clientes de San Camilo o Río Seco (QA-05, (H,M)). La
evaluación ATAM-lite de la iteración 1 lo marcó como riesgo crítico (R1). ADR-002 ya organiza la
base con un esquema por módulo, y QA-04 exige un p95 ≤ 2 s con 20 req/s.

## Alternativas consideradas

1. **Una base de datos por mercado:** operación compleja para 2 developers en un VPS.
2. **Un esquema por mercado:** choca con el esquema por módulo de ADR-002 (serían 18 esquemas).
3. **Columna `mercado_id` con filtro solo en la aplicación:** medido en PostgreSQL 16, un reporte que
   olvida el filtro expone entre 15 028 y 23 971 filas de otros mercados.
4. **`mercado_id` + filtro en la aplicación + Row-Level Security + claim en el token:** elegida.

## Decisión

- Toda tabla con datos de un mercado tendrá la columna `mercado_id` y una política RLS forzada
  (`ENABLE` y `FORCE ROW LEVEL SECURITY`) que compara con `current_setting('app.mercado_id', true)`
  ([`db/rls.sql`](../../../db/rls.sql)).
- La aplicación se conecta con un rol que **no** es dueño de las tablas ni tiene `BYPASSRLS`.
- El token de sesión lleva el claim `mercado`. Un middleware de Django abre la transacción y ejecuta
  `set_config('app.mercado_id', <claim>, true)`; si falta el claim, la consulta no ve filas (falla
  cerrado).
- Cada tabla con `mercado_id` lleva un índice que empieza por esa columna.
- La fitness function **FF-06** se ejecuta en CI contra un PostgreSQL de pruebas: 0 filas ajenas, 0
  filas sin mercado y ninguna tabla con `mercado_id` sin RLS forzado.

## Evidencia

| Variante | Filas ajenas visibles | p95 de la consulta frecuente |
|----------|-----------------------|------------------------------|
| Solo filtro en la aplicación | 15 028 a 23 971 | 0,19 ms |
| RLS + índice | 0 | 0,21 ms |
| RLS sin índice | 0 | 5,63 ms |

Con RLS + índice, la simulación del catálogo da un p95 de 209 ms a 20 req/s (QA-04 se cumple).
Detalle en [`add/iteracion-2.md`](../add/iteracion-2.md).

## Consecuencias

- **Positivas:** un olvido en una consulta ya no expone datos de otro mercado; agregar un mercado no
  crea bases ni esquemas (QA-07).
- **Negativas / riesgos:**
  - Configuración delicada: una tabla nueva sin política, o un rol con `BYPASSRLS`, anula la
    protección (riesgo R5); por eso FF-06 revisa el catálogo de PostgreSQL en cada Pull Request.
  - Las consultas dependen del índice por mercado (punto de sensibilidad: ×27 sin índice).
  - Los reportes globales del equipo (por ejemplo, la comisión de los 3 mercados) necesitan un rol
    separado con `BYPASSRLS`, usado solo desde tareas internas y nunca desde la API.

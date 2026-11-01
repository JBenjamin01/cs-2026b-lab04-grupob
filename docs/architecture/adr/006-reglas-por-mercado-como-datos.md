# ADR-006: Las reglas de cada mercado se guardan como datos, no como código

- Estado: Aceptado
- Fecha: 2026-10-28
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar
- Relacionado con: ADR-001 (monolito modular), ADR-005 (Strategy de tarifas), iteración 1 de ADD

## Contexto

Se suman los mercados Altiplano y Río Seco, cada uno con sus propias reglas: pedido mínimo, medios
de pago aceptados, zonas y costos de delivery, comisión de la plataforma y horario. El árbol de
utilidad prioriza QA-07 (H,H): incorporar un mercado en ≤ 1 día-persona, con 0 líneas de código y
sin desplegar; y QA-08 (H,M): que el administrador de un mercado cambie una regla sin despliegue y
sin afectar a los demás. El plazo sigue siendo de 1 mes con 2 developers (R-01, R-02).

## Alternativas consideradas

1. **Un despliegue por mercado:** triplica el costo del VPS (R-03) y la operación.
2. **`if/elif` por mercado en el código:** se prototipó en una rama descartada. Incorporar Altiplano
   cambió 3 archivos y 54 líneas; Río Seco, 2 archivos y 11 líneas; cada mercado suma 3 condicionales
   y un despliegue, y se rompieron 2 pruebas del Lab 07.
3. **Motor de reglas genérico (DSL):** sobreingeniería para 6 valores por mercado.
4. **Reglas como datos validados (módulo Mercados) + Strategy de tarifas del Lab 07:** elegida.

## Decisión

- Crearemos el módulo `mercados` (app de Django) con la entidad `ReglasMercado` y el puerto
  `RepositorioMercados`. En producción, las reglas se guardan en la tabla `mercados_mercado`,
  editable desde el administrador de Django, y se cachean como máximo 5 min.
- Cada pedido guarda el código de su mercado. `ServicioPedidos` aplica las reglas de ese mercado
  (pedido mínimo, medios, tarifa de delivery y comisión) sin preguntar nunca qué mercado es.
- Los datos se **validan antes de guardarse** (comisión entre 0 y 15 %, montos no negativos, al
  menos un medio de pago, horario coherente, código en mayúsculas).
- Dependencias: `mercados` está en la misma capa que `catalogo`, `pagos` y `notificaciones`; solo
  depende de `comun` (FF-01).
- La fitness function **FF-03** falla si aparece en `src/` cualquier comparación `mercado == "..."`,
  y **FF-05** verifica que un mercado nuevo funcione solo con datos.

## Evidencia

| Medida | `if/elif` | Reglas como datos |
|--------|-----------|-------------------|
| Condicionales por mercado con 3 mercados | 10 | 0 |
| Líneas de código para incorporar Río Seco | 11 + despliegue | 0, sin despliegue |
| Costo único | — | 101 líneas (SLOC) del módulo `mercados` |

Detalle en [`add/iteracion-1.md`](../add/iteracion-1.md).

## Consecuencias

- **Positivas:** QA-07 y QA-08 se cumplen; un cuarto mercado cuesta 0 líneas de código; el principio
  abierto/cerrado de la Factory de pagos (Lab 07) se conserva.
- **Negativas / riesgos:**
  - Un error en los datos ya no pasa por revisión de código ni por las pruebas (riesgo R3). La
    validación atrapa los valores imposibles, pero no los válidos y equivocados (por ejemplo,
    comisión de 5 % en vez de 4 %). Pendiente: registro de auditoría de cambios de reglas.
  - Una regla que no sea un valor (por ejemplo, «envío gratis los martes») requerirá código nuevo;
    se agregará como un campo más solo cuando un mercado la pida.

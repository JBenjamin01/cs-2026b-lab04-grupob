# Evaluación ATAM-lite — San Camilo en Línea 2.0 (E3, Lab 08)

Primera ronda, en la sesión de laboratorio, sobre el árbol de utilidad y la iteración 1 de ADD.
Tuvo dos fuentes:

1. **Evaluación cruzada (E3):** otro grupo revisó el repositorio y abrió un issue (sección 3).
2. **Evaluador adversario (Prompt IA 3):** la IA actuó como evaluador escéptico; cada hallazgo se
   verificó contra la evidencia de la iteración 1.

## 1. Prompt usado (Prompt IA 3)

```
Actúa como evaluador ATAM escéptico. Te paso el árbol de utilidad, la iteración 1 de ADD y su
evidencia [pegar]. Para cada escenario (H,*) identifica: puntos de sensibilidad, puntos de
trade-off, riesgos y no riesgos. Para cada riesgo indica probabilidad e impacto (1 a 5) y una
pregunta incómoda que el equipo debería poder responder. No propongas rediseños completos;
cita la evidencia que te falta.
```

## 2. Hallazgos de la primera ronda

| Tipo | Hallazgo | Respuesta del equipo |
|------|----------|----------------------|
| Sensibilidad | QA-07 depende de que los datos de un mercado se validen antes de guardarse | Confirmado: 5 configuraciones inválidas se rechazan (`test_una_configuracion_invalida_se_rechaza_antes_de_guardarse`) |
| Trade-off | Reglas como datos: mejora la modificabilidad, pero un cambio de regla ya no pasa por revisión de código | Aceptado; se registra como riesgo R3 |
| Riesgo R1 (P 4, I 5) | Sin aislamiento, un usuario de un mercado ve los pedidos de otro. «¿Qué impide que un reporte olvide el filtro por mercado?» | **Crítico:** se mitiga en la iteración 2 (QA-05) |
| Riesgo R2 (P 4, I 4) | Con el código del Lab 07, si el proveedor no responde, `ConReintentos` devuelve EXPIRADO y el pedido **se cancela**. «¿Cuántos pedidos se pierden si el proveedor cae 10 min un sábado?» | **Crítico:** se mitiga en la iteración 3 (QA-09) |
| Riesgo R3 (P 3, I 4) | Una regla mal escrita se publica sin despliegue ni revisión | Validación al guardar; falta un registro de auditoría |
| Riesgo R4 (P 3, I 5) | Un solo VPS es punto único de falla de los 3 mercados | Aceptado para el plazo de 1 mes: respaldo diario y plan de recuperación en ≤ 2 h |
| No riesgo | El monolito modular soporta la carga de 3 mercados | Cálculo preliminar: 20 req/s × 0,11 s / 5 workers = 0,44 de utilización; se confirmará con simulación en la iteración 2 |

## 3. Evaluación cruzada recibida (E3)

> **Completar en la sesión de laboratorio** con el issue que abrió el grupo evaluador en este
> repositorio. Copien cada hallazgo y respondan si lo aceptan o lo refutan con evidencia.

- Grupo evaluador: `[grupo]` · Issue: `#[número]` · Fecha: `[fecha]`

| Tipo | Hallazgo del grupo evaluador | ¿Aceptado? | Respuesta del equipo (con evidencia) |
|------|------------------------------|------------|--------------------------------------|
| Sensibilidad | `[...]` | `[sí/no]` | `[...]` |
| Trade-off | `[...]` | `[sí/no]` | `[...]` |
| Riesgo (P, I) | `[...]` | `[sí/no]` | `[...]` |
| Riesgo (P, I) | `[...]` | `[sí/no]` | `[...]` |
| No riesgo | `[...]` | `[sí/no]` | `[...]` |

## 4. Evaluación entregada a otro grupo (E3)

- Repositorio evaluado: `[enlace]` · Issue abierto: `[enlace]`

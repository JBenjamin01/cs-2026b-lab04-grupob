# No determinismo (Lab 09, E7)

Se ejecutó el mejor prompt de la Tarea A de ese momento (**criterios v3**) **3 veces** sobre los mismos
3 casos (H1 normal, H7 ambigua y H9 adversaria), cada vez en un chat nuevo con el mismo modelo
(Claude Sonnet). `python prompts/no-determinismo/comparar.py` compara las tres respuestas:

| Caso | ¿Textos idénticos? | Contrato válido | invest_ok en las 3 | Preguntas / escenarios | Tipos de escenario | Similitud del texto |
|------|--------------------|-----------------|--------------------|------------------------|--------------------|---------------------|
| H1 | No | 3/3 | false, false, false | 3 / 0 en las 3 | — | 0,38 a 0,57 |
| H7 | No | 3/3 | false, false, false | 3 / 0 en las 3 | — | 0,30 a 0,60 |
| H9 | No | 3/3 | true, true, true | 2 / 3 en las 3 | borde, error y éxito en las 3 | 0,26 a 0,46 |

**En 5 líneas.**
1. Ninguna de las 9 respuestas se repitió palabra por palabra: la similitud del texto entre ejecuciones fue de solo 0,26 a 0,60.
2. Lo que el código consume no cambió: el contrato se cumplió 9/9 y la decisión INVEST, la cantidad de preguntas y escenarios y sus tipos fueron iguales en las 3 ejecuciones; en H9 cambiaron los títulos de los escenarios.
3. Por eso las aserciones deben verificar estructura y decisiones, no el texto exacto: una prueba que compare contra una respuesta literal fallaría al azar.
4. Una grabación es **una muestra**: si se regraba, el texto cambia y la evaluación puede cambiar; por eso se versionan y no se editan, y conviene regrabar varias veces antes de declarar una mejora.
5. El experimento encontró además un error real: H1 (una historia válida) fue rechazada **en las 3 ejecuciones** y la evaluación no lo había detectado (la aserción A2 aceptaba cualquier rechazo); se agregó A7 y nació la v3.1.

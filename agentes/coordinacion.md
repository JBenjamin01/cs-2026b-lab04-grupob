# E5 — Coordinación: agente único frente a actor-crítico (issue 02)

El issue 02 (producto agotado visible) se resolvió dos veces con las mismas herramientas y la misma
política del ejecutor:

```bash
python orquestador.py 02                        # agente único  -> trazas/issue-02/unico/
python orquestador.py 02 --modo actor-critico   # planificador + ejecutor + revisor -> trazas/issue-02/multi/
```

| Variante | Agentes | Rondas | Acciones (incl. respuesta final) | Bloqueadas | Rechazadas por el contrato | Contexto final total | Contexto del agente más cargado | ¿Corrigió la búsqueda? |
|----------|---------|--------|----------------------------------|------------|----------------------------|----------------------|---------------------------------|------------------------|
| Agente único | ejecutor | 1 | 7 | 0 | 0 | 4 986 caracteres (~1 246 tokens) | 4 986 (ejecutor) | **No** |
| Actor-crítico | planificador, ejecutor, revisor (×2 rondas) | 2 | 19 | 0 | 0 | 14 179 caracteres (~3 545 tokens) | 5 214 (ejecutor, ronda 1) | **Sí** |

Datos: `trazas/issue-02/<variante>/resumen.json`, generados por el orquestador a partir de las trazas.

**¿Encontró el revisor algo que el agente único pasó por alto?** Sí. El agente único corrigió
`productos_visibles()` y terminó con las pruebas en verde, pero `buscar_productos()` repetía el criterio
antiguo: la búsqueda seguía mostrando la papa agotada. Las pruebas no lo detectaron porque ninguna
ejercitaba la búsqueda. El revisor (solo lectura) buscó `disponible` en el código, encontró la segunda
función y pidió cambios. En la ronda 2 el ejecutor hizo que la búsqueda reutilice `productos_visibles()`.
El humano agregó después la prueba `test_busqueda_tampoco_muestra_agotados`, porque el agente no puede tocar `tests/`.

## Conclusión (parsimonia)

El actor-crítico costó 2,8 veces más contexto (14 179 frente a 4 986 caracteres) y 2,7 veces más acciones
(19 frente a 7) para un issue de una línea. Aun así, en San Camilo en Línea **sí** compensó en este caso:
el agente único entregó un arreglo incompleto con las pruebas en verde, que es el peor tipo de error
porque parece terminado. El costo extra es pequeño en términos absolutos (unos 2 300 tokens más) frente
a lo que cuesta que un cliente pague un producto agotado. Por el principio de parsimonia no usaríamos
actor-crítico en todo: para issues acotados con buena cobertura de pruebas (como el 01 y el 03), un
agente único más las pruebas basta. Lo reservamos para cambios que tocan dinero, stock o más de una
función, donde un revisor de solo lectura agrega una mirada independiente a bajo costo.

# Fitness functions: comprobación con violaciones (E5, Lab 08)

Las fitness functions solo sirven si **fallan** cuando la arquitectura se degrada. Para comprobarlo
se introdujeron tres violaciones típicas en una rama (`demo/violacion-ff`), se ejecutaron las
fitness functions, se guardó la salida y se revirtió la rama.

| # | Violación introducida | Regla que rompe | Fitness function que la detecta |
|---|-----------------------|-----------------|---------------------------------|
| 1 | `src/catalogo/ia.py`: `from pedidos import Pedido` («atajo temporal: sugerir productos según el último pedido») | Capas sin ciclos (ADR-001, ADR-004) | FF-01 (lint-imports) |
| 2 | `src/reparto/suscriptores.py`: `from pagos.adaptadores import YapeAdapter` («atajo temporal: reembolso directo») | Solo el arranque conoce los adaptadores (ADR-005) | FF-02 (lint-imports) |
| 3 | `src/pedidos/servicio.py`: `if pedido.mercado == "RIO_SECO" and medio == "PLIN":` («promoción de Río Seco») | Reglas por mercado como datos (ADR-006) | FF-03 (pytest) |

## Inventario de fitness functions

| ID | Tipo | Qué verifica | Escenario o ADR | Herramienta |
|----|------|--------------|-----------------|-------------|
| FF-01 | Estructural | Capas `reparto → pedidos → {catalogo, pagos, notificaciones, mercados} → comun`, sin ciclos | ADR-001, ADR-004 | import-linter |
| FF-02 | Estructural | Ningún módulo de dominio importa `pagos.adaptadores`; y ese módulo existe | ADR-005 | import-linter + pytest |
| FF-03 | Estructural | 0 comparaciones `mercado == "..."` en `src/` | QA-07, ADR-006 | pytest (AST) |
| FF-04 | Calidad | p95 del catálogo ≤ 2 s a 20 req/s con RLS + índice, sin caché | QA-04 | pytest + simulación M/G/c |
| FF-05 | Calidad | Un mercado que el código nunca vio funciona solo con datos | QA-07 | pytest |
| FF-06 | Calidad | 0 filas de otro mercado, 0 filas sin mercado y RLS forzado en toda tabla con `mercado_id` | QA-05, ADR-007 | pytest + PostgreSQL 16 |
| FF-07 | Calidad | 0 pedidos perdidos con una caída de 10 min del proveedor | QA-09, ADR-008 | pytest + Monte Carlo |
| FF-08 | Calidad | El circuito reduce las llamadas al proveedor caído a menos de un tercio | QA-09, ADR-008 | pytest + Monte Carlo |
| FF-09 | Modelo | `workspace.dsl` es válido | Lab 06 | structurizr validate |

## Salida real de `lint-imports` con las violaciones 1 y 2

```text
Contracts
---------

Analyzed 30 files, 46 dependencies.
-----------------------------------

FF-01 Capas del monolito modular sin ciclos (ADR-001, ADR-004) BROKEN
FF-02 Solo el arranque conoce los adaptadores de pago (ADR-005) BROKEN

Contracts: 0 kept, 2 broken.


----------------
Broken contracts
----------------

FF-01 Capas del monolito modular sin ciclos (ADR-001, ADR-004)
--------------------------------------------------------------

catalogo is not allowed to import pedidos:

- catalogo.ia -> pedidos (l.140)


FF-02 Solo el arranque conoce los adaptadores de pago (ADR-005)
---------------------------------------------------------------

reparto is not allowed to import pagos.adaptadores:

-   reparto.suscriptores -> pagos.adaptadores (l.18)


```

## Salida real de `pytest tests/test_fitness.py` con las tres violaciones

```text
E       AssertionError: assert ['src/pedidos/servicio.py:52'] == []
E         
E         Left contains one more item: 'src/pedidos/servicio.py:52'
E         Use -v to get more diff
E   ImportError: cannot import name 'Comerciante' from partially initialized module 'catalogo' (most likely due to a circular import) (src/catalogo/__init__.py)
FAILED tests/test_fitness.py::test_ff03_ninguna_decision_del_codigo_depende_de_que_mercado_es
FAILED tests/test_fitness.py::test_ff05_un_mercado_nuevo_se_incorpora_solo_con_datos
2 failed, 4 passed, 1 skipped in 0.07s
```

FF-05 también falló, aunque no se tocó el módulo Mercados: la violación 1 creó un **import
circular** (`catalogo → pedidos → catalogo`) y el sistema ni siquiera pudo arrancar. Es la
degradación que FF-01 detecta antes de que llegue a ejecutarse.

## Hallazgo al escribir FF-02 sobre el código del Lab 07

La primera versión del contrato prohibía `pagos.pasarelas`, donde estaban los adaptadores en el
Lab 07, y falló sin ninguna violación introducida (salida completa en
[`ff02-sobre-codigo-lab07.txt`](ff02-sobre-codigo-lab07.txt)):

```text
pedidos is not allowed to import pagos.pasarelas:
-   pedidos.servicio -> pagos (l.25)
    pagos -> pagos.pasarelas (l.3)
```

`pagos/__init__.py` reexportaba `YapeAdapter` y `PlinAdapter`, y la fábrica vivía en el mismo
archivo que los adaptadores, así que `pedidos` dependía de ellos **indirectamente**. Se movieron
los adaptadores a `pagos/adaptadores.py`, que solo importa `arranque.py`.

Además se comprobó que import-linter da por **cumplido** un contrato `forbidden` cuyo módulo
prohibido no existe. Si alguien renombra `pagos/adaptadores.py`, FF-02 dejaría de proteger sin
avisar; por eso `test_ff02_el_modulo_prohibido_existe` verifica que el módulo exista.

## Cómo repetir la comprobación

```bash
git checkout -b demo/violacion-ff
# introducir las 3 violaciones de la tabla
PYTHONPATH=src lint-imports            # FF-01 y FF-02: BROKEN
python -m pytest -q tests/test_fitness.py   # FF-03 y FF-05: FAILED
git checkout main && git branch -D demo/violacion-ff
```

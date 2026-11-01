"""Fitness functions de CALIDAD (Lab 08, E5): los escenarios del árbol de utilidad como pruebas.

Si alguien quita una táctica (el índice, el circuit breaker, las reglas como datos o RLS),
la integración continua falla y el Pull Request no se puede fusionar.
Las fitness functions estructurales FF-01 y FF-02 están en .importlinter (lint-imports).
"""
import importlib.util
import os
from decimal import Decimal
from pathlib import Path

import pytest

from fitness.disponibilidad import simular as simular_pagos
from fitness.modificabilidad import condicionales_por_mercado
from fitness.rendimiento import WORKERS, bd_con_indice, con_rls, simular

RAIZ = Path(__file__).resolve().parents[1]
PRESUPUESTO_P95_MS = 2000          # QA-04: p95 <= 2 s


# ---------------------------------------------------------------- estructurales (complemento)
def test_ff02_el_modulo_prohibido_existe():
    """import-linter da por cumplido un contrato `forbidden` si el módulo prohibido no existe:
    si alguien renombra pagos/adaptadores.py, FF-02 dejaría de proteger sin avisar."""
    assert importlib.util.find_spec("pagos.adaptadores") is not None


def test_ff03_ninguna_decision_del_codigo_depende_de_que_mercado_es():
    """QA-07 (ADR-006): cero comparaciones `mercado == "..."` en src/."""
    assert condicionales_por_mercado(RAIZ / "src") == []


# ---------------------------------------------------------------- calidad
def test_ff04_rendimiento_catalogo_con_tres_mercados():
    """QA-04: 20 req/s en hora pico con 3 mercados, RLS + índice, SIN contar con la caché."""
    r = simular(lam=20, workers=WORKERS, servicio=con_rls(bd_con_indice))
    assert r["p95"] <= PRESUPUESTO_P95_MS, f"p95={r['p95']:.0f} ms excede el presupuesto"


def test_ff05_un_mercado_nuevo_se_incorpora_solo_con_datos():
    """QA-07: un mercado que el código nunca vio funciona con sus reglas, sin escribir código."""
    from arranque import crear_servicio_pedidos
    from catalogo.modelos import Comerciante, Producto
    from mercados import RepositorioMercadosEnMemoria, cargar_datos_iniciales
    from pedidos.pedido import Cliente, Pedido

    nuevo = {"codigo": "MERCADO_PRUEBA", "nombre": "Mercado de prueba", "pedido_minimo": "30",
             "comision": "0.02", "medios_pago": ["PLIN"], "zonas_delivery": {"Sachaca": "7"},
             "tarifa_por_defecto": "10", "delivery_gratis_desde": "500", "abre": "07:00", "cierra": "13:00"}
    repo = RepositorioMercadosEnMemoria(cargar_datos_iniciales() + [nuevo])
    papa = Producto("Papa", Decimal("3.50"), "kg", Decimal("100"), Comerciante("Ana", "P-1", "900000001"))
    p = Pedido(Cliente("Cliente demo", "959000111", "Calle Demo 123"), "DELIVERY", "Sachaca", mercado="MERCADO_PRUEBA")
    p.agregar_linea(papa, Decimal("10"))                                  # S/ 35 >= 30
    assert crear_servicio_pedidos(mercados=repo).servicio.confirmar_y_pagar(p, "PLIN") == "PAGADO"
    assert (p.costo_envio, p.comision) == (Decimal("7"), Decimal("0.70"))


def test_ff06_aislamiento_entre_mercados_en_postgresql():
    """QA-05: con RLS, un reporte que olvida filtrar no ve filas de otros mercados; sin mercado
    en el token no ve nada; y toda tabla con columna mercado_id tiene RLS forzado.
    Necesita un PostgreSQL de pruebas (en GitHub Actions es un servicio del workflow)."""
    dsn = os.environ.get("AISLAMIENTO_DSN")
    if not dsn:
        pytest.skip("Sin AISLAMIENTO_DSN: se ejecuta en GitHub Actions con el servicio postgres")
    from fitness.aislamiento import MERCADOS, conectar, filas_ajenas, preparar
    conn = conectar(dsn)
    preparar(conn, pedidos=3000)
    assert {m: filas_ajenas(conn, m) for m in MERCADOS} == {m: 0 for m in MERCADOS}
    assert filas_ajenas(conn, None) == 0                         # falla cerrado
    sin_rls = conn.execute(
        "SELECT c.relname FROM pg_class c JOIN pg_attribute a ON a.attrelid = c.oid "
        "WHERE a.attname = 'mercado_id' AND c.relkind = 'r' "
        "AND NOT (c.relrowsecurity AND c.relforcerowsecurity)").fetchall()
    conn.close()
    assert sin_rls == [], f"Tablas con mercado_id sin RLS forzado: {sin_rls}"


def test_ff07_cero_pedidos_perdidos_ante_caida_de_10_min_del_proveedor():
    """QA-09: caída total de 10 min en hora pico del sábado."""
    assert simular_pagos("breaker", caida_min=10)["perdidos"] == 0


def test_ff08_el_circuito_protege_al_proveedor_caido():
    """QA-09: durante la caída, el circuito reduce las llamadas a menos de un tercio."""
    assert simular_pagos("breaker")["llamadas_en_caida"] < simular_pagos("reintentos")["llamadas_en_caida"] / 3

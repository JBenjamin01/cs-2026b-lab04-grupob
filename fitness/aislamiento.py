"""Evidencia de la iteración 2 (QA-05): aislamiento entre mercados sobre PostgreSQL REAL.

Carga pedidos de los 3 mercados y ejecuta, como el rol de la aplicación, una consulta con un
error típico: un reporte que OLVIDA filtrar por mercado. Mide cuántas filas de OTROS mercados ve:
  - solo con filtro en la aplicación (sin RLS): el olvido expone todo;
  - con Row-Level Security (db/rls.sql): 0 filas ajenas.
También mide el costo de RLS en la consulta más frecuente (p95 en ms).

Requiere un PostgreSQL de pruebas (¡nunca el de producción!):
    AISLAMIENTO_DSN="postgresql://postgres:postgres@localhost:5432/postgres" python fitness/aislamiento.py
"""
from __future__ import annotations

import os
import random
import statistics
import time
from pathlib import Path

MERCADOS = {"SAN_CAMILO": 0.5, "ALTIPLANO": 0.3, "RIO_SECO": 0.2}   # proporción de pedidos
SQL_RLS = Path(__file__).resolve().parents[1] / "db" / "rls.sql"

# El reporte con el error: no tiene WHERE mercado_id = ...
REPORTE_CON_OLVIDO = "SELECT mercado_id, count(*) FROM pedidos.pedido GROUP BY mercado_id"
# La consulta más frecuente: pedidos recientes de un mercado (panel del comerciante)
CONSULTA_FRECUENTE = ("SELECT id, numero_puesto, total FROM pedidos.pedido "
                      "WHERE mercado_id = %s ORDER BY creado DESC LIMIT 50")


def conectar(dsn: str | None = None):
    import psycopg                      # se importa aquí: el resto del repositorio no lo necesita
    return psycopg.connect(dsn or os.environ["AISLAMIENTO_DSN"], autocommit=True)


def preparar(conn, pedidos: int = 30_000, con_rls: bool = True, con_indice: bool = True, semilla: int = 7) -> None:
    """Crea el esquema desde cero (con o sin RLS, con o sin índice) y carga pedidos de prueba."""
    conn.execute("DROP SCHEMA IF EXISTS pedidos CASCADE")
    conn.execute("DROP ROLE IF EXISTS app_sancamilo")
    sql = SQL_RLS.read_text(encoding="utf-8")
    if not con_rls:                     # alternativa «solo filtro en la aplicación»
        sql = sql.replace("ALTER TABLE pedidos.pedido ENABLE ROW LEVEL SECURITY;", "") \
                 .replace("ALTER TABLE pedidos.pedido FORCE ROW LEVEL SECURITY;", "")
    if not con_indice:                  # para medir el punto de sensibilidad del índice
        sql = sql.replace("CREATE INDEX pedido_mercado_creado ON pedidos.pedido (mercado_id, creado DESC);", "")
    conn.execute(sql)
    rnd = random.Random(semilla)
    codigos, pesos = list(MERCADOS), list(MERCADOS.values())
    filas = [(rnd.choices(codigos, pesos)[0], f"P-{rnd.randint(1, 120)}", f"9{rnd.randint(10**7, 10**8 - 1)}",
              round(rnd.uniform(8, 250), 2), rnd.randint(0, 30 * 24 * 3600)) for _ in range(pedidos)]
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO pedidos.pedido (mercado_id, numero_puesto, celular_cliente, total, creado) "
                        "VALUES (%s, %s, %s, %s, now() - make_interval(secs => %s))", filas)
    conn.execute("ANALYZE pedidos.pedido")


def _como_mercado(conn, mercado: str | None):
    """Lo que hace el middleware en cada petición: rol de la aplicación + mercado del token."""
    conn.execute("RESET ROLE")
    conn.execute("SET ROLE app_sancamilo")
    conn.execute("SELECT set_config('app.mercado_id', %s, false)", (mercado or "",))


def filas_ajenas(conn, mercado: str | None) -> int:
    """Filas de OTROS mercados que ve el reporte con el olvido, actuando como `mercado`."""
    _como_mercado(conn, mercado)
    filas = conn.execute(REPORTE_CON_OLVIDO).fetchall()
    conn.execute("RESET ROLE")
    return sum(n for m, n in filas if m != mercado)


def p95_consulta_ms(conn, repeticiones: int = 400) -> float:
    tiempos = []
    for i in range(repeticiones):
        mercado = list(MERCADOS)[i % 3]
        _como_mercado(conn, mercado)
        t0 = time.perf_counter()
        conn.execute(CONSULTA_FRECUENTE, (mercado,)).fetchall()
        tiempos.append((time.perf_counter() - t0) * 1000)
    conn.execute("RESET ROLE")
    tiempos.sort()
    return tiempos[int(0.95 * (len(tiempos) - 1))]


VARIANTES = {   # nombre: (con_rls, con_indice)
    "Solo filtro en la aplicación": (False, True),
    "RLS + índice (mercado_id, creado)": (True, True),
    "RLS sin índice": (True, False),
}


def medir(dsn: str | None = None, pedidos: int = 30_000) -> dict:
    conn = conectar(dsn)
    r = {}
    for nombre, (con_rls, con_indice) in VARIANTES.items():
        preparar(conn, pedidos, con_rls, con_indice)
        r[nombre] = {
            "ajenas_por_mercado": {m: filas_ajenas(conn, m) for m in MERCADOS},
            "ajenas_sin_mercado": filas_ajenas(conn, None),
            "p95_ms": p95_consulta_ms(conn),
        }
    conn.close()
    return r


if __name__ == "__main__":
    r = medir()
    for clave, v in r.items():
        print(f"{clave:34s} filas ajenas por mercado={v['ajenas_por_mercado']}  "
              f"sin mercado en el token={v['ajenas_sin_mercado']}  p95 consulta frecuente={v['p95_ms']:.2f} ms")

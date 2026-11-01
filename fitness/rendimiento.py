"""Verificación de QA-04 con 3 mercados (análisis de la iteración 2): cola M/G/c del catálogo.

Adaptado de la simulación del docente (AgroConecta). Llegan solicitudes al catálogo (Poisson) y
las atienden los workers de Gunicorn del VPS (2 vCPU -> 2 x 2 + 1 = 5 workers, ADR-001).

Supuestos (ver iteracion-2.md):
- S1 Carga: 200 clientes concurrentes en San Camilo (QA-04, Lab 04) + 120 en Altiplano + 80 en
  Río Seco; cada cliente activo pide el catálogo cada ~20 s -> 10 req/s hoy y 20 req/s con
  3 mercados en hora pico. Se prueba además un margen de x1.5 (30 req/s).
- S2 Tiempos de servicio: los del MVP de AgroConecta (guía del Lab 08), porque San Camilo
  todavía no tiene mediciones propias. Con 3 mercados la tabla triplica sus filas: sin índice
  por mercado, la consulta recorre más filas (+20 %, supuesto conservador).
- S3 RLS: +5 % al tiempo de la consulta (medido con fitness/aislamiento.py: 0,19 -> 0,21 ms en BD).
"""
from __future__ import annotations

import heapq
import random
import statistics

WORKERS = 5


def simular(lam: float, workers: int, servicio, segundos: int = 120, semilla: int = 7) -> dict:
    rnd = random.Random(semilla)
    t, llegadas = 0.0, []
    while t < segundos:
        t += rnd.expovariate(lam)
        llegadas.append(t)
    libres = [0.0] * workers              # instante en que cada worker queda libre
    heapq.heapify(libres)
    respuestas = []
    for a in llegadas:
        libre = heapq.heappop(libres)
        inicio = max(a, libre)
        fin = inicio + servicio(rnd)
        heapq.heappush(libres, fin)
        respuestas.append((fin - a) * 1000)   # ms
    respuestas.sort()
    p = lambda q: respuestas[int(q * (len(respuestas) - 1))]
    return {"n": len(respuestas), "p50": p(0.50), "p95": p(0.95), "media": statistics.mean(respuestas)}


def bd_sin_indice(r):                     # ~0,34 s: consulta que recorre las filas de los 3 mercados
    return r.lognormvariate(-1.35, 0.45) * 1.20


def bd_con_indice(r):                     # ~0,11 s: índice (mercado_id, puesto) del ADR-007
    return r.lognormvariate(-2.30, 0.40)


def con_rls(base, sobrecosto=1.05):
    return lambda r: base(r) * sobrecosto


def con_cache(base, acierto=0.85):        # caché del catálogo en Redis (ADR-001), ~10 ms si acierta
    return lambda r: r.lognormvariate(-4.6, 0.3) if r.random() < acierto else base(r)


CARGAS = [("Hoy: solo San Camilo (10 req/s)", 10), ("3 mercados, hora pico (20 req/s)", 20),
          ("Margen x1,5 (30 req/s)", 30)]

ESCENARIOS = {
    "RLS sin índice": con_rls(bd_sin_indice),
    "RLS + índice": con_rls(bd_con_indice),
    "RLS + índice + caché": con_cache(con_rls(bd_con_indice)),
}

if __name__ == "__main__":
    for carga, lam in CARGAS:
        print(f"\nCarga {carga}, {WORKERS} workers")
        for nombre, f in ESCENARIOS.items():
            r = simular(lam, WORKERS, f)
            print(f"  {nombre:22s} p50={r['p50']:8.0f} ms  p95={r['p95']:8.0f} ms  n={r['n']}")
    print("\nSensibilidad: aciertos de la caché (20 req/s, RLS + índice) -> p95")
    print("  " + "  ".join(f"{a}%: {simular(20, WORKERS, con_cache(con_rls(bd_con_indice), a / 100))['p95']:.0f} ms"
                         for a in (0, 50, 85, 95)))

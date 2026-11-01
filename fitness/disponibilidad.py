"""Evidencia de la iteración 3 (QA-09): Monte Carlo de una jornada de sábado con 3 mercados.

Adaptado de la simulación del docente (AgroConecta) con los datos de San Camilo en Línea:
- Jornada de sábado de 06:00 a 14:00 (480 min) con hora pico de 07:00 a 10:00.
- Pedidos de los 3 mercados por hora (supuesto S1, ver iteracion-3.md): 1 290 en la jornada.
- El proveedor tiene timeouts transitorios (5 %) y una CAÍDA TOTAL de `caida_min` minutos
  que empieza a las 08:30, en plena hora pico (supuesto S2).
- Ventana de pago: un pedido pendiente más de 15 min se cancela (regla del Lab 05).

Tácticas comparadas (las mismas del código):
  "ninguna"    -> un solo intento: cualquier falla cancela el pedido (Lab 06).
  "reintentos" -> ConReintentos, 3 intentos (Lab 07): resiste timeouts, no una caída.
  "breaker"    -> ConReintentos + ConCircuitBreaker (umbral 3, espera 60 s) + outbox (Lab 08).
"""
from __future__ import annotations

import random
from collections import deque

INICIO, FIN = 6 * 60, 14 * 60
PEDIDOS_POR_HORA = {6: 90, 7: 240, 8: 240, 9: 240, 10: 150, 11: 150, 12: 90, 13: 90}
P_TIMEOUT = 0.05
INTENTOS, UMBRAL, ESPERA_MIN, VENTANA_MIN = 3, 3, 1, 15
INICIO_CAIDA = 8 * 60 + 30


class Proveedor:
    def __init__(self, rnd: random.Random, caida: tuple[int, int]):
        self.rnd, self.caida = rnd, caida
        self.llamadas_en_caida = 0

    def cobrar(self, minuto: int) -> bool:
        if self.caida[0] <= minuto < self.caida[1]:
            self.llamadas_en_caida += 1
            return False
        return self.rnd.random() > P_TIMEOUT


def _con_reintentos(prov: Proveedor, minuto: int) -> bool:
    return any(prov.cobrar(minuto) for _ in range(INTENTOS))


def _llegadas(rnd: random.Random, minuto: int) -> int:
    """Pedidos que llegan en un minuto (proceso de Poisson con la tasa de esa hora)."""
    lam, n, t = PEDIDOS_POR_HORA[minuto // 60] / 60, 0, rnd.expovariate(PEDIDOS_POR_HORA[minuto // 60] / 60)
    while t < 1:
        n += 1
        t += rnd.expovariate(lam)
    return n


def simular(tactica: str, caida_min: int = 10, semilla: int = 11) -> dict:
    llegadas = random.Random(semilla)          # mismos pedidos para las tres tácticas
    prov = Proveedor(random.Random(semilla + 1), (INICIO_CAIDA, INICIO_CAIDA + caida_min))
    total = cobrados = perdidos = 0
    demoras: list[int] = []
    cola: deque[int] = deque()                 # minuto en que se difirió cada pedido (outbox)
    fallas, abierto_desde = 0, None

    def registrar(ok: bool, m: int) -> None:
        nonlocal fallas, abierto_desde
        if ok:
            fallas, abierto_desde = 0, None
        else:
            fallas += 1
            if fallas >= UMBRAL or abierto_desde is not None:
                abierto_desde = m

    for m in range(INICIO, FIN):
        if tactica == "breaker":
            while cola and m - cola[0] > VENTANA_MIN:          # vencidos: se cancelan
                cola.popleft()
                perdidos += 1
            # worker: cada minuto reintenta la outbox si el circuito lo permite
            while cola and (abierto_desde is None or m - abierto_desde >= ESPERA_MIN):
                ok = _con_reintentos(prov, m)
                registrar(ok, m)
                if not ok:
                    break
                demoras.append(m - cola.popleft())
                cobrados += 1
        for _ in range(_llegadas(llegadas, m)):
            total += 1
            if tactica == "ninguna":
                ok = prov.cobrar(m)
            elif tactica == "reintentos":
                ok = _con_reintentos(prov, m)
            else:
                if abierto_desde is not None and m - abierto_desde < ESPERA_MIN:
                    cola.append(m)                              # falla rápida: a la outbox
                    continue
                ok = _con_reintentos(prov, m)
                registrar(ok, m)
                if not ok:
                    cola.append(m)
                    continue
            cobrados += ok
            perdidos += not ok
    perdidos += len(cola)                                       # lo que quedó al cierre
    return {"total": total, "cobrados": cobrados, "perdidos": perdidos,
            "llamadas_en_caida": prov.llamadas_en_caida, "demora_max_min": max(demoras, default=0)}


if __name__ == "__main__":
    for caida in (10, 20):
        print(f"\nCaída del proveedor de {caida} min (08:30), jornada de sábado")
        for t in ("ninguna", "reintentos", "breaker"):
            r = simular(t, caida)
            print(f"  {t:10s} pedidos={r['total']}  cobrados={r['cobrados']/r['total']*100:6.2f} %  "
                  f"perdidos={r['perdidos']:4d}  llamadas_en_caida={r['llamadas_en_caida']:4d}  "
                  f"demora_max={r['demora_max_min']} min")
    print("\nSensibilidad (breaker): duración de la caída -> pedidos perdidos")
    print("  " + "  ".join(f"{c} min: {simular('breaker', c)['perdidos']}" for c in (5, 10, 15, 20, 25, 30)))

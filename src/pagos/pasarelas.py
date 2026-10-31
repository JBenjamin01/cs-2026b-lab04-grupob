"""Pagos con patrones (Lab 07): ADAPTER + STRATEGY + DECORATOR + FACTORY (registro).

- YapeAdapter y PlinAdapter traducen cada SDK a la interfaz PasarelaPago (Adapter).
- Cada adaptador es una estrategia intercambiable de cobro (Strategy).
- ConReintentos agrega reintentos ante TimeoutError sin modificar los adaptadores (Decorator).
- FabricaPasarelas crea la estrategia por nombre; un medio nuevo solo se registra (Factory).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Callable
from uuid import UUID

from pagos.modelos import EstadoPago, Pago, PasarelaPago


# ---------- ADAPTER: traduce cada SDK a la interfaz PasarelaPago ----------
class YapeAdapter(PasarelaPago):
    """El SDK cobra en soles y responde con un diccionario."""

    def __init__(self, sdk):
        self._sdk = sdk

    def iniciar_cobro(self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str) -> Pago:
        r = self._sdk.cobrar_yape(celular, monto, codigo_aprobacion)
        estado = EstadoPago.CONFIRMADO if r["estado"] == "APROBADO" else EstadoPago.RECHAZADO
        return Pago(pedido_id, monto, r["id_transaccion"], estado)

    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None:
        self._sdk.devolver(referencia_proveedor, monto)


class PlinAdapter(PasarelaPago):
    """El cliente cobra en céntimos y responde con (código HTTP, id de transacción)."""

    def __init__(self, cliente):
        self._cliente = cliente

    def iniciar_cobro(self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str) -> Pago:
        codigo, tx = self._cliente.charge(_a_centimos(monto), celular, codigo_aprobacion)
        estado = EstadoPago.CONFIRMADO if codigo == 200 else EstadoPago.RECHAZADO
        return Pago(pedido_id, monto, tx, estado)

    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None:
        self._cliente.refund(referencia_proveedor, _a_centimos(monto))


def _a_centimos(monto: Decimal) -> int:
    return int(monto * 100)


# ---------- DECORATOR: reintentos ante TimeoutError, sin tocar los adaptadores ----------
class ConReintentos(PasarelaPago):
    """Solo reintenta cuando el proveedor NO respondió. Un rechazo nunca se reintenta
    (reintentarlo podría generar cobros duplicados)."""

    def __init__(self, interna: PasarelaPago, intentos: int = 3):
        self._interna = interna
        self._intentos = intentos

    def iniciar_cobro(self, pedido_id: UUID, monto: Decimal, celular: str, codigo_aprobacion: str) -> Pago:
        for _ in range(self._intentos):
            try:
                return self._interna.iniciar_cobro(pedido_id, monto, celular, codigo_aprobacion)
            except TimeoutError:
                continue
        return Pago(pedido_id, monto, None, EstadoPago.EXPIRADO)

    def reembolsar(self, referencia_proveedor: str, monto: Decimal) -> None:
        for intento in range(self._intentos):
            try:
                return self._interna.reembolsar(referencia_proveedor, monto)
            except TimeoutError:
                if intento == self._intentos - 1:
                    raise


# ---------- FACTORY (registro): crea la estrategia adecuada por nombre ----------
class FabricaPasarelas:
    """Se crea e inyecta una instancia (no es Singleton): las pruebas registran SDK simulados."""

    def __init__(self, intentos: int = 3):
        self._creadores: dict[str, Callable[[], PasarelaPago]] = {}
        self._intentos = intentos

    def registrar(self, medio: str, creador: Callable[[], PasarelaPago]) -> None:
        self._creadores[medio] = creador

    def crear(self, medio: str) -> PasarelaPago:
        if medio not in self._creadores:
            raise ValueError(f"Medio de pago no soportado: {medio}")
        return ConReintentos(self._creadores[medio](), self._intentos)

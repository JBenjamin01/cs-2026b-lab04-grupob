"""Servicios externos SIMULADOS (Lab 07). Nunca llaman a la red ni usan claves de API.

Cada uno tiene una interfaz distinta, como ocurre con los SDK reales:
- YapeSDK: cobra en soles y responde con un diccionario.
- PlinClient: cobra en céntimos y responde con una tupla (código HTTP, id de transacción).
- ClienteClaudeSimulado: imita un SDK de chat que devuelve bloques de contenido.
- ModeloLocalSimulado: imita un modelo local que devuelve texto plano.
"""
from __future__ import annotations

from decimal import Decimal


class YapeSDK:
    """Proveedor de pagos que cobra con Yape (R-05: Yape no tiene API pública abierta)."""

    def __init__(self, fallas: int = 0, limite: Decimal = Decimal("500")):
        self.fallas = fallas          # cuántas llamadas seguidas lanzan TimeoutError
        self.limite = limite          # monto máximo por operación
        self.llamadas = 0
        self.montos: list[Decimal] = []
        self.devoluciones: list[tuple[str, Decimal]] = []

    def cobrar_yape(self, celular: str, monto_soles: Decimal, codigo_aprobacion: str) -> dict:
        self.llamadas += 1
        if self.llamadas <= self.fallas:
            raise TimeoutError("Yape no respondió")
        self.montos.append(monto_soles)
        if monto_soles > self.limite or codigo_aprobacion == "000000":
            return {"estado": "RECHAZADO", "id_transaccion": None}
        return {"estado": "APROBADO", "id_transaccion": f"YP-{self.llamadas:04d}"}

    def devolver(self, id_transaccion: str, monto_soles: Decimal) -> dict:
        self.devoluciones.append((id_transaccion, monto_soles))
        return {"estado": "DEVUELTO"}


class PlinClient:
    """Cliente de Plin (extensión prevista en R-05): trabaja en céntimos."""

    def __init__(self, fallas: int = 0, limite_centimos: int = 50000):
        self.fallas = fallas
        self.limite_centimos = limite_centimos
        self.llamadas = 0
        self.montos: list[int] = []
        self.reembolsos: list[tuple[str, int]] = []

    def charge(self, amount_cents: int, phone: str, otp: str) -> tuple[int, str | None]:
        self.llamadas += 1
        if self.llamadas <= self.fallas:
            raise TimeoutError("Plin timeout")
        self.montos.append(amount_cents)
        if amount_cents > self.limite_centimos or otp == "000000":
            return 402, None
        return 200, f"PL-{self.llamadas:04d}"

    def refund(self, tx_id: str, amount_cents: int) -> int:
        self.reembolsos.append((tx_id, amount_cents))
        return 200


class ClienteClaudeSimulado:
    """Imita la forma de un SDK de chat: messages_create(...) -> {"content": [{"text": ...}]}."""

    def __init__(self, respuesta: str = ""):
        self.respuesta = respuesta
        self.llamadas = 0

    def messages_create(self, model: str, max_tokens: int, messages: list[dict]) -> dict:
        self.llamadas += 1
        return {"content": [{"type": "text", "text": self.respuesta}]}


class ModeloLocalSimulado:
    """Imita un modelo ejecutado en local: generate(prompt) -> str."""

    def __init__(self, respuesta: str = ""):
        self.respuesta = respuesta
        self.llamadas = 0

    def generate(self, prompt: str) -> str:
        self.llamadas += 1
        return self.respuesta

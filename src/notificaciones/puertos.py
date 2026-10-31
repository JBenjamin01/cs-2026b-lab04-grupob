"""Puerto NotificadorMensajeria con tipos neutrales (ADR-004): no importa nada de pedidos."""
from __future__ import annotations

from abc import ABC, abstractmethod


class NotificadorMensajeria(ABC):
    @abstractmethod
    def notificar_comerciante(self, celular: str, resumen: str) -> None: ...

    @abstractmethod
    def notificar_cliente(self, celular: str, mensaje: str) -> None: ...


class WhatsAppAdapter(NotificadorMensajeria):
    """Encola el envío en Celery; el registro pendiente ya quedó en el outbox (ADR-001)."""

    def notificar_comerciante(self, celular: str, resumen: str) -> None:
        raise NotImplementedError("Encolar plantilla aprobada de WhatsApp Business")

    def notificar_cliente(self, celular: str, mensaje: str) -> None:
        raise NotImplementedError("Encolar plantilla aprobada de WhatsApp Business")


class BandejaMensajes(NotificadorMensajeria):
    """Adaptador en memoria (desarrollo y pruebas): guarda los mensajes en una lista."""

    def __init__(self, bandeja: list[str]):
        self._bandeja = bandeja

    def notificar_comerciante(self, celular: str, resumen: str) -> None:
        self._bandeja.append(f"whatsapp:{celular}:{resumen}")

    def notificar_cliente(self, celular: str, mensaje: str) -> None:
        self._bandeja.append(f"whatsapp:{celular}:{mensaje}")

"""Módulo Notificaciones. Interfaz pública del módulo."""
from notificaciones.puertos import NotificadorMensajeria, WhatsAppAdapter

__all__ = ["NotificadorMensajeria", "WhatsAppAdapter"]

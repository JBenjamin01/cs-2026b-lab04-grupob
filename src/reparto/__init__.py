"""Módulo Reparto: depende de pedidos (nunca al revés). Interfaz pública del módulo."""
from reparto.modelos import Repartidor
from reparto.suscriptores import AsignadorReparto

__all__ = ["AsignadorReparto", "Repartidor"]

"""Suscriptores del módulo Notificaciones (OBSERVER, Lab 07)."""
from __future__ import annotations

from comun.eventos import Suscriptor
from notificaciones.puertos import NotificadorMensajeria


class NotificadorComerciantes(Suscriptor):
    """Avisa a cada puesto qué parte del pedido le toca preparar."""

    def __init__(self, mensajeria: NotificadorMensajeria):
        self._mensajeria = mensajeria

    def actualizar(self, evento: str, datos: dict) -> None:
        for puesto in datos["puestos"]:
            self._mensajeria.notificar_comerciante(
                puesto["celular"],
                f"Pedido {datos['codigo']} - {puesto['productos']} producto(s) "
                f"para el puesto {puesto['numero_puesto']}")


class NotificadorCliente(Suscriptor):
    """Confirma el pago y avisa los reembolsos parciales al cliente."""

    def __init__(self, mensajeria: NotificadorMensajeria):
        self._mensajeria = mensajeria

    def actualizar(self, evento: str, datos: dict) -> None:
        if evento == "pedido_pagado":
            texto = f"Pedido {datos['codigo']} pagado: S/ {datos['total']:.2f}"
        else:  # subpedido_rechazado
            texto = f"Puesto {datos['numero_puesto']} sin stock; se reembolsó S/ {datos['monto']:.2f}"
        self._mensajeria.notificar_cliente(datos["celular_cliente"], texto)

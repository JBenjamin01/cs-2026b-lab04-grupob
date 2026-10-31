"""Raíz de composición (Lab 07): arma los objetos y conecta los patrones.

Es el único lugar que conoce las clases concretas (adaptadores, suscriptores, tarifas).
pedidos no importa notificaciones ni reparto: solo publica eventos (ADR-004 y ADR-005).
En producción, aquí se inyectarían los SDK reales; en las pruebas, los simulados.
"""
from __future__ import annotations

from dataclasses import dataclass

from comun.eventos import PublicadorEventos
from notificaciones.puertos import BandejaMensajes
from notificaciones.suscriptores import NotificadorCliente, NotificadorComerciantes
from pagos.pasarelas import FabricaPasarelas, PlinAdapter, YapeAdapter
from pedidos.externos import PlinClient, YapeSDK
from pedidos.pedido import Cliente, Pedido
from pedidos.servicio import ServicioPedidos
from pedidos.tarifas import tarifas_por_defecto
from reparto.suscriptores import AsignadorReparto

__all__ = ["Aplicacion", "Cliente", "Pedido", "crear_servicio_pedidos"]


@dataclass
class Aplicacion:
    servicio: ServicioPedidos
    eventos: list


def crear_servicio_pedidos(yape=None, plin=None) -> Aplicacion:
    yape, plin = yape or YapeSDK(), plin or PlinClient()
    fabrica = FabricaPasarelas()
    fabrica.registrar("YAPE", lambda: YapeAdapter(yape))
    fabrica.registrar("PLIN", lambda: PlinAdapter(plin))

    eventos: list[str] = []
    mensajeria = BandejaMensajes(eventos)
    publicador = PublicadorEventos()
    publicador.suscribir("pedido_pagado", NotificadorComerciantes(mensajeria))
    publicador.suscribir("pedido_pagado", NotificadorCliente(mensajeria))
    publicador.suscribir("pedido_pagado", AsignadorReparto(eventos))
    publicador.suscribir("subpedido_rechazado", NotificadorCliente(mensajeria))

    return Aplicacion(ServicioPedidos(fabrica, publicador, tarifas_por_defecto()), eventos)


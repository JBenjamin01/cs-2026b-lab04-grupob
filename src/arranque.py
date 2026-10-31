"""Raíz de composición (Lab 07): arma los objetos y conecta los patrones.

Es el único lugar que conoce las clases concretas (adaptadores, suscriptores, tarifas).
pedidos no importa notificaciones ni reparto: solo publica eventos (ADR-004 y ADR-005).
En producción, aquí se inyectarían los SDK reales; en las pruebas, los simulados.
"""
from __future__ import annotations

from dataclasses import dataclass

from catalogo import ClaudeAdapter, ConCache, LocalAdapter, NormalizadorNombres, cadena_guardrails
from comun.eventos import PublicadorEventos
from notificaciones import BandejaMensajes, NotificadorCliente, NotificadorComerciantes
from pagos import FabricaPasarelas, PlinAdapter, YapeAdapter
from pedidos import Cliente, Pedido, ServicioPedidos, tarifas_por_defecto
from pedidos.externos import ClienteClaudeSimulado, ModeloLocalSimulado, PlinClient, YapeSDK
from reparto import AsignadorReparto

__all__ = ["Aplicacion", "Cliente", "Pedido", "crear_normalizador", "crear_servicio_pedidos"]


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


def crear_normalizador(catalogo: list[str], claude=None, local=None) -> NormalizadorNombres:
    proveedores = {
        "CLAUDE": ConCache(ClaudeAdapter(claude or ClienteClaudeSimulado())),
        "LOCAL": ConCache(LocalAdapter(local or ModeloLocalSimulado())),
    }
    return NormalizadorNombres(proveedores, cadena_guardrails(catalogo), catalogo)

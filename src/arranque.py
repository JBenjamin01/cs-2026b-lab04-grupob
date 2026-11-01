"""Raíz de composición (Lab 07): arma los objetos y conecta los patrones.

Es el único lugar que conoce las clases concretas (adaptadores, suscriptores, tarifas).
pedidos no importa notificaciones ni reparto: solo publica eventos (ADR-004 y ADR-005).
En producción, aquí se inyectarían los SDK reales; en las pruebas, los simulados.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from catalogo import ClaudeAdapter, ConCache, LocalAdapter, NormalizadorNombres, cadena_guardrails
from comun.eventos import PublicadorEventos
from mercados import RepositorioMercados, RepositorioMercadosEnMemoria, cargar_datos_iniciales
from notificaciones import BandejaMensajes, NotificadorCliente, NotificadorComerciantes
from pagos import ColaPagosPendientes, ColaPagosPendientesEnMemoria, FabricaPasarelas
from pagos.adaptadores import PlinAdapter, YapeAdapter   # el único import de adaptadores (FF-02)
from pedidos import Cliente, Pedido, ServicioPedidos, tarifas_por_defecto
from pedidos.externos import ClienteClaudeSimulado, ModeloLocalSimulado, PlinClient, YapeSDK
from reparto import AsignadorReparto

__all__ = ["Aplicacion", "Cliente", "Pedido", "crear_normalizador", "crear_servicio_pedidos"]


@dataclass
class Aplicacion:
    servicio: ServicioPedidos
    eventos: list
    pendientes: ColaPagosPendientes | None = None


def crear_servicio_pedidos(yape=None, plin=None, mercados: RepositorioMercados | None = None,
                           reloj=None) -> Aplicacion:
    """`reloj` (opcional, para pruebas) tiene now() -> datetime y monotonic() -> float."""
    yape, plin = yape or YapeSDK(), plin or PlinClient()
    fabrica = FabricaPasarelas(reloj=reloj.monotonic) if reloj else FabricaPasarelas()
    reloj = reloj.now if reloj else datetime.now
    fabrica.registrar("YAPE", lambda: YapeAdapter(yape))
    fabrica.registrar("PLIN", lambda: PlinAdapter(plin))

    eventos: list[str] = []
    mensajeria = BandejaMensajes(eventos)
    publicador = PublicadorEventos()
    publicador.suscribir("pedido_pagado", NotificadorComerciantes(mensajeria))
    publicador.suscribir("pedido_pagado", NotificadorCliente(mensajeria))
    publicador.suscribir("pedido_pagado", AsignadorReparto(eventos))
    publicador.suscribir("subpedido_rechazado", NotificadorCliente(mensajeria))

    mercados = mercados or RepositorioMercadosEnMemoria(cargar_datos_iniciales())  # Lab 08 (ADR-006)
    pendientes = ColaPagosPendientesEnMemoria()                                     # Lab 08 (ADR-008)
    servicio = ServicioPedidos(fabrica, publicador, tarifas_por_defecto(), mercados=mercados,
                               pendientes=pendientes, reloj=reloj)
    return Aplicacion(servicio, eventos, pendientes)


def crear_normalizador(catalogo: list[str], claude=None, local=None) -> NormalizadorNombres:
    proveedores = {
        "CLAUDE": ConCache(ClaudeAdapter(claude or ClienteClaudeSimulado())),
        "LOCAL": ConCache(LocalAdapter(local or ModeloLocalSimulado())),
    }
    return NormalizadorNombres(proveedores, cadena_guardrails(catalogo), catalogo)

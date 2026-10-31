"""Raíz de composición (Lab 07): arma los objetos y conecta los patrones.

Es el único lugar que conoce las clases concretas. En producción, aquí se inyectarían los SDK
reales; en las pruebas, los simulados.
"""
from __future__ import annotations

from dataclasses import dataclass

from pagos.pasarelas import FabricaPasarelas, PlinAdapter, YapeAdapter
from pedidos.externos import PlinClient, YapeSDK
from pedidos.pedido import Cliente, Pedido
from pedidos.servicio import ServicioPedidos

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
    return Aplicacion(ServicioPedidos(fabrica, eventos), eventos)

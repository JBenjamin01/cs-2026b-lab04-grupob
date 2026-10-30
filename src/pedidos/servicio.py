"""Servicio de aplicación del módulo Pedidos (Lab 07, E2): pagos con Strategy + Adapter + Factory.

Ya no hay if/elif por medio de pago. Quedan pendientes (E4): la tarifa de envío y los avisos
armados a mano.
"""
from __future__ import annotations

from decimal import Decimal

from catalogo.modelos import Comerciante
from pagos.pasarelas import FabricaPasarelas
from pedidos.pedido import Pedido, a_soles


class ServicioPedidos:
    def __init__(self, fabrica: FabricaPasarelas, eventos: list[str]):
        self._fabrica = fabrica
        self.eventos = eventos

    def confirmar_y_pagar(self, pedido: Pedido, medio: str, codigo_aprobacion: str = "123456") -> str:
        pasarela = self._fabrica.crear(medio)  # valida el medio ANTES de tocar el pedido
        pedido.confirmar()
        subtotal = pedido.subtotal()
        envio = Decimal("0")
        if pedido.tipo_entrega.value == "DELIVERY":
            if subtotal >= 150:
                envio = Decimal("0")
            elif pedido.distrito in ("Cercado", "Selva Alegre"):
                envio = Decimal("5")
            elif pedido.distrito in ("Yanahuara", "Cayma", "Miraflores"):
                envio = Decimal("8")
            else:
                envio = Decimal("12")
        pedido.costo_envio = envio
        pedido.medio_pago = medio
        pago = pasarela.iniciar_cobro(pedido.id, pedido.total(), pedido.cliente.celular, codigo_aprobacion)
        if pago.esta_confirmado():
            pedido.registrar_pago(pago)
            for pp in pedido.subpedidos:
                self.eventos.append(f"whatsapp:{pp.comerciante.celular}:Pedido {pedido.codigo} - "
                                    f"{len(pp.lineas)} producto(s) para el puesto {pp.comerciante.numero_puesto}")
            self.eventos.append(f"whatsapp:{pedido.cliente.celular}:Pedido {pedido.codigo} pagado: "
                                f"S/ {pedido.total():.2f}")
            if pedido.tipo_entrega.value == "DELIVERY":
                self.eventos.append(f"reparto:{pedido.codigo}:{pedido.distrito}")
        else:
            pedido.cancelar("pago rechazado")
        return pedido.estado

    def rechazar_puesto(self, pedido: Pedido, comerciante: Comerciante, motivo: str) -> str:
        subpedido = pedido.subpedido_de(comerciante)
        subpedido.rechazar(motivo)
        monto = a_soles(subpedido.subtotal())
        self._fabrica.crear(pedido.medio_pago).reembolsar(pedido.pago.referencia_proveedor, monto)
        self.eventos.append(f"whatsapp:{pedido.cliente.celular}:Puesto {comerciante.numero_puesto} "
                            f"sin stock; se reembolsó S/ {monto:.2f}")
        return subpedido.estado

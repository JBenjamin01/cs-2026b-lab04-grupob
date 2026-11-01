"""Servicio de aplicación del módulo Pedidos DESPUÉS del refactor (Lab 07).

Ya no contiene if/elif por medio de pago, por tarifa ni por estado, ni arma los mensajes a mano:
- elige la pasarela con la Factory (Strategy + Adapter + Decorator),
- delega las transiciones al patrón State,
- calcula el envío con una Strategy de tarifa,
- y publica eventos para que los interesados reaccionen (Observer).

Lab 08 (ADR-006): las reglas de cada mercado (pedido mínimo, medios aceptados, zonas de delivery,
comisión) llegan como datos desde el módulo Mercados. El servicio nunca pregunta «¿qué mercado es?».
"""
from __future__ import annotations

from catalogo import Comerciante
from comun.eventos import PublicadorEventos
from mercados import ReglasMercado, RepositorioMercados
from pagos import EstadoPago, FabricaPasarelas, Pago
from pedidos.pedido import Pedido, TipoEntrega, a_soles
from pedidos.puertos import RepositorioEnMemoria, RepositorioPedidos
from pedidos.tarifas import TarifaEnvio, TarifaPorZona


class ServicioPedidos:
    def __init__(self, fabrica: FabricaPasarelas, publicador: PublicadorEventos,
                 tarifas: dict[str, TarifaEnvio], repositorio: RepositorioPedidos | None = None,
                 mercados: RepositorioMercados | None = None):
        self._fabrica = fabrica
        self._mercados = mercados
        self._publicador = publicador
        self._tarifas = tarifas
        self._repositorio = repositorio or RepositorioEnMemoria()

    def confirmar_y_pagar(self, pedido: Pedido, medio: str, codigo_aprobacion: str = "123456") -> str:
        pasarela = self._fabrica.crear(medio)  # valida el medio ANTES de tocar el pedido
        reglas = self._reglas_de(pedido)
        if reglas:
            reglas.validar_pedido(pedido.subtotal(), medio)
        tarifa = self._tarifa_para(pedido, reglas)
        pedido.confirmar()
        pedido.costo_envio = tarifa.calcular(pedido.subtotal(), pedido.distrito)
        pedido.medio_pago = medio
        if reglas:
            pedido.comision = reglas.comision_de(pedido.subtotal())
        pago = pasarela.iniciar_cobro(pedido.id, pedido.total(), pedido.cliente.celular, codigo_aprobacion)
        if pago.estado is not EstadoPago.PENDIENTE:  # si queda PENDIENTE, decide el webhook
            self._aplicar_resultado(pedido, pago)
        return pedido.estado

    def procesar_webhook_pago(self, pedido: Pedido, pago: Pago) -> None:
        """Webhook idempotente del proveedor (ADR-002): ignora pedidos ya resueltos."""
        if pedido.estado == "PENDIENTE_PAGO":
            self._aplicar_resultado(pedido, pago)

    def cancelar_por_tiempo_agotado(self, pedido: Pedido) -> None:
        pedido.cancelar("sin respuesta del proveedor en 15 min")
        self._repositorio.guardar(pedido)

    def rechazar_puesto(self, pedido: Pedido, comerciante: Comerciante, motivo: str) -> str:
        subpedido = pedido.subpedido_de(comerciante)
        subpedido.rechazar(motivo)
        monto = a_soles(subpedido.subtotal())
        self._fabrica.crear(pedido.medio_pago).reembolsar(pedido.pago.referencia_proveedor, monto)
        self._repositorio.guardar(pedido)
        self._publicador.publicar("subpedido_rechazado", {
            "codigo": pedido.codigo, "celular_cliente": pedido.cliente.celular,
            "numero_puesto": comerciante.numero_puesto, "monto": monto})
        return subpedido.estado

    def _reglas_de(self, pedido: Pedido) -> ReglasMercado | None:
        return self._mercados.obtener(pedido.mercado) if self._mercados else None

    def _tarifa_para(self, pedido: Pedido, reglas: ReglasMercado | None) -> TarifaEnvio:
        if reglas and pedido.tipo_entrega is TipoEntrega.DELIVERY:
            return TarifaPorZona(dict(reglas.zonas_delivery), reglas.tarifa_por_defecto,
                                 reglas.delivery_gratis_desde)
        return self._tarifas[pedido.tipo_entrega.value]

    def _aplicar_resultado(self, pedido: Pedido, pago: Pago) -> None:
        if pago.esta_confirmado():
            pedido.registrar_pago(pago)
            self._repositorio.guardar(pedido)  # misma transacción que el outbox (ADR-001)
            self._publicador.publicar("pedido_pagado", self._datos_pagado(pedido))
        else:
            pedido.cancelar("pago rechazado")
            self._repositorio.guardar(pedido)

    @staticmethod
    def _datos_pagado(pedido: Pedido) -> dict:
        """Datos neutrales (ADR-004): los suscriptores no necesitan importar pedidos."""
        return {
            "codigo": pedido.codigo, "celular_cliente": pedido.cliente.celular,
            "total": pedido.total(), "tipo_entrega": pedido.tipo_entrega.value,
            "distrito": pedido.distrito,
            "puestos": [{"celular": pp.comerciante.celular, "numero_puesto": pp.comerciante.numero_puesto,
                         "productos": len(pp.lineas)} for pp in pedido.subpedidos],
        }

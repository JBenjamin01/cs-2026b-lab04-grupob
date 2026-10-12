"""Servicio de aplicación del módulo Pedidos: orquesta el flujo del diagrama de secuencia (E2)."""
from __future__ import annotations

from uuid import UUID

from notificaciones import NotificadorMensajeria
from pagos import EstadoPago, Pago, PasarelaPago
from pedidos.dominio import EstadoPedido, Pedido
from pedidos.puertos import RepositorioPedidos


class ServicioPedidos:
    def __init__(
        self,
        repositorio: RepositorioPedidos,
        pasarela: PasarelaPago,
        notificador: NotificadorMensajeria,
    ) -> None:
        self._repositorio = repositorio
        self._pasarela = pasarela
        self._notificador = notificador

    def confirmar_y_pagar(self, pedido_id: UUID, celular: str, codigo_aprobacion: str) -> Pedido:
        pedido = self._repositorio.buscar_por_id(pedido_id)
        pedido.confirmar()
        total = pedido.calcular_total()
        pago = self._pasarela.iniciar_cobro(pedido.id, total, celular, codigo_aprobacion)
        if pago.estado is not EstadoPago.PENDIENTE:  # si queda PENDIENTE, decide el webhook
            self._aplicar_resultado(pedido, pago)
        return pedido

    def procesar_webhook_pago(self, pedido_id: UUID, pago: Pago) -> None:
        """Webhook idempotente del proveedor (ADR-002): ignora pedidos ya resueltos."""
        pedido = self._repositorio.buscar_por_id(pedido_id)
        if pedido.estado is EstadoPedido.PENDIENTE_PAGO:
            self._aplicar_resultado(pedido, pago)

    def _aplicar_resultado(self, pedido: Pedido, pago: Pago) -> None:
        if pago.esta_confirmado():
            pedido.registrar_pago(pago)
            self._repositorio.guardar(pedido)  # misma transacción que el outbox (ADR-001)
            for subpedido in pedido.subpedidos:
                resumen = f"Pedido {pedido.codigo_seguimiento}: {len(subpedido.lineas)} producto(s)"
                self._notificador.notificar_comerciante(subpedido.comerciante.celular, resumen)
        else:
            pedido.cancelar("pago rechazado")
            self._repositorio.guardar(pedido)

    def procesar_rechazo_puesto(self, subpedido_id: UUID, motivo: str) -> None:
        pedido = self._repositorio.buscar_por_subpedido(subpedido_id)
        subpedido = pedido.buscar_subpedido(subpedido_id)
        subpedido.rechazar(motivo)
        if pedido.pago is not None:
            self._pasarela.reembolsar(pedido.pago.id, subpedido.calcular_subtotal())
        self._repositorio.guardar(pedido)
        self._notificador.notificar_cliente(
            pedido.cliente.celular, f"Un puesto no tenía stock: se reembolsó su parte ({motivo})"
        )

    def cancelar_por_tiempo_agotado(self, pedido_id: UUID) -> None:
        pedido = self._repositorio.buscar_por_id(pedido_id)
        pedido.cancelar("sin respuesta del proveedor en 15 min")
        self._repositorio.guardar(pedido)

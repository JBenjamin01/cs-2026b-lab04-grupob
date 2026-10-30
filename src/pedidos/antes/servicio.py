"""VERSIÓN ANTES (ingenua) del flujo crítico «confirmar y pagar un pedido multipuesto».

Se escribió rápido para el sprint a partir de la secuencia del Lab 05 y SE CONSERVA SOLO PARA
COMPARAR (Lab 07, E1). No se usa en producción: la versión con patrones está en pedidos/,
pagos/, comun/eventos.py, notificaciones/, reparto/, catalogo/ia.py y arranque.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from pedidos.externos import ClienteClaudeSimulado, ModeloLocalSimulado, PlinClient, YapeSDK


@dataclass
class Cliente:
    nombre: str
    celular: str
    direccion: str


@dataclass
class Linea:
    producto: object
    cantidad: Decimal
    precio: Decimal


@dataclass
class Subpedido:
    comerciante: object
    lineas: list = field(default_factory=list)
    estado: str = "PENDIENTE"
    motivo_rechazo: str | None = None


class Pedido:
    def __init__(self, cliente, tipo_entrega="RECOJO_MERCADO", distrito=None, codigo="SC-0001"):
        self.cliente = cliente
        self.tipo_entrega = tipo_entrega
        self.distrito = distrito
        self.codigo = codigo
        self.id: UUID = uuid4()
        self.subpedidos: list[Subpedido] = []
        self.estado = "CREADO"
        self.costo_envio = Decimal("0")
        self.medio_pago = None
        self.operacion = None

    def agregar_linea(self, producto, cantidad):
        if self.estado != "CREADO":
            raise ValueError("Solo se agregan productos a un pedido CREADO")
        for s in self.subpedidos:
            if s.comerciante.id == producto.comerciante.id:
                s.lineas.append(Linea(producto, cantidad, producto.precio))
                return
        self.subpedidos.append(Subpedido(producto.comerciante, [Linea(producto, cantidad, producto.precio)]))


class ServicioPedidos:
    def __init__(self, yape=None, plin=None, claude=None, local=None, catalogo=None):
        self.yape = yape or YapeSDK()
        self.plin = plin or PlinClient()
        self.claude = claude or ClienteClaudeSimulado()
        self.local = local or ModeloLocalSimulado()
        self.catalogo = catalogo or []
        self.eventos: list[str] = []

    def confirmar_y_pagar(self, pedido, medio, codigo_aprobacion="123456"):
        if pedido.estado != "CREADO":
            if pedido.estado == "CANCELADO":
                raise ValueError("El pedido está cancelado")
            elif pedido.estado == "PAGADO":
                raise ValueError("El pedido ya fue pagado")
            else:
                raise ValueError("Estado no válido")
        if not pedido.subpedidos:
            raise ValueError("El pedido no tiene productos")
        reservadas = []
        for s in pedido.subpedidos:
            for l in s.lineas:
                if not l.producto.disponible or l.cantidad > l.producto.stock_disponible:
                    for p, c in reservadas:
                        p.stock_disponible += c
                    raise ValueError(f"Stock insuficiente de {l.producto.nombre}")
                l.producto.stock_disponible -= l.cantidad
                reservadas.append((l.producto, l.cantidad))
        pedido.estado = "PENDIENTE_PAGO"
        subtotal = Decimal("0")
        for s in pedido.subpedidos:
            for l in s.lineas:
                subtotal += l.cantidad * l.precio
        envio = Decimal("0")
        if pedido.tipo_entrega == "DELIVERY":
            if subtotal >= 150:
                envio = Decimal("0")
            elif pedido.distrito in ("Cercado", "Selva Alegre"):
                envio = Decimal("5")
            elif pedido.distrito in ("Yanahuara", "Cayma", "Miraflores"):
                envio = Decimal("8")
            else:
                envio = Decimal("12")
        pedido.costo_envio = envio
        total = subtotal + envio
        aprobado, operacion = False, None
        if medio == "YAPE":
            for intento in range(3):
                try:
                    r = self.yape.cobrar_yape(pedido.cliente.celular, total, codigo_aprobacion)
                    aprobado, operacion = r["estado"] == "APROBADO", r["id_transaccion"]
                    break
                except TimeoutError:
                    if intento == 2:
                        aprobado = False
        elif medio == "PLIN":
            for intento in range(3):
                try:
                    codigo, tx = self.plin.charge(int(total * 100), pedido.cliente.celular, codigo_aprobacion)
                    aprobado, operacion = codigo == 200, tx
                    break
                except TimeoutError:
                    if intento == 2:
                        aprobado = False
        else:
            raise ValueError(f"Medio de pago no soportado: {medio}")
        if aprobado:
            pedido.estado = "PAGADO"
            pedido.medio_pago = medio
            pedido.operacion = operacion
            for s in pedido.subpedidos:
                s.estado = "RECIBIDO"
                self.eventos.append(
                    f"whatsapp:{s.comerciante.celular}:Pedido {pedido.codigo} - "
                    f"{len(s.lineas)} producto(s) para el puesto {s.comerciante.numero_puesto}")
            self.eventos.append(f"whatsapp:{pedido.cliente.celular}:Pedido {pedido.codigo} pagado: S/ {total:.2f}")
            if pedido.tipo_entrega == "DELIVERY":
                self.eventos.append(f"reparto:{pedido.codigo}:{pedido.distrito}")
        else:
            for p, c in reservadas:
                p.stock_disponible += c
            for s in pedido.subpedidos:
                s.estado = "ANULADO"
            pedido.estado = "CANCELADO"
        return pedido.estado

    def rechazar_puesto(self, pedido, comerciante, motivo):
        sub = None
        for s in pedido.subpedidos:
            if s.comerciante.id == comerciante.id:
                sub = s
        if sub is None:
            raise ValueError("El puesto no participa en el pedido")
        if sub.estado != "RECIBIDO":
            if sub.estado == "RECHAZADO":
                raise ValueError("El subpedido ya fue rechazado")
            else:
                raise ValueError(f"No se puede rechazar un subpedido {sub.estado}")
        sub.estado = "RECHAZADO"
        sub.motivo_rechazo = motivo
        monto = Decimal("0")
        for l in sub.lineas:
            monto += l.cantidad * l.precio
        if pedido.medio_pago == "YAPE":
            self.yape.devolver(pedido.operacion, monto)
        elif pedido.medio_pago == "PLIN":
            self.plin.refund(pedido.operacion, int(monto * 100))
        self.eventos.append(
            f"whatsapp:{pedido.cliente.celular}:Puesto {comerciante.numero_puesto} sin stock; "
            f"se reembolsó S/ {monto:.2f}")
        return sub.estado

    def sugerir_nombre(self, nombre, proveedor="CLAUDE"):
        for c in self.catalogo:
            if c.lower() == nombre.strip().lower():
                return c
        prompt = (f"Normaliza el nombre de producto '{nombre}' a uno de esta lista: "
                  f"{', '.join(self.catalogo)}. Responde solo con el nombre.")
        if proveedor == "CLAUDE":
            r = self.claude.messages_create(model="claude", max_tokens=50,
                                            messages=[{"role": "user", "content": prompt}])
            texto = r["content"][0]["text"]
        elif proveedor == "LOCAL":
            texto = self.local.generate(prompt)
        else:
            raise ValueError(f"Proveedor de IA no soportado: {proveedor}")
        texto = texto.strip().strip('"').strip("'").rstrip(".").strip()
        if "S/" in texto or any(ch.isdigit() for ch in texto):
            return None
        if len(texto) > 40:
            return None
        for c in self.catalogo:
            if c.lower() == texto.lower():
                return c
        return None


@dataclass
class Aplicacion:
    """Lo que las pruebas de caracterización usan en ambas versiones."""
    servicio: ServicioPedidos
    eventos: list


def crear_servicio_pedidos(yape=None, plin=None) -> Aplicacion:
    s = ServicioPedidos(yape=yape, plin=plin)
    return Aplicacion(s, s.eventos)


def crear_normalizador(catalogo, claude=None, local=None) -> ServicioPedidos:
    return ServicioPedidos(claude=claude, local=local, catalogo=catalogo)

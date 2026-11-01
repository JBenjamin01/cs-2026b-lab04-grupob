"""Módulo Pagos (no depende de pedidos). Interfaz pública del módulo.

Lab 08 (FF-02): los adaptadores (YapeAdapter, PlinAdapter) ya NO se exportan aquí; se importan
desde pagos.adaptadores y solo en arranque.py.
"""
from pagos.modelos import EstadoPago, Pago, PasarelaPago
from pagos.pasarelas import ConReintentos, FabricaPasarelas
from pagos.pendientes import ColaPagosPendientes, ColaPagosPendientesEnMemoria, PagoPendiente
from pagos.resiliencia import CircuitoAbierto, ConCircuitBreaker

__all__ = ["CircuitoAbierto", "ColaPagosPendientes", "ColaPagosPendientesEnMemoria", "ConCircuitBreaker",
           "ConReintentos", "EstadoPago", "FabricaPasarelas", "Pago", "PagoPendiente", "PasarelaPago"]

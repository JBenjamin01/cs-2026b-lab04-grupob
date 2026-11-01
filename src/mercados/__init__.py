"""Módulo Mercados (Lab 08, ADR-006). Interfaz pública del módulo.

Cada mercado (San Camilo, Altiplano, Río Seco...) tiene sus propias reglas. Se guardan como
DATOS (tabla `mercados_mercado`, editable desde el administrador de Django), no como código:
incorporar un mercado o cambiar una regla no exige desplegar (QA-07 y QA-08).
"""
from mercados.reglas import ConfiguracionInvalida, ReglasMercado
from mercados.repositorio import RepositorioMercados, RepositorioMercadosEnMemoria, cargar_datos_iniciales

__all__ = ["ConfiguracionInvalida", "ReglasMercado", "RepositorioMercados", "RepositorioMercadosEnMemoria",
           "cargar_datos_iniciales"]

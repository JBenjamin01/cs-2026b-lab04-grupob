"""Puerto de persistencia de las reglas de mercado y su adaptador en memoria.

En producción, el adaptador lee la tabla `mercados_mercado` de PostgreSQL (editable desde el
administrador de Django) y la cachea; `datos_iniciales.json` es la carga inicial (fixture).
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from comun.excepciones import ReglaNegocioError
from mercados.reglas import ReglasMercado


class RepositorioMercados(ABC):
    @abstractmethod
    def obtener(self, codigo: str) -> ReglasMercado: ...

    @abstractmethod
    def guardar(self, datos: dict) -> ReglasMercado: ...

    @abstractmethod
    def codigos(self) -> list[str]: ...


class RepositorioMercadosEnMemoria(RepositorioMercados):
    def __init__(self, datos: list[dict] | None = None):
        self._reglas: dict[str, ReglasMercado] = {}
        for d in datos or []:
            self.guardar(d)

    def obtener(self, codigo: str) -> ReglasMercado:
        if codigo not in self._reglas:
            raise ReglaNegocioError(f"Mercado no registrado: {codigo}")
        return self._reglas[codigo]

    def guardar(self, datos: dict) -> ReglasMercado:
        reglas = ReglasMercado.desde_dict(datos)   # valida antes de guardar
        self._reglas[reglas.codigo] = reglas
        return reglas

    def codigos(self) -> list[str]:
        return sorted(self._reglas)


def cargar_datos_iniciales() -> list[dict]:
    return json.loads((Path(__file__).parent / "datos_iniciales.json").read_text(encoding="utf-8"))

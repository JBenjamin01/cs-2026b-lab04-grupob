"""OBSERVER (Lab 07): publicador de eventos con datos neutrales (dict), sin acoplarse a quién escucha.

Vive en comun para que pedidos publique y notificaciones/reparto escuchen sin depender entre sí
(regla de dependencias de ADR-004).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Suscriptor(ABC):
    @abstractmethod
    def actualizar(self, evento: str, datos: dict) -> None: ...


class PublicadorEventos:
    def __init__(self) -> None:
        self._suscriptores: dict[str, list[Suscriptor]] = {}

    def suscribir(self, evento: str, suscriptor: Suscriptor) -> None:
        self._suscriptores.setdefault(evento, []).append(suscriptor)

    def publicar(self, evento: str, datos: dict) -> None:
        for suscriptor in self._suscriptores.get(evento, []):
            suscriptor.actualizar(evento, datos)

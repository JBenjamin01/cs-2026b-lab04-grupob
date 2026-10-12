"""Excepciones de dominio comunes."""


class ReglaNegocioError(Exception):
    """Se viola una regla de negocio (por ejemplo, stock insuficiente)."""


class EstadoInvalidoError(ReglaNegocioError):
    """Se invoca una operación que no es válida en el estado actual de la entidad."""

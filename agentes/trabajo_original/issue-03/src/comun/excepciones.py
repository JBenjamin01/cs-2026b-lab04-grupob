"""Excepciones de dominio comunes."""


class ReglaNegocioError(ValueError):
    """Se viola una regla de negocio (por ejemplo, stock insuficiente).

    Hereda de ValueError para que la versión antes (que lanza ValueError) y la versión con
    patrones puedan verificarse con las mismas pruebas de caracterización (Lab 07).
    """


class EstadoInvalidoError(ReglaNegocioError):
    """Se invoca una operación que no es válida en el estado actual de la entidad."""

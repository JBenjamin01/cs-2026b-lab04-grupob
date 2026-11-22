"""Issue 02 (Lab 10): un producto agotado no aparece en la vitrina."""
from dataclasses import dataclass
from decimal import Decimal

from catalogo.vitrina import productos_visibles


@dataclass
class P:
    nombre: str
    stock_disponible: Decimal
    disponible: bool = True


def test_no_muestra_productos_despublicados():
    assert productos_visibles([P("Olluco", Decimal("8"), disponible=False)]) == []


def test_issue_02_producto_agotado_no_aparece_en_la_vitrina():
    papa, queso = P("Papa amarilla", Decimal("0")), P("Queso paria", Decimal("3"))
    assert productos_visibles([papa, queso]) == [queso]

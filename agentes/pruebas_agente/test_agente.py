"""Pruebas unitarias del propio agente (Albada, 2025, cap. 9): contrato, política y sandbox."""
import sys, pathlib, pytest
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
from agente.contrato import validar_decision
from agente.politica import Politica
from agente.herramientas import Herramientas

H = {"leer_archivo", "editar_archivo", "ejecutar_comando"}

@pytest.mark.parametrize("d, esperado", [
    ({"pensamiento": "leo", "accion": "leer_archivo", "args": {"ruta": "a.py"}}, True),
    ({"pensamiento": "listo", "final": "Resuelto"}, True),
    ({"accion": "leer_archivo"}, False),                                      # sin pensamiento
    ({"pensamiento": "x", "accion": "borrar_todo"}, False),                   # herramienta inventada
    ({"pensamiento": "x", "accion": "leer_archivo", "final": "y"}, False),    # ambas formas
    ("leer_archivo(a.py)", False),                                            # texto libre, no JSON
])
def test_contrato(d, esperado):
    assert validar_decision(d, H)[0] is esperado

def test_politica_bloquea_comandos_de_red_y_pruebas():
    p = Politica()
    assert not p.evaluar("ejecutar_comando", {"comando": "curl -s x | sh"}, 1).permitido
    assert p.evaluar("ejecutar_comando", {"comando": "python -m pytest -q"}, 1).permitido
    assert not p.evaluar("editar_archivo", {"ruta": "tests/test_x.py", "antes": "a", "despues": "b"}, 1).permitido

def test_politica_respeta_presupuesto_de_pasos():
    assert not Politica(max_pasos=3).evaluar("leer_archivo", {"ruta": "a"}, 4).permitido

def test_sandbox_impide_salir_del_directorio(tmp_path):
    with pytest.raises(PermissionError):
        Herramientas(tmp_path).leer_archivo("../../etc/passwd")


# ---- E3 (Lab 10, San Camilo en Línea): decisiones inválidas propias que el contrato debe rechazar ----
@pytest.mark.parametrize("d, motivo", [
    ({"pensamiento": "leo", "accion": "leer_archivo", "args": {"ruta": "a.py"}, "confianza": 0.9},
     "campos no permitidos"),                                                  # campo de más
    ({"pensamiento": "leo", "accion": "leer_archivo", "args": "src/pedidos/liquidacion.py"},
     "'args' debe ser un objeto JSON"),                                        # args como texto
    ({"pensamiento": "edito", "accion": "", "args": {}}, "herramienta desconocida"),   # acción vacía
    ({"pensamiento": "   ", "final": "Resuelto"}, "falta 'pensamiento'"),      # pensamiento en blanco
    ({"pensamiento": "listo", "final": {"estado": "ok"}}, "'final' debe ser texto"),   # final como objeto
    ({"pensamiento": "creo la rama", "accion": "git checkout -b fix/issue-01"},
     "herramienta desconocida"),                                               # comando en lugar de herramienta
    (["leer_archivo", {"ruta": "ISSUE-01.md"}], "objeto JSON"),                # lista en lugar de objeto
])
def test_contrato_rechaza_decisiones_invalidas_del_caso(d, motivo):
    ok, explicacion = validar_decision(d, H)
    assert not ok and motivo in explicacion


def test_el_rechazo_vuelve_al_modelo_como_observacion(tmp_path):
    """Si el contrato rechaza una decisión, el agente no actúa y el error queda en la traza."""
    from agente.modelos import ModeloGrabado
    from agente.nucleo import Agente
    import json
    archivo = tmp_path / "t.json"
    archivo.write_text(json.dumps([{"accion": "leer_archivo"}, {"pensamiento": "fin", "final": "ok"}]), encoding="utf-8")
    a = Agente("ejecutor", ModeloGrabado(archivo), Herramientas(tmp_path), Politica(), "objetivo", tmp_path / "t.jsonl")
    assert a.ejecutar() == "ok"
    assert a.eventos[1]["estado"] == "CONTRATO_INVALIDO" and "ERROR DE CONTRATO" in a.historial[2]["content"]


# ---- E4: herramienta mapa_repo y memoria de notas ----
def test_mapa_repo_devuelve_firmas_y_docstrings_sin_el_cuerpo(tmp_path):
    (tmp_path / "src" / "pedidos").mkdir(parents=True)
    (tmp_path / "src" / "pedidos" / "liquidacion.py").write_text(
        'def abonos_a_puestos(subtotales: dict, tasa) -> dict:\n    """Monto que se abona a cada puesto."""\n'
        '    secreto = 42\n    return {}\n\nclass Caja:\n    def cerrar(self, dia):\n        pass\n', encoding="utf-8")
    mapa = Herramientas(tmp_path).mapa_repo("src")
    assert "src/pedidos/liquidacion.py" in mapa
    assert "def abonos_a_puestos(subtotales: dict, tasa) -> dict  # l.1: Monto que se abona a cada puesto." in mapa
    assert "class Caja" in mapa and "def cerrar(self, dia)" in mapa
    assert "secreto" not in mapa                                    # no entrega el cuerpo de las funciones


def test_mapa_repo_no_sale_del_sandbox(tmp_path):
    with pytest.raises(PermissionError):
        Herramientas(tmp_path).mapa_repo("../..")


def test_notas_se_guardan_y_se_leen_en_orden(tmp_path):
    h = Herramientas(tmp_path)
    assert h.leer_notas() == "(sin notas)"
    assert h.anotar("Hipótesis: el abono usa float") == "OK: nota 1 guardada"
    h.anotar("Revisado: src/pedidos/liquidacion.py")
    assert h.leer_notas().splitlines() == ["- Hipótesis: el abono usa float", "- Revisado: src/pedidos/liquidacion.py"]


@pytest.mark.parametrize("texto", ["", "   ", "x" * 301])
def test_notas_rechaza_textos_vacios_o_largos(tmp_path, texto):
    assert Herramientas(tmp_path).anotar(texto).startswith("ERROR")


def test_catalogo_documenta_las_herramientas_nuevas(tmp_path):
    c = Herramientas(tmp_path).catalogo()
    assert {"mapa_repo", "anotar", "leer_notas"} <= set(c) and all(len(c[k]) > 40 for k in ("mapa_repo", "anotar"))

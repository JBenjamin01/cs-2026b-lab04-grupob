"""Herramientas del agente. Cada una es una función pequeña, con descripción y parámetros explícitos.
Todas operan DENTRO del directorio de trabajo (sandbox)."""
import ast, pathlib, re, subprocess


class Herramientas:
    def __init__(self, raiz: str, original: str | None = None):
        self.raiz = pathlib.Path(raiz).resolve()
        self.original = pathlib.Path(original).resolve() if original else self.raiz.parent / "trabajo_original"

    # --- utilidades ---
    def _ruta(self, ruta: str) -> pathlib.Path:
        p = (self.raiz / ruta).resolve()
        if self.raiz not in p.parents and p != self.raiz:
            raise PermissionError(f"Ruta fuera del sandbox: {ruta}")
        return p

    def catalogo(self) -> dict:
        """Descripción de las herramientas que se envía al modelo (como en un MCP server)."""
        return {
            "listar_archivos": "listar_archivos(carpeta='.'): lista los archivos .py y .md",
            "leer_archivo": "leer_archivo(ruta): devuelve el contenido con números de línea",
            "buscar": "buscar(patron): busca una expresión regular en los archivos .py",
            "ejecutar_pruebas": "ejecutar_pruebas(): ejecuta pytest y devuelve el resumen",
            "editar_archivo": "editar_archivo(ruta, antes, despues): reemplaza un fragmento exacto (una sola vez)",
            "ver_cambios": "ver_cambios(): muestra el diff respecto de la versión original",
            "ejecutar_comando": "ejecutar_comando(comando): ejecuta un comando de shell (sujeto a la política)",
            "mapa_repo": "mapa_repo(carpeta='src'): estructura del código sin leerlo entero: por archivo, las "
                         "clases y funciones con su firma y la primera línea del docstring (módulo ast). "
                         "Devuelve texto; no modifica nada",
            "anotar": "anotar(texto): agrega una línea a notas.md (hipótesis, archivos revisados, pendientes); "
                      "máx. 300 caracteres",
            "leer_notas": "leer_notas(): devuelve notas.md (las notas de esta tarea) o '(sin notas)'",
        }

    # --- herramientas ---
    def listar_archivos(self, carpeta="."):
        base = self._ruta(carpeta)
        return "\n".join(sorted(p.relative_to(self.raiz).as_posix() for p in base.rglob("*")
                                if p.suffix in (".py", ".md") and "__pycache__" not in p.parts))

    def leer_archivo(self, ruta):
        lineas = self._ruta(ruta).read_text(encoding="utf-8").splitlines()
        return "\n".join(f"{i:3d}| {l}" for i, l in enumerate(lineas, 1))

    def buscar(self, patron):
        rx, hallazgos = re.compile(patron), []
        for p in sorted(self.raiz.rglob("*.py")):
            for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if rx.search(l):
                    hallazgos.append(f"{p.relative_to(self.raiz).as_posix()}:{i}: {l.strip()}")
        return "\n".join(hallazgos) or "(sin resultados)"

    def ejecutar_pruebas(self):
        r = subprocess.run(["python", "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
                           cwd=self.raiz, capture_output=True, text=True, timeout=120)
        salida = (r.stdout + r.stderr).strip().splitlines()
        fallos = [l for l in salida if l.startswith(("FAILED", "E "))][:6]
        return "\n".join(fallos + salida[-1:])

    def editar_archivo(self, ruta, antes, despues):
        p = self._ruta(ruta)
        texto = p.read_text(encoding="utf-8")
        if texto.count(antes) != 1:
            return f"ERROR: el fragmento aparece {texto.count(antes)} veces; debe aparecer exactamente 1"
        p.write_text(texto.replace(antes, despues), encoding="utf-8")
        return f"OK: {ruta} modificado"

    def ver_cambios(self):
        import difflib
        base, salida = self.original, []
        for p in sorted(self.raiz.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            rel = p.relative_to(self.raiz).as_posix(); q = base / rel
            a = q.read_text(encoding="utf-8").splitlines() if q.exists() else []
            salida += difflib.unified_diff(a, p.read_text(encoding="utf-8").splitlines(),
                                           f"a/{rel}", f"b/{rel}", lineterm="", n=1)
        return "\n".join(salida) or "(sin cambios)"

    def ejecutar_comando(self, comando):
        r = subprocess.run(comando, shell=True, cwd=self.raiz, capture_output=True, text=True, timeout=60)
        return (r.stdout + r.stderr).strip()[-2000:]

    # --- E4 (Lab 10): herramienta nueva y memoria de notas ---
    def mapa_repo(self, carpeta="src"):
        """Mapa del repositorio: firmas en lugar de código completo (ingeniería de contexto)."""
        lineas = []
        for p in sorted(self._ruta(carpeta).rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            try:
                arbol = ast.parse(p.read_text(encoding="utf-8"))
            except SyntaxError as e:
                lineas.append(f"{p.relative_to(self.raiz).as_posix()}: ERROR de sintaxis en la línea {e.lineno}")
                continue
            lineas.append(p.relative_to(self.raiz).as_posix())
            for n in arbol.body:
                if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                    lineas.append(f"  {self._firma(n)}  # l.{n.lineno}{self._doc(n)}")
                if isinstance(n, ast.ClassDef):
                    lineas += [f"    {self._firma(m)}  # l.{m.lineno}{self._doc(m)}" for m in n.body
                               if isinstance(m, ast.FunctionDef) and not m.name.startswith("__")]
        return "\n".join(lineas) or "(sin archivos .py)"

    @staticmethod
    def _firma(n):
        if isinstance(n, ast.ClassDef):
            return f"class {n.name}"
        ret = f" -> {ast.unparse(n.returns)}" if n.returns else ""
        return f"def {n.name}({ast.unparse(n.args)}){ret}"

    @staticmethod
    def _doc(n):
        d = ast.get_docstring(n)
        return f": {d.splitlines()[0][:70]}" if d else ""

    def anotar(self, texto):
        texto = " ".join(str(texto).split())
        if not texto:
            return "ERROR: la nota está vacía"
        if len(texto) > 300:
            return "ERROR: la nota supera 300 caracteres; resúmala"
        with open(self.raiz / "notas.md", "a", encoding="utf-8") as f:
            f.write(f"- {texto}\n")
        return f"OK: nota {len(self.leer_notas().splitlines())} guardada"

    def leer_notas(self):
        p = self.raiz / "notas.md"
        return p.read_text(encoding="utf-8").strip() if p.exists() else "(sin notas)"

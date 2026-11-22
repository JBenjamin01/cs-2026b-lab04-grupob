"""Humano en el circuito (Lab 10, E6): un integrante aprueba o rechaza cada edición antes de ejecutarla.

Patrones de la Tabla 8: «aprobar o rechazar», «revisar llamadas a herramientas» y «validar la entrada
humana» (solo se acepta «s» o «n»).
"""


class AprobacionConsola:
    """Muestra la edición propuesta y pregunta en la consola. Repite hasta recibir «s» o «n»."""

    def __init__(self, entrada=input, salida=print, max_intentos=5):
        self._entrada, self._salida, self._max = entrada, salida, max_intentos
        self.registro = []                                   # (ruta, respuesta) para la traza y el informe

    def __call__(self, args: dict) -> bool:
        self._salida(f"\n=== EDICIÓN PROPUESTA en {args.get('ruta')} ===\n--- antes\n{args.get('antes')}\n"
                     f"+++ después\n{args.get('despues')}")
        for _ in range(self._max):
            r = str(self._entrada("¿Aprueba esta edición? [s/n]: ")).strip().lower()
            if r in ("s", "n"):
                self.registro.append((args.get("ruta"), r))
                return r == "s"
            self._salida("Respuesta no válida: escriba solo «s» o «n».")
        self.registro.append((args.get("ruta"), "sin respuesta válida"))
        return False                                         # ante la duda, NO se edita

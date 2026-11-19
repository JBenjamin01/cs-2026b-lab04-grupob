"""Reto opcional A (Lab 09): compara dos modelos con el mismo prompt.

Combina (1) la tasa de aprobación de promptfoo (resultados-*.json), (2) la latencia medida al grabar
cada respuesta (latencias.json) y (3) un costo ESTIMADO por caso a partir del tamaño del prompt y de
la respuesta. Escribe comparacion.json y comparacion.md.

Uso (desde esta carpeta, después de las tres evaluaciones):  python comparar.py
"""
import json
import pathlib
import re
import statistics

AQUI = pathlib.Path(__file__).parent
CARACTERES_POR_TOKEN = 4          # aproximación para texto en español; no hay tokenizador sin conexión
PRECIOS = {                        # USD por millón de tokens (página oficial de precios, nov. 2026)
    "sonnet": {"modelo": "Claude Sonnet 5.5", "entrada": 2.00, "salida": 10.00},
    "haiku": {"modelo": "Claude Haiku 5.5", "entrada": 0.10, "salida": 0.50},
}
CONJUNTOS = {"criterios": ("resultados-criterios.json", "v3.1"),
             "normalizacion": ("resultados-normalizacion.json", "v3.1"),
             "seguridad v3": ("resultados-seguridad.json", "v3"),
             "seguridad v3.1": ("resultados-seguridad.json", "v3.1")}


def main():
    lat = json.loads((AQUI / "latencias.json").read_text(encoding="utf-8"))
    filas = []
    for conjunto, (archivo, version) in CONJUNTOS.items():
        res = json.loads((AQUI / archivo).read_text(encoding="utf-8"))["results"]["results"]
        fila = {"conjunto": conjunto}
        for modelo, precio in PRECIOS.items():
            casos = [r for r in res if r["provider"]["label"] == modelo
                     and re.search(r"(v[\w.]+)\.txt", r["prompt"]["label"]).group(1) == version]
            medidas = [x for x in lat if x["modelo"] == modelo and x["conjunto"] == conjunto]
            costo = statistics.mean(
                (x["caracteres_prompt"] / CARACTERES_POR_TOKEN * precio["entrada"]
                 + x["caracteres_respuesta"] / CARACTERES_POR_TOKEN * precio["salida"]) / 1e6 for x in medidas)
            fila[modelo] = {"casos": len(casos), "aprobados": sum(r["success"] for r in casos),
                            "tasa": sum(r["success"] for r in casos) / len(casos),
                            "fallidos": [r["vars"]["id"] for r in casos if not r["success"]],
                            "latencia_mediana_s": round(statistics.median(x["segundos"] for x in medidas), 2),
                            "costo_usd_por_caso": costo, "costo_usd_por_1000": round(costo * 1000, 3)}
        filas.append(fila)
    (AQUI / "comparacion.json").write_text(json.dumps({"precios": PRECIOS, "filas": filas}, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    lineas = ["| Conjunto | Modelo | Aprobación | Latencia mediana | Costo estimado / 1 000 casos | Casos que fallan |",
              "|----------|--------|------------|------------------|-------------------------------|------------------|"]
    for f in filas:
        for m in PRECIOS:
            d = f[m]
            lineas.append(f"| {f['conjunto']} | {PRECIOS[m]['modelo']} | {d['aprobados']}/{d['casos']} ({d['tasa']:.0%}) | "
                          f"{d['latencia_mediana_s']:.1f} s | US$ {d['costo_usd_por_1000']:.2f} | {', '.join(d['fallidos']) or '—'} |")
    (AQUI / "comparacion.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()

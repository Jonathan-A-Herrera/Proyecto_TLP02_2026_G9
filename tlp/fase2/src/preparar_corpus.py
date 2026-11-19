"""
preparar_corpus.py
Convierte corpus/oraciones.txt en corpus/corpus.csv con dos etiquetas por oración:

  esperado             ACEPTA / RECHAZA según el español (etiqueta escrita a mano en oraciones.txt)
  en_gramatica         SI / NO: si la oración pertenece a L(G), el lenguaje de nuestra CFG.
                       Se calcula de forma exacta con el ChartParser de NLTK (parser general,
                       acepta gramáticas ambiguas) sobre la misma gramática v2.
  categorias_esperadas estructura esperada: la categoría de cada palabra.

Uso:  python src/preparar_corpus.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nltk                                                          # noqa: E402
from nltk import CFG                                                 # noqa: E402
from gramaticas_espanol import LEXICO, GRAMATICA_V2, INICIAL, etiquetar  # noqa: E402
from comun import RAIZ, CORPUS_CSV, normalizar, separar              # noqa: E402


def a_cfg_nltk(gramatica, inicial, version=2):
    lineas, terminales = [], set()
    for A in [inicial] + [k for k in gramatica if k != inicial]:
        for prod in gramatica[A]:
            lineas.append(f"{A} -> {' '.join(prod)}")
            terminales |= {s for s in prod if s not in gramatica}
    for palabra in LEXICO:
        _, cats = etiquetar(palabra, version)
        if cats[0] in terminales:
            lineas.append(f'{cats[0]} -> "{palabra}"')
    return CFG.fromstring("\n".join(lineas))


def main():
    chart = nltk.ChartParser(a_cfg_nltk(GRAMATICA_V2, INICIAL))
    filas = []
    with open(os.path.join(RAIZ, "corpus", "oraciones.txt"), encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            nivel, esperado, oracion, fenomeno = [x.strip() for x in linea.split("|")]
            palabras = separar(oracion)
            faltan = [p for p in palabras if p not in LEXICO]
            if faltan:
                raise SystemExit(f"Palabras fuera del léxico en '{oracion}': {faltan}")
            cats = [normalizar(LEXICO[p][0][0]) for p in palabras]
            try:
                arboles = len(list(chart.parse(palabras)))
            except ValueError:       # la gramática v2 no tiene reglas para ',', 'y' ni 'respectivamente'
                arboles = 0
            filas.append({"id": len(filas) + 1, "nivel": nivel, "oracion": oracion,
                          "esperado": esperado, "en_gramatica": "SI" if arboles else "NO",
                          "arboles_en_G": arboles, "categorias_esperadas": " ".join(cats),
                          "fenomeno": fenomeno})
    with open(CORPUS_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} oraciones escritas en {CORPUS_CSV}")
    for n in "123":
        sub = [r for r in filas if r["nivel"] == n]
        print(f"  Nivel {n}: {len(sub)} oraciones, {sum(r['esperado'] == 'ACEPTA' for r in sub)} correctas, "
              f"{sum(r['en_gramatica'] == 'SI' for r in sub)} dentro de L(G)")


if __name__ == "__main__":
    main()

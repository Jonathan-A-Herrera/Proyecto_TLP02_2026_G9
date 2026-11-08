"""
analisis_fallas.py
Experimentos que documentan dónde y por qué falla la CFG con el español.

  1. Tamaño y conflictos LL(1) de cada gramática (MiniC, v1, v2).
  2. Resultado de v1 y v2 sobre el conjunto de oraciones (aceptada / rechazada,
     falsos positivos, falsos negativos y número de árboles posibles).
  3. Ambigüedad estructural: árboles según cuántas frases preposicionales hay.
  4. Explosión de la gramática al agregar rasgos de concordancia.
  5. Dependencias cruzadas con "respectivamente" (v3a y v3b).
"""
import os
import json
import nltk
from nltk import CFG

from ll1 import ParserLL1, ErrorLL1, construir_tabla, contar_producciones, formato_prod
from gramatica_c import GRAMATICA_C, INICIAL_C
from gramaticas_espanol import (LEXICO, GRAMATICA_V1, GRAMATICA_V2, GRAMATICA_V3A, GRAMATICA_V3B,
                                INICIAL, etiquetar, separar, generar_v2, PalabraDesconocida)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO_ORACIONES = os.path.join(RAIZ, "ejemplos", "oraciones_espanol.txt")


def leer_oraciones(ruta=ARCHIVO_ORACIONES):
    datos = []
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            etiqueta, oracion, fenomeno = [x.strip() for x in linea.split("|")]
            datos.append({"esperado": etiqueta, "oracion": oracion, "fenomeno": fenomeno})
    return datos


def a_cfg_nltk(gramatica, inicial, version):
    """Traduce nuestra gramática (diccionario) a un nltk.CFG agregando las reglas léxicas.
    Sirve para usar el ChartParser de NLTK, que es un parser general (acepta gramáticas
    ambiguas) y devuelve TODOS los árboles posibles, no solo uno como el LL(1)."""
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


def contar_arboles(parser_chart, oracion):
    try:
        return len(list(parser_chart.parse(separar(oracion))))
    except ValueError:            # palabra fuera de la gramática
        return 0


# ---------------------------------------------------------------------------
def experimento_tablas():
    filas = []
    for nombre, g, ini in [("MiniC", GRAMATICA_C, INICIAL_C), ("Español v1", GRAMATICA_V1, INICIAL),
                           ("Español v2", GRAMATICA_V2, INICIAL)]:
        _, conflictos, _, _ = construir_tabla(g, ini)
        filas.append({
            "gramatica": nombre, "no_terminales": len(g), "producciones": contar_producciones(g),
            "conflictos": len(conflictos),
            "detalle": [f"M[{A}, {a}] = {{ " + " | ".join(formato_prod(A, p) for p in ps) + " }"
                        for (A, a), ps in sorted(conflictos.items())],
        })
    return filas


def experimento_oraciones():
    p1, p2 = ParserLL1(GRAMATICA_V1, INICIAL), ParserLL1(GRAMATICA_V2, INICIAL)
    chart1 = nltk.ChartParser(a_cfg_nltk(GRAMATICA_V1, INICIAL, 1))
    chart2 = nltk.ChartParser(a_cfg_nltk(GRAMATICA_V2, INICIAL, 2))
    resultados = []
    for d in leer_oraciones():
        fila = dict(d)
        for nombre, parser, version, chart in [("v1", p1, 1, chart1), ("v2", p2, 2, chart2)]:
            try:
                palabras, cats = etiquetar(d["oracion"], version)
                parser.analizar(cats, palabras)
                fila[nombre] = "acepta"
                fila[nombre + "_motivo"] = ""
            except (ErrorLL1, PalabraDesconocida) as e:
                fila[nombre] = "rechaza"
                fila[nombre + "_motivo"] = str(e)
            fila[nombre + "_arboles"] = contar_arboles(chart, d["oracion"])
            correcto = (fila[nombre] == "acepta") == (d["esperado"] == "G")
            if correcto:
                fila[nombre + "_tipo"] = "VP" if d["esperado"] == "G" else "VN"
            else:
                fila[nombre + "_tipo"] = "FP" if fila[nombre] == "acepta" else "FN"
        resultados.append(fila)
    return resultados


def resumen_metricas(resultados, version):
    conteo = {"VP": 0, "VN": 0, "FP": 0, "FN": 0}
    for r in resultados:
        conteo[r[version + "_tipo"]] += 1
    total = sum(conteo.values())
    conteo["exactitud"] = round((conteo["VP"] + conteo["VN"]) / total, 3)
    return conteo


def experimento_ambiguedad(max_sp=6):
    chart = nltk.ChartParser(a_cfg_nltk(GRAMATICA_V1, INICIAL, 1))
    filas = []
    base = "ana vio el perro"
    frases = ["en el parque", "con el telescopio", "sobre la mesa", "de la niña", "en la casa", "con el libro"]
    for k in range(max_sp + 1):
        oracion = " ".join([base] + frases[:k])
        filas.append({"frases_prep": k, "oracion": oracion, "arboles": contar_arboles(chart, oracion)})
    return filas


def experimento_explosion():
    """Cuánto crece la gramática si cada rasgo de concordancia se codifica en los no terminales."""
    casos = [
        ("Sin rasgos (v1)", None),
        ("Número (s, p)", (["x"], ["s", "p"])),
        ("Género y número (v2)", (["m", "f"], ["s", "p"])),
        ("Género, número y persona", (["m", "f"], ["1s", "2s", "3s", "1p", "2p", "3p"])),
        ("Lo anterior + formalidad (tú/usted)", (["m", "f"], ["1s", "2s", "2su", "3s", "1p", "2p", "2pu", "3p"])),
    ]
    filas = []
    for nombre, rasgos in casos:
        g = GRAMATICA_V1 if rasgos is None else generar_v2(*rasgos)
        filas.append({"caso": nombre, "combinaciones": 1 if rasgos is None else len(rasgos[0]) * len(rasgos[1]),
                      "no_terminales": len(g), "producciones": contar_producciones(g)})
    return filas


def experimento_respectivamente():
    oraciones = [
        ("G", "Ana , Luis y Pedro son alta , alto y alto respectivamente", "orden cruzado correcto"),
        ("A", "Ana , Luis y Pedro son alto , alto y alta respectivamente", "orden espejo (incorrecto)"),
        ("A", "Ana y Luis son alto y alta respectivamente", "mal emparejado"),
        ("G", "Ana y Luis son alta y alto respectivamente", "orden cruzado correcto"),
    ]
    chart_a = nltk.ChartParser(a_cfg_nltk(GRAMATICA_V3A, "O", 2))
    chart_b = nltk.ChartParser(a_cfg_nltk(GRAMATICA_V3B, "O", 2))
    filas = []
    for esperado, o, desc in oraciones:
        filas.append({"esperado": esperado, "oracion": o, "descripcion": desc,
                      "v3a": "acepta" if contar_arboles(chart_a, o) else "rechaza",
                      "v3b": "acepta" if contar_arboles(chart_b, o) else "rechaza"})
    return filas


# ---------------------------------------------------------------------------
def linea(c="-", n=100):
    return c * n


def ejecutar_todo(guardar=True):
    salida = []
    p = salida.append

    p(linea("="))
    p("1. TAMAÑO Y CONFLICTOS LL(1) DE CADA GRAMÁTICA")
    p(linea("="))
    tablas = experimento_tablas()
    for t in tablas:
        p(f"{t['gramatica']}: {t['no_terminales']} no terminales, {t['producciones']} producciones, "
          f"{t['conflictos']} conflictos LL(1)")
        for d in t["detalle"][:8]:
            p("    " + d)
        if len(t["detalle"]) > 8:
            p(f"    ... y {len(t['detalle']) - 8} conflictos más del mismo tipo")

    p("")
    p(linea("="))
    p("2. RESULTADOS DE v1 Y v2 SOBRE EL CONJUNTO DE ORACIONES")
    p("   VP: aceptó una correcta | VN: rechazó una incorrecta | FP: aceptó una incorrecta | FN: rechazó una correcta")
    p(linea("="))
    oraciones = experimento_oraciones()
    for i, r in enumerate(oraciones, 1):
        p(f"{i:2}. [{r['esperado']}] {r['oracion']}")
        p(f"      fenómeno: {r['fenomeno']}")
        p(f"      v1: {r['v1']:7} ({r['v1_tipo']}, árboles={r['v1_arboles']})   "
          f"v2: {r['v2']:7} ({r['v2_tipo']}, árboles={r['v2_arboles']})")
        if r["v2_motivo"]:
            p(f"      motivo v2: {r['v2_motivo'][:140]}")
    m1, m2 = resumen_metricas(oraciones, "v1"), resumen_metricas(oraciones, "v2")
    p(f"Resumen v1: {m1}")
    p(f"Resumen v2: {m2}")

    p("")
    p(linea("="))
    p("3. AMBIGÜEDAD ESTRUCTURAL: ÁRBOLES SEGÚN EL NÚMERO DE FRASES PREPOSICIONALES (v1, ChartParser de NLTK)")
    p(linea("="))
    amb = experimento_ambiguedad()
    for a in amb:
        p(f"  {a['frases_prep']} SP -> {a['arboles']:4} árboles   ({a['oracion']})")

    p("")
    p(linea("="))
    p("4. EXPLOSIÓN DE LA GRAMÁTICA AL CODIFICAR LA CONCORDANCIA EN LOS NO TERMINALES")
    p(linea("="))
    exp = experimento_explosion()
    for e in exp:
        p(f"  {e['caso']:40} combinaciones={e['combinaciones']:3}  no terminales={e['no_terminales']:4}  "
          f"producciones={e['producciones']:5}")

    p("")
    p(linea("="))
    p("5. DEPENDENCIAS CRUZADAS CON 'RESPECTIVAMENTE' (v3a: listas libres, v3b: emparejamiento anidado)")
    p(linea("="))
    resp = experimento_respectivamente()
    for r in resp:
        p(f"  [{r['esperado']}] {r['oracion']:62} v3a: {r['v3a']:8} v3b: {r['v3b']:8} ({r['descripcion']})")

    texto = "\n".join(salida)
    if guardar:
        carpeta = os.path.join(RAIZ, "salidas")
        os.makedirs(carpeta, exist_ok=True)
        with open(os.path.join(carpeta, "resultados_fallas.txt"), "w", encoding="utf-8") as f:
            f.write(texto)
        with open(os.path.join(carpeta, "resultados_fallas.json"), "w", encoding="utf-8") as f:
            json.dump({"tablas": tablas, "oraciones": oraciones, "metricas": {"v1": m1, "v2": m2},
                       "ambiguedad": amb, "explosion": exp, "respectivamente": resp},
                      f, ensure_ascii=False, indent=2)
    return texto


if __name__ == "__main__":
    print(ejecutar_todo())

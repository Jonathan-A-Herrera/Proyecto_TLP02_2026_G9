"""
demo.py
Punto de entrada para la demostración.
    python demo.py c ejemplos/programa_valido.c     analiza un archivo MiniC
    python demo.py c "int x = 2 + 3;"               analiza código escrito en la línea
    python demo.py tabla                            FIRST, FOLLOW y conflictos de MiniC
    python demo.py es "Las niñas que el profesor regañó están cansadas"
    python demo.py fallas                           experimentos de los puntos de falla
    python demo.py nlp                              comparación con spaCy y NLTK
    python demo.py pruebas                          corre todas las pruebas unitarias
"""
import os
import sys
import unittest

# En consola Windows o una redirección a archivo pueden no usar UTF-8 [tildes, ñ o ramas del árbol]
for flujo in (sys.stdout, sys.stderr):
    try:
        flujo.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from parser_c import analizar                                                   # noqa: E402
from ll1 import ParserLL1, ErrorLL1, construir_tabla, formato_prod, EPS          # noqa: E402
from gramatica_c import GRAMATICA_C, INICIAL_C                                   # noqa: E402
from gramaticas_espanol import GRAMATICA_V1, GRAMATICA_V2, INICIAL, etiquetar, PalabraDesconocida  # noqa: E402

VENTANA = "--ventana" in sys.argv


def mostrar_arbol(arbol):
    print(arbol.imprimir())
    if VENTANA:
        arbol.a_nltk().draw()


def demo_c(entrada):
    if os.path.isfile(entrada):
        with open(entrada, encoding="utf-8") as f:
            codigo = f.read()
        print(f"Archivo: {entrada}")
    else:
        codigo = entrada
    print("-" * 70)
    print(codigo)
    print("-" * 70)
    arbol, errores = analizar(codigo)
    if errores:
        print(f"RECHAZADO: {len(errores)} error(es) sintáctico(s)")
        for e in errores:
            print("  -", e)
    else:
        print("ACEPTADO. Árbol de análisis sintáctico:")
        mostrar_arbol(arbol)


def demo_tabla():
    tabla, conflictos, first, follow = construir_tabla(GRAMATICA_C, INICIAL_C)
    print(f"{'No terminal':14} {'FIRST':45} FOLLOW")
    for A in GRAMATICA_C:
        f = ", ".join(sorted(first[A]))
        fo = ", ".join(sorted(follow[A]))
        print(f"{A:14} {f:45} {fo}")
    print(f"\nCeldas de la tabla LL(1): {len(tabla)}  |  Conflictos: {len(conflictos)}")
    for (A, a), prods in conflictos.items():
        print(f"  M[{A}, {a}] = " + " | ".join(formato_prod(A, p) for p in prods))
    print("Se resuelve eligiendo 'sino -> ELSE sentencia' (else con el if más cercano), igual que C.")


def demo_es(oracion):
    print(f"Oración: {oracion}\n")
    for nombre, g, v in [("v1 (sin concordancia)", GRAMATICA_V1, 1), ("v2 (con concordancia)", GRAMATICA_V2, 2)]:
        print("=" * 70)
        print(nombre)
        try:
            palabras, cats = etiquetar(oracion, v)
        except PalabraDesconocida as e:
            print("  ", e)
            continue
        print("  Categorías:", " ".join(cats))
        try:
            arbol, decisiones = ParserLL1(g, INICIAL).analizar(cats, palabras)
            print("  ACEPTADA")
            for (A, a, prods) in decisiones:
                print(f"  Conflicto LL(1) en M[{A}, {a}]: {' | '.join(prods)}  -> se eligió la primera")
            mostrar_arbol(arbol)
        except ErrorLL1 as e:
            print("  RECHAZADA:", e)
    # lecturas posibles con un parser general (NLTK)
    import nltk
    from analisis_fallas import a_cfg_nltk
    from gramaticas_espanol import separar
    try:
        arboles = list(nltk.ChartParser(a_cfg_nltk(GRAMATICA_V2, INICIAL, 2)).parse(separar(oracion)))
    except ValueError:
        arboles = []
    print("=" * 70)
    print(f"Parser general de NLTK con la gramática v2: {len(arboles)} árbol(es) posible(s)")
    for i, t in enumerate(arboles[:3], 1):
        print(f"\nLectura {i}:")
        t.pretty_print(unicodelines=True)


def demo_pruebas():
    suite = unittest.defaultTestLoader.discover(os.path.join(RAIZ, "tests"))
    unittest.TextTestRunner(verbosity=2).run(suite)


def menu():
    opciones = {
        "1": ("Analizar programa válido de MiniC", lambda: demo_c(os.path.join(RAIZ, "ejemplos", "programa_valido.c"))),
        "2": ("Analizar programa con errores", lambda: demo_c(os.path.join(RAIZ, "ejemplos", "programa_con_errores.c"))),
        "3": ("Else colgante", lambda: demo_c(os.path.join(RAIZ, "ejemplos", "else_colgante.c"))),
        "4": ("Escribir código MiniC", lambda: demo_c(input("Código: "))),
        "5": ("Tabla FIRST/FOLLOW y conflictos de MiniC", demo_tabla),
        "6": ("Analizar oración en español", lambda: demo_es(input("Oración: "))),
        "7": ("Experimentos de puntos de falla", lambda: print(__import__("analisis_fallas").ejecutar_todo())),
        "8": ("Comparación con spaCy y NLTK", lambda: print(__import__("demo_nlp").ejecutar_todo()[0])),
        "9": ("Correr pruebas unitarias", demo_pruebas),
    }
    while True:
        print("\n===== Proyecto TLP Fase 1 =====")
        for k, (texto, _) in opciones.items():
            print(f" {k}. {texto}")
        print(" 0. Salir")
        op = input("Opción: ").strip()
        if op == "0":
            break
        if op in opciones:
            opciones[op][1]()


def main():
    args = [a for a in sys.argv[1:] if a != "--ventana"]
    if not args:
        menu()
    elif args[0] == "c":
        demo_c(" ".join(args[1:]) or os.path.join(RAIZ, "ejemplos", "programa_valido.c"))
    elif args[0] == "tabla":
        demo_tabla()
    elif args[0] == "es":
        demo_es(" ".join(args[1:]) or "Ana vio el perro con el telescopio")
    elif args[0] == "fallas":
        import analisis_fallas
        print(analisis_fallas.ejecutar_todo())
    elif args[0] == "nlp":
        import demo_nlp
        print(demo_nlp.ejecutar_todo()[0])
    elif args[0] == "pruebas":
        demo_pruebas()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

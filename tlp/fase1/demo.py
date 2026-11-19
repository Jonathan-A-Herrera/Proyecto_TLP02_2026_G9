"""
demo.py - Demostración del parser LL(1) de MiniC.

    python demo.py                        menú
    python demo.py first                  conjuntos FIRST y FOLLOW
    python demo.py tabla                  tabla predictiva LL(1)
    python demo.py traza ejemplos/corto.c traza de la pila paso a paso + árbol
    python demo.py analizar ejemplos/valido.c
    python demo.py analizar "x = (a + 2) * b;"
    python demo.py pruebas                pruebas unitarias
Agregar --ventana para ver el árbol en una ventana gráfica (requiere nltk y Tkinter).
"""
import os
import sys
import unittest

for flujo in (sys.stdout, sys.stderr):          # tildes y ramas del árbol en la consola de Windows
    try:
        flujo.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from gramatica import GRAMATICA, formato, EPS                                  # noqa: E402
from parser_ll1 import analizar, TABLA, CONFLICTOS, FIRST, FOLLOW, ErrorSintactico  # noqa: E402
from lexer import ErrorLexico                                                   # noqa: E402

VENTANA = "--ventana" in sys.argv


def leer(entrada):
    if os.path.isfile(entrada):
        with open(entrada, encoding="utf-8") as f:
            return f.read()
    return entrada


def mostrar_gramatica():
    print("GRAMÁTICA LL(1) DE MiniC")
    for A, prods in GRAMATICA.items():
        print(f"  {A:12} → " + " | ".join(" ".join(p) if p else EPS for p in prods))
    print(f"\n{len(GRAMATICA)} no terminales, {sum(len(p) for p in GRAMATICA.values())} producciones")


def mostrar_first():
    print(f"{'No terminal':13}{'FIRST':42}FOLLOW")
    for A in GRAMATICA:
        print(f"{A:13}{', '.join(sorted(FIRST[A])):42}{', '.join(sorted(FOLLOW[A]))}")


def mostrar_tabla():
    print(f"Tabla LL(1): {len(TABLA)} celdas con producción, {len(CONFLICTOS)} conflictos")
    for A in GRAMATICA:
        fila = sorted((a, p) for (X, a), p in TABLA.items() if X == A)
        print(f"\n{A}")
        for a, p in fila:
            print(f"   M[{A}, {a}] = {formato(A, p)}")
    if not CONFLICTOS:
        print("\nNinguna celda tiene dos producciones: la gramática es LL(1).")


def correr(entrada, traza=False):
    codigo = leer(entrada)
    print("-" * 70 + "\n" + codigo.rstrip() + "\n" + "-" * 70)
    try:
        arbol, pasos = analizar(codigo, traza=traza)
    except (ErrorLexico, ErrorSintactico) as e:
        print("RECHAZADO:", e)
        return
    if traza:
        ancho = max(len(p[0]) for p in pasos) + 2
        ancho_e = min(max(len(p[1]) for p in pasos) + 2, 40)
        print(f"{'PILA':{ancho}}{'ENTRADA':{ancho_e}}ACCIÓN")
        for pila, ent, acc in pasos:
            print(f"{pila:{ancho}}{ent[:ancho_e - 2]:{ancho_e}}{acc}")
        print()
    print("ACEPTADO. Árbol de análisis sintáctico:")
    print(arbol.texto())
    if VENTANA:
        arbol.a_nltk().draw()


def pruebas():
    unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(os.path.join(RAIZ, "tests")))


def menu():
    ej = lambda n: os.path.join(RAIZ, "ejemplos", n)      # noqa: E731
    opciones = {
        "1": ("Ver la gramática", mostrar_gramatica),
        "2": ("FIRST y FOLLOW", mostrar_first),
        "3": ("Tabla LL(1)", mostrar_tabla),
        "4": ("Traza paso a paso (int x = 2 + 3 * 4;)", lambda: correr(ej("corto.c"), traza=True)),
        "5": ("Programa válido completo", lambda: correr(ej("valido.c"))),
        "6": ("Programa con error", lambda: correr(ej("con_error.c"))),
        "7": ("Escribir código", lambda: correr(input("Código: "), traza=True)),
        "8": ("Pruebas unitarias", pruebas),
    }
    while True:
        print("\n===== Parser LL(1) de MiniC =====")
        for k, (t, _) in opciones.items():
            print(f" {k}. {t}")
        print(" 0. Salir")
        op = input("Opción: ").strip()
        if op == "0":
            break
        if op in opciones:
            opciones[op][1]()


def main():
    args = [a for a in sys.argv[1:] if a != "--ventana"]
    if not args:
        return menu()
    cmd, resto = args[0], " ".join(args[1:])
    if cmd == "gramatica":
        mostrar_gramatica()
    elif cmd == "first":
        mostrar_first()
    elif cmd == "tabla":
        mostrar_tabla()
    elif cmd == "traza":
        correr(resto or os.path.join(RAIZ, "ejemplos", "corto.c"), traza=True)
    elif cmd == "analizar":
        correr(resto or os.path.join(RAIZ, "ejemplos", "valido.c"))
    elif cmd == "pruebas":
        pruebas()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

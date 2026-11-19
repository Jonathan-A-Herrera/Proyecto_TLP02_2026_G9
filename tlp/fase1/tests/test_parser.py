"""Pruebas del parser LL(1) de MiniC.   python -m unittest discover -s tests -v"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parser_ll1 import analizar, CONFLICTOS, ErrorSintactico   # noqa: E402
from lexer import ErrorLexico                                  # noqa: E402

VALIDOS = {
    "declaración sin valor": "int x;",
    "declaración con valor": "float y = 3.5;",
    "asignación": "x = 5;",
    "precedencia": "x = 2 + 3 * 4;",
    "paréntesis": "x = (2 + 3) * 4;",
    "if sin else": "if (x > 0) { x = 1; }",
    "if con else": "if (x == 0) { x = 1; } else { x = 2; }",
    "while": "while (i < 10) { i = i + 1; }",
    "anidados": "while (a != b) { if (a > b) { a = a - b; } else { b = b - a; } }",
    "bloque vacío": "if (x > 0) { }",
    "programa vacío": "",
}

INVALIDOS = {
    "falta punto y coma": ("int x = 5", 1),
    "expresión incompleta": ("x = 3 +;", 1),
    "paréntesis sin cerrar": ("x = (2 + 3;", 1),
    "if sin paréntesis": ("if x > 0 { x = 1; }", 1),
    "if sin llaves": ("if (x > 0) x = 1;", 1),
    "else suelto": ("else { x = 2; }", 1),
    "condición sin operador": ("while (x) { x = 1; }", 1),
    "tipo sin identificador": ("int = 4;", 1),
    "llave sin cerrar": ("while (x < 3) { x = 1;", 1),
    "error en la línea 2": ("int a;\na = ;", 2),
}


class Validos(unittest.TestCase):
    def test_validos(self):
        for nombre, codigo in VALIDOS.items():
            with self.subTest(caso=nombre):
                arbol, _ = analizar(codigo)
                self.assertEqual(arbol.simbolo, "programa")

    def test_precedencia_en_el_arbol(self):
        # en 2 + 3 * 4 el '*' queda dentro del segundo término, más abajo que el '+'
        arbol, _ = analizar("x = 2 + 3 * 4;")
        expr = arbol.hijos[0].hijos[0].hijos[0].hijos[2]
        expr_resto = expr.hijos[1]
        self.assertEqual(expr_resto.hijos[0].simbolo, "+")
        termino_resto = expr_resto.hijos[1].hijos[1]
        self.assertEqual(termino_resto.hijos[0].simbolo, "*")

    def test_traza_termina_en_aceptar(self):
        _, pasos = analizar("int x = 1;", traza=True)
        self.assertEqual(pasos[-1][2], "ACEPTAR")


class Invalidos(unittest.TestCase):
    def test_invalidos(self):
        for nombre, (codigo, linea) in INVALIDOS.items():
            with self.subTest(caso=nombre):
                with self.assertRaises(ErrorSintactico) as ctx:
                    analizar(codigo)
                self.assertIn(f"línea {linea}", str(ctx.exception))

    def test_error_lexico(self):
        with self.assertRaises(ErrorLexico):
            analizar("int x = 5 @ 2;")


class Gramatica(unittest.TestCase):
    def test_es_ll1(self):
        self.assertEqual(CONFLICTOS, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

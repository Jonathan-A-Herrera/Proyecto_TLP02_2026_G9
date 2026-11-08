"""
Pruebas del parser de MiniC.
Ejecutar desde la carpeta del proyecto:   python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parser_c import analizar                                   # noqa: E402
from ll1 import construir_tabla                                  # noqa: E402
from gramatica_c import GRAMATICA_C, INICIAL_C                   # noqa: E402

VALIDOS = {
    "declaración simple": "int x;",
    "declaración con valor": "float y = 3.14;",
    "asignación": "x = 5;",
    "precedencia": "x = 2 + 3 * 4;",
    "paréntesis": "x = (2 + 3) * 4;",
    "menos unario": "x = -y + -(3);",
    "if sin else": "if (x > 0) x = 1;",
    "if con else": "if (x == 0) x = 1; else x = 2;",
    "while con bloque": "while (i < 10) { i = i + 1; printf(i); }",
    "bloques anidados": "{ { int a = 1; } { a = 2; } }",
    "programa vacío": "",
    "condición sin operador": "while (x) x = x - 1;",
    "comentarios": "// comentario\nint z = 0; // otro\n",
}

INVALIDOS = {
    "falta punto y coma": ("int x = 5", 1),
    "expresión incompleta": ("x = 3 +;", 1),
    "paréntesis sin cerrar": ("x = (2 + 3;", 1),
    "if sin paréntesis": ("if x > 0 x = 1;", 1),
    "else suelto": ("else x = 2;", 1),
    "tipo sin identificador": ("int = 4;", 1),
    "llave sin cerrar": ("{ x = 1;", 1),
    "dos operadores seguidos": ("x = 2 * / 3;", 1),
    "error en segunda línea": ("int a;\na = ;", 2),
    "operador relacional en asignación": ("x = a < b;", 1),
}


class PruebasValidas(unittest.TestCase):
    def test_validos(self):
        for nombre, codigo in VALIDOS.items():
            with self.subTest(caso=nombre):
                arbol, errores = analizar(codigo)
                self.assertEqual(errores, [], f"{nombre}: {errores}")
                self.assertIsNotNone(arbol)

    def test_precedencia_en_el_arbol(self):
        # En 2 + 3 * 4 la multiplicación debe quedar dentro de un 'termino' (más profundo que el '+')
        arbol, _ = analizar("x = 2 + 3 * 4;")
        expr = arbol.hijos[0].hijos[0].hijos[0].hijos[2]
        self.assertEqual(expr.etiqueta, "expr")
        self.assertEqual(expr.hijos[1].etiqueta, "SUMA")
        segundo_termino = expr.hijos[2]
        self.assertEqual([h.etiqueta for h in segundo_termino.hijos], ["factor", "MULT", "factor"])

    def test_else_colgante(self):
        # El else debe quedar dentro del if interno
        arbol, errores = analizar("if (a) if (b) x = 1; else x = 2;")
        self.assertEqual(errores, [])
        si_externo = arbol.hijos[0].hijos[0].hijos[0]
        self.assertEqual(len(si_externo.hijos), 5)            # el if externo NO tiene 'sino'
        si_interno = si_externo.hijos[4].hijos[0]
        self.assertEqual(si_interno.hijos[-1].etiqueta, "sino")


class PruebasInvalidas(unittest.TestCase):
    def test_invalidos(self):
        for nombre, (codigo, linea) in INVALIDOS.items():
            with self.subTest(caso=nombre):
                _, errores = analizar(codigo)
                self.assertTrue(errores, f"{nombre}: debía fallar")
                self.assertIn(f"Línea {linea}", errores[0])

    def test_error_lexico(self):
        _, errores = analizar("int x = 5 @ 2;")
        self.assertTrue(errores[0].startswith("Error léxico"))

    def test_recuperacion_varios_errores(self):
        # Modo pánico: reporta más de un error en la misma ejecución
        _, errores = analizar("int x = ;\nx = 3 +;\ny = 2;")
        self.assertEqual(len(errores), 2)

    def test_llave_sobrante_no_cicla(self):
        # Antes de corregir sincronizar() esta entrada dejaba al parser en un ciclo infinito
        _, errores = analizar("if (x > 2 { printf(x); }\nx = 1;")
        self.assertTrue(errores)


class PruebasGramatica(unittest.TestCase):
    def test_unico_conflicto_es_else_colgante(self):
        _, conflictos, _, _ = construir_tabla(GRAMATICA_C, INICIAL_C)
        self.assertEqual(list(conflictos.keys()), [("sino", "ELSE")])


if __name__ == "__main__":
    unittest.main(verbosity=2)

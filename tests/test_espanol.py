"""
Pruebas de los intentos de extensión al español.
Documentan como pruebas lo que la CFG SÍ logra y lo que NO logra.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from ll1 import ParserLL1, ErrorLL1                                         # noqa: E402
from gramaticas_espanol import GRAMATICA_V1, GRAMATICA_V2, INICIAL, etiquetar  # noqa: E402
from analisis_fallas import experimento_ambiguedad, experimento_respectivamente  # noqa: E402


def acepta(gramatica, version, oracion):
    parser = ParserLL1(gramatica, INICIAL)
    palabras, cats = etiquetar(oracion, version)
    try:
        parser.analizar(cats, palabras)
        return True
    except ErrorLL1:
        return False


class V1SinConcordancia(unittest.TestCase):
    def test_acepta_oracion_correcta(self):
        self.assertTrue(acepta(GRAMATICA_V1, 1, "El perro negro come"))

    def test_falso_positivo_concordancia(self):
        # Falla documentada: v1 no ve género ni número
        self.assertTrue(acepta(GRAMATICA_V1, 1, "Los gato negra come"))


class V2ConConcordancia(unittest.TestCase):
    def test_rechaza_errores_de_concordancia(self):
        for o in ["Los gato negra come", "El perro negro comen", "La estudiante pequeño lee",
                  "Las niñas que el profesor regañó están cansados"]:
            with self.subTest(oracion=o):
                self.assertFalse(acepta(GRAMATICA_V2, 2, o))

    def test_acepta_concordancia_a_distancia(self):
        self.assertTrue(acepta(GRAMATICA_V2, 2, "Las niñas que el profesor regañó están cansadas"))

    def test_falsos_negativos_orden_libre_y_sujeto_tacito(self):
        for o in ["Llegaron los niños", "Lee un libro", "Ayer los niños comieron mucho"]:
            with self.subTest(oracion=o):
                self.assertFalse(acepta(GRAMATICA_V2, 2, o))


class Ambiguedad(unittest.TestCase):
    def test_numeros_de_catalan(self):
        conteos = [f["arboles"] for f in experimento_ambiguedad(5)]
        self.assertEqual(conteos, [1, 2, 5, 14, 42, 132])


class DependenciasCruzadas(unittest.TestCase):
    def test_ninguna_cfg_probada_acierta(self):
        for f in experimento_respectivamente():
            acierta_a = (f["v3a"] == "acepta") == (f["esperado"] == "G")
            acierta_b = (f["v3b"] == "acepta") == (f["esperado"] == "G")
            if f["esperado"] == "A":
                self.assertFalse(acierta_a)     # v3a acepta oraciones mal emparejadas
            else:
                self.assertFalse(acierta_b)     # v3b rechaza el orden cruzado correcto


if __name__ == "__main__":
    unittest.main(verbosity=2)

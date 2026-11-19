"""
ll1.py
Herramienta genérica para gramáticas LL(1).

Una gramática se representa como un diccionario:
    { "NoTerminal": [ [símbolos de la producción 1], [producción 2], ... ] }
La lista vacía [] representa ε.
Todo símbolo que no sea clave del diccionario se considera terminal.

Funciones:
  - calcular_first, calcular_follow
  - construir_tabla: arma la tabla M[A, a] y reporta CONFLICTOS
    (si hay conflictos, la gramática NO es LL(1))
  - ParserLL1: parser predictivo con pila que usa la tabla y construye el árbol
"""
from arbol import Nodo

EPS = "ε"
FIN = "$"


def es_terminal(simbolo, gramatica):
    return simbolo not in gramatica


def first_de_cadena(simbolos, first, gramatica):
    """FIRST de una secuencia X1 X2 ... Xn."""
    resultado = set()
    for s in simbolos:
        if es_terminal(s, gramatica):
            resultado.add(s)
            return resultado
        resultado |= (first[s] - {EPS})
        if EPS not in first[s]:
            return resultado
    resultado.add(EPS)          # todos los símbolos pueden derivar ε
    return resultado


def calcular_first(gramatica):
    first = {A: set() for A in gramatica}
    cambio = True
    while cambio:                       # punto fijo: se repite hasta que nada cambie
        cambio = False
        for A, producciones in gramatica.items():
            for prod in producciones:
                nuevo = first_de_cadena(prod, first, gramatica)
                if not nuevo <= first[A]:
                    first[A] |= nuevo
                    cambio = True
    return first


def calcular_follow(gramatica, inicial, first):
    follow = {A: set() for A in gramatica}
    follow[inicial].add(FIN)
    cambio = True
    while cambio:
        cambio = False
        for A, producciones in gramatica.items():
            for prod in producciones:
                for i, B in enumerate(prod):
                    if es_terminal(B, gramatica):
                        continue
                    resto = first_de_cadena(prod[i + 1:], first, gramatica)
                    nuevo = resto - {EPS}
                    if EPS in resto:
                        nuevo |= follow[A]
                    if not nuevo <= follow[B]:
                        follow[B] |= nuevo
                        cambio = True
    return follow


def construir_tabla(gramatica, inicial):
    """Devuelve (tabla, conflictos, first, follow).
    tabla[(A, a)] = lista de producciones posibles (más de una = conflicto)."""
    first = calcular_first(gramatica)
    follow = calcular_follow(gramatica, inicial, first)
    tabla = {}
    for A, producciones in gramatica.items():
        for prod in producciones:
            f = first_de_cadena(prod, first, gramatica)
            destinos = (f - {EPS}) | (follow[A] if EPS in f else set())
            for a in destinos:
                tabla.setdefault((A, a), [])
                if prod not in tabla[(A, a)]:
                    tabla[(A, a)].append(prod)
    conflictos = {k: v for k, v in tabla.items() if len(v) > 1}
    return tabla, conflictos, first, follow


def formato_prod(A, prod):
    return f"{A} -> {' '.join(prod) if prod else EPS}"


def contar_producciones(gramatica):
    return sum(len(p) for p in gramatica.values())


class ErrorLL1(Exception):
    pass


class ParserLL1:
    """Parser predictivo con pila. Ante un conflicto aplica la PRIMERA producción
    de la celda (igual que el 'else' se pega al if más cercano) y lo registra:
    así se ve que el parser se queda con UNA sola lectura de una frase ambigua."""

    def __init__(self, gramatica, inicial):
        self.g = gramatica
        self.inicial = inicial
        self.tabla, self.conflictos, self.first, self.follow = construir_tabla(gramatica, inicial)

    def analizar(self, categorias, palabras=None):
        """categorias: lista de terminales (p. ej. ['DET','N','V']).
        palabras: las palabras originales, para mostrarlas en las hojas."""
        palabras = palabras or categorias
        entrada = list(categorias) + [FIN]
        pal = list(palabras) + [""]
        raiz = Nodo(self.inicial)
        pila = [(FIN, None), (self.inicial, raiz)]
        i = 0
        decisiones = []                   # conflictos que se resolvieron al vuelo
        while pila:
            simbolo, nodo = pila.pop()
            a = entrada[i]
            if simbolo == FIN:
                if a == FIN:
                    return raiz, decisiones
                raise ErrorLL1(f"Sobra entrada desde la palabra '{pal[i]}' (posición {i + 1})")
            if es_terminal(simbolo, self.g):
                if simbolo == a:
                    nodo.valor = pal[i]
                    i += 1
                    continue
                raise ErrorLL1(f"Se esperaba {simbolo} y llegó '{pal[i] or 'fin'}' ({a}) en la posición {i + 1}")
            opciones = self.tabla.get((simbolo, a))
            if not opciones:
                esperados = sorted(t for (A, t) in self.tabla if A == simbolo)
                raise ErrorLL1(f"No hay regla para {simbolo} con '{pal[i] or 'fin'}' ({a}) "
                               f"en la posición {i + 1}. Se esperaba uno de: {', '.join(esperados)}")
            if len(opciones) > 1:
                decisiones.append((simbolo, a, [formato_prod(simbolo, p) for p in opciones]))
            prod = opciones[0]
            hijos = [Nodo(s) for s in prod] or [Nodo(EPS, valor="")]
            nodo.hijos = hijos
            for s, h in reversed(list(zip(prod, hijos))):
                pila.append((s, h))
        raise ErrorLL1("Pila vacía antes de terminar")

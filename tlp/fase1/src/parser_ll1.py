"""
parser_ll1.py - Parser predictivo LL(1) dirigido por tabla (algoritmo de Aho et al., cap. 4).

L = la entrada se lee de izquierda a derecha.
L = se construye una derivación por la izquierda.
1 = se mira 1 token de anticipación para decidir.

Algoritmo:
  pila = [$, programa]
  repetir:
    X = tope de la pila, a = token actual
    si X es terminal: si X == a se consumen los dos; si no, error
    si X es no terminal: se busca M[X, a]; si no hay producción, error;
                         si la hay, se saca X y se meten los símbolos de la producción al revés
  hasta que la pila y la entrada lleguen a $ al mismo tiempo
"""
from lexer import tokenizar, ErrorLexico
from gramatica import construir_tabla, es_terminal, formato, FIN, INICIAL, EPS

TABLA, CONFLICTOS, FIRST, FOLLOW = construir_tabla()

NOMBRES = {"id": "un identificador", "num": "un número", "oprel": "un operador relacional (<, >, ==, ...)",
           "$": "fin de archivo"}


class Nodo:
    def __init__(self, simbolo):
        self.simbolo = simbolo
        self.hijos = []
        self.lexema = None

    def texto(self, prefijo="", ultimo=True):
        rama = "└── " if ultimo else "├── "
        etiqueta = self.simbolo if self.lexema is None else f"{self.simbolo}: {self.lexema}"
        lineas = [prefijo + rama + etiqueta]
        for i, h in enumerate(self.hijos):
            lineas.append(h.texto(prefijo + ("    " if ultimo else "│   "), i == len(self.hijos) - 1))
        return "\n".join(lineas)

    def a_nltk(self):
        from nltk import Tree
        if not self.hijos:
            return self.lexema if self.lexema is not None else self.simbolo
        return Tree(self.simbolo, [h.a_nltk() for h in self.hijos])


class ErrorSintactico(Exception):
    pass


def esperados(no_terminal):
    """Terminales que habrían sido válidos: las columnas con producción en la fila del no terminal."""
    return sorted(a for (A, a) in TABLA if A == no_terminal)


def describir(tokens):
    return ", ".join(NOMBRES.get(t, f"'{t}'") for t in tokens)


def analizar(codigo, traza=False):
    """Devuelve (arbol, pasos). Lanza ErrorLexico o ErrorSintactico si la entrada no es válida."""
    tokens = tokenizar(codigo)
    raiz = Nodo(INICIAL)
    pila = [(FIN, None), (INICIAL, raiz)]   # cada elemento: (símbolo, nodo del árbol que le corresponde)
    i = 0
    pasos = []
    while True:
        X, nodo = pila[-1]
        a = tokens[i]
        if traza:
            pasos.append([" ".join(s for s, _ in pila), " ".join(t.lexema if t.tipo != FIN else "$"
                                                                  for t in tokens[i:]), ""])
        if X == FIN and a.tipo == FIN:      # pila vacía y entrada terminada: se acepta
            if traza:
                pasos[-1][2] = "ACEPTAR"
            return raiz, pasos
        if es_terminal(X):
            if X == a.tipo:                 # coincide: se consume
                pila.pop()
                if nodo is not None:
                    nodo.lexema = a.lexema
                i += 1
                if traza:
                    pasos[-1][2] = f"coincide '{a.lexema}'"
                continue
            raise ErrorSintactico(f"Error sintáctico en línea {a.linea}, columna {a.columna}: "
                                  f"se esperaba {describir([X])} y se encontró '{a.lexema}'")
        produccion = TABLA.get((X, a.tipo))
        if produccion is None:              # celda vacía de la tabla: error
            raise ErrorSintactico(f"Error sintáctico en línea {a.linea}, columna {a.columna}: "
                                  f"se encontró '{a.lexema}' pero se esperaba {describir(esperados(X))}")
        pila.pop()
        hijos = [Nodo(s) for s in produccion] or [Nodo(EPS)]
        nodo.hijos = hijos
        for s, h in reversed(list(zip(produccion, hijos))):   # al revés: el primer símbolo queda arriba
            pila.append((s, h))
        if traza:
            pasos[-1][2] = formato(X, produccion)

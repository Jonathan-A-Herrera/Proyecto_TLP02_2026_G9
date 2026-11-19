"""
gramatica.py - Gramática LL(1) de MiniC y cálculo de FIRST, FOLLOW y la tabla predictiva.

MiniC es un subconjunto de C con 4 elementos:
  1. declaración   int x = 5;   float y;
  2. asignación    x = x + 1;
  3. if / else     if (x > 0) { ... } else { ... }
  4. while         while (x < 10) { ... }

Las llaves son obligatorias en if y while. Así la gramática no tiene el problema del
"else colgante" y queda LL(1) sin conflictos.

La gramática se escribe como diccionario: no terminal -> lista de producciones.
Cada producción es una lista de símbolos; [] es ε (cadena vacía).
"""

EPS = "ε"
FIN = "$"
INICIAL = "programa"

GRAMATICA = {
    "programa":    [["sentencias"]],
    "sentencias":  [["sentencia", "sentencias"], []],
    "sentencia":   [["declaracion"], ["asignacion"], ["si"], ["mientras"]],
    "declaracion": [["tipo", "id", "inicial", ";"]],
    "tipo":        [["int"], ["float"]],
    "inicial":     [["=", "expr"], []],
    "asignacion":  [["id", "=", "expr", ";"]],
    "si":          [["if", "(", "cond", ")", "bloque", "sino"]],
    "sino":        [["else", "bloque"], []],
    "mientras":    [["while", "(", "cond", ")", "bloque"]],
    "bloque":      [["{", "sentencias", "}"]],
    "cond":        [["expr", "oprel", "expr"]],
    "expr":        [["termino", "expr'"]],
    "expr'":       [["+", "termino", "expr'"], ["-", "termino", "expr'"], []],
    "termino":     [["factor", "termino'"]],
    "termino'":    [["*", "factor", "termino'"], ["/", "factor", "termino'"], []],
    "factor":      [["(", "expr", ")"], ["id"], ["num"]],
}


def es_terminal(simbolo):
    return simbolo not in GRAMATICA


def first_cadena(simbolos, first):
    """FIRST de una secuencia X1 X2 ... Xn."""
    resultado = set()
    for x in simbolos:
        if es_terminal(x):                 # un terminal es su propio FIRST y corta la cadena
            resultado.add(x)
            return resultado
        resultado |= first[x] - {EPS}
        if EPS not in first[x]:            # si X no puede ser vacío, no se mira lo que sigue
            return resultado
    resultado.add(EPS)                     # todos los símbolos pueden ser vacíos
    return resultado


def calcular_first():
    first = {A: set() for A in GRAMATICA}
    cambio = True
    while cambio:                          # se repite hasta que ningún conjunto crezca (punto fijo)
        cambio = False
        for A, producciones in GRAMATICA.items():
            for p in producciones:
                nuevo = first_cadena(p, first)
                if not nuevo <= first[A]:
                    first[A] |= nuevo
                    cambio = True
    return first


def calcular_follow(first):
    follow = {A: set() for A in GRAMATICA}
    follow[INICIAL].add(FIN)               # regla 1: $ está en FOLLOW del símbolo inicial
    cambio = True
    while cambio:
        cambio = False
        for A, producciones in GRAMATICA.items():
            for p in producciones:
                for i, B in enumerate(p):
                    if es_terminal(B):
                        continue
                    resto = first_cadena(p[i + 1:], first)
                    nuevo = resto - {EPS}          # regla 2: A -> α B β  =>  FIRST(β) en FOLLOW(B)
                    if EPS in resto:
                        nuevo |= follow[A]         # regla 3: si β puede ser vacío, FOLLOW(A) en FOLLOW(B)
                    if not nuevo <= follow[B]:
                        follow[B] |= nuevo
                        cambio = True
    return follow


def construir_tabla():
    """M[A, a] = producción a usar cuando en la pila está A y en la entrada está a.
    Devuelve (tabla, conflictos, first, follow)."""
    first = calcular_first()
    follow = calcular_follow(first)
    tabla, conflictos = {}, []
    for A, producciones in GRAMATICA.items():
        for p in producciones:
            f = first_cadena(p, first)
            terminales = (f - {EPS}) | (follow[A] if EPS in f else set())
            for a in terminales:
                if (A, a) in tabla:
                    conflictos.append((A, a, tabla[(A, a)], p))
                tabla[(A, a)] = p
    return tabla, conflictos, first, follow


def formato(A, p):
    return f"{A} → {' '.join(p) if p else EPS}"

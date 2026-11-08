"""
lexer_c.py
Analizador léxico para el subconjunto de C (MiniC).

Convierte el texto fuente en una lista de tokens (tipo, lexema, línea, columna).
Usa expresiones regulares: el nivel léxico es un lenguaje regular (Tipo 3 de Chomsky).
"""
import re

PALABRAS_RESERVADAS = {"int", "float", "if", "else", "while", "printf"}

# El orden importa: el comentario va antes que "/" y los operadores de dos caracteres antes que los de uno.
ESPECIFICACION = [
    ("COMENT",   r"//[^\n]*"),     # antes que "/" para no confundirlo con división
    ("NUM",      r"\d+(\.\d+)?"),
    ("ID",       r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OPREL",    r"<=|>=|==|!=|<|>"),
    ("ASIGNA",   r"="),
    ("SUMA",     r"[+\-]"),
    ("MULT",     r"[*/]"),
    ("PAR_IZQ",  r"\("),
    ("PAR_DER",  r"\)"),
    ("LLAVE_IZQ", r"\{"),
    ("LLAVE_DER", r"\}"),
    ("PYC",      r";"),
    ("SALTO",    r"\n"),
    ("ESPACIO",  r"[ \t\r]+"),
    ("ERROR",    r"."),
]

PATRON = re.compile("|".join(f"(?P<{n}>{p})" for n, p in ESPECIFICACION))


class Token:
    def __init__(self, tipo, lexema, linea, columna):
        self.tipo = tipo
        self.lexema = lexema
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"<{self.tipo} '{self.lexema}' {self.linea}:{self.columna}>"


class ErrorLexico(Exception):
    pass


def tokenizar(codigo):
    tokens = []
    linea, inicio_linea = 1, 0
    for m in PATRON.finditer(codigo):
        tipo, lexema = m.lastgroup, m.group()
        columna = m.start() - inicio_linea + 1
        if tipo == "SALTO":
            linea += 1
            inicio_linea = m.end()
            continue
        if tipo in ("ESPACIO", "COMENT"):
            continue
        if tipo == "ERROR":
            raise ErrorLexico(f"Línea {linea}, columna {columna}: carácter no reconocido '{lexema}'")
        if tipo == "ID" and lexema in PALABRAS_RESERVADAS:
            tipo = lexema.upper()          # int -> INT, if -> IF, etc.
        tokens.append(Token(tipo, lexema, linea, columna))
    tokens.append(Token("EOF", "", linea, 1))
    return tokens

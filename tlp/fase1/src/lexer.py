"""
lexer.py - Analizador léxico de MiniC.

Recorre el texto con una expresión regular y lo convierte en una lista de tokens.
Cada token guarda su tipo, el texto original (lexema), la línea y la columna.
Los tokens son los TERMINALES de la gramática.
"""
import re

# Palabras reservadas: se reconocen primero como identificador y luego se reclasifican.
RESERVADAS = {"int", "float", "if", "else", "while"}

# (tipo de token, patrón). El orden importa: "==" debe probarse antes que "=".
PATRONES = [
    ("num",     r"\d+(?:\.\d+)?"),
    ("id",      r"[A-Za-z_]\w*"),
    ("oprel",   r"==|!=|<=|>=|<|>"),
    ("=",       r"="),
    ("+",       r"\+"),
    ("-",       r"-"),
    ("*",       r"\*"),
    ("/",       r"/"),
    ("(",       r"\("),
    (")",       r"\)"),
    ("{",       r"\{"),
    ("}",       r"\}"),
    (";",       r";"),
    ("SALTO",   r"\n"),
    ("ESPACIO", r"[ \t\r]+"),
    ("ERROR",   r"."),
]
REGEX = re.compile("|".join(f"(?P<g{i}>{p})" for i, (_, p) in enumerate(PATRONES)))


class Token:
    def __init__(self, tipo, lexema, linea, columna):
        self.tipo, self.lexema, self.linea, self.columna = tipo, lexema, linea, columna

    def __repr__(self):
        return f"{self.tipo}({self.lexema})"


class ErrorLexico(Exception):
    pass


def tokenizar(codigo):
    tokens, linea, inicio_linea = [], 1, 0
    for m in REGEX.finditer(codigo):
        tipo = PATRONES[int(m.lastgroup[1:])][0]
        lexema = m.group()
        columna = m.start() - inicio_linea + 1
        if tipo == "SALTO":
            linea, inicio_linea = linea + 1, m.end()
        elif tipo == "ESPACIO":
            continue
        elif tipo == "ERROR":
            raise ErrorLexico(f"Error léxico en línea {linea}, columna {columna}: símbolo '{lexema}' no válido")
        else:
            if tipo == "id" and lexema in RESERVADAS:
                tipo = lexema                      # "if" deja de ser id y pasa a ser el token if
            tokens.append(Token(tipo, lexema, linea, columna))
    ult = tokens[-1] if tokens else None
    col_fin = ult.columna + len(ult.lexema) if ult else 1
    tokens.append(Token("$", "fin de archivo", ult.linea if ult else linea, col_fin))   # marca de fin
    return tokens

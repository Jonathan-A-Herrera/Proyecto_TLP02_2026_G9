"""
gramatica_c.py
La misma gramática de parser_c.py, escrita como diccionario para que ll1.py
calcule FIRST, FOLLOW y la tabla LL(1) y verifique formalmente si hay conflictos.
"""

GRAMATICA_C = {
    "programa":    [["lista_sent"]],
    "lista_sent":  [["sentencia", "lista_sent"], []],
    "sentencia":   [["declaracion"], ["asignacion"], ["si"], ["mientras"], ["bloque"], ["imprimir"]],
    "declaracion": [["tipo", "ID", "decl_ini", "PYC"]],
    "tipo":        [["INT"], ["FLOAT"]],
    "decl_ini":    [["ASIGNA", "expr"], []],
    "asignacion":  [["ID", "ASIGNA", "expr", "PYC"]],
    "si":          [["IF", "PAR_IZQ", "cond", "PAR_DER", "sentencia", "sino"]],
    "sino":        [["ELSE", "sentencia"], []],
    "mientras":    [["WHILE", "PAR_IZQ", "cond", "PAR_DER", "sentencia"]],
    "bloque":      [["LLAVE_IZQ", "lista_sent", "LLAVE_DER"]],
    "imprimir":    [["PRINTF", "PAR_IZQ", "expr", "PAR_DER", "PYC"]],
    "cond":        [["expr", "cond_resto"]],
    "cond_resto":  [["OPREL", "expr"], []],
    "expr":        [["termino", "expr_resto"]],
    "expr_resto":  [["SUMA", "termino", "expr_resto"], []],
    "termino":     [["factor", "term_resto"]],
    "term_resto":  [["MULT", "factor", "term_resto"], []],
    "factor":      [["NUM"], ["ID"], ["PAR_IZQ", "expr", "PAR_DER"], ["SUMA", "factor"]],
}
INICIAL_C = "programa"

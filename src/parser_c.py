"""
parser_c.py
Parser descendente recursivo para MiniC, un subconjunto de C.

Gramática (LL(1), sin recursión por la izquierda y factorizada):

    programa     -> lista_sent EOF
    lista_sent   -> sentencia lista_sent | ε
    sentencia    -> declaracion | asignacion | si | mientras | bloque | imprimir
    declaracion  -> tipo ID decl_ini ';'
    tipo         -> 'int' | 'float'
    decl_ini     -> '=' expr | ε
    asignacion   -> ID '=' expr ';'
    si           -> 'if' '(' cond ')' sentencia sino
    sino         -> 'else' sentencia | ε
    mientras     -> 'while' '(' cond ')' sentencia
    bloque       -> '{' lista_sent '}'
    imprimir     -> 'printf' '(' expr ')' ';'
    cond         -> expr cond_resto
    cond_resto   -> OPREL expr | ε
    expr         -> termino expr_resto
    expr_resto   -> ('+' | '-') termino expr_resto | ε
    termino      -> factor term_resto
    term_resto   -> ('*' | '/') factor term_resto | ε
    factor       -> NUM | ID | '(' expr ')' | '-' factor

Cada no terminal es una función. La función mira el token actual (1 token de
lookahead) y decide qué producción aplicar: eso es lo que hace al parser LL(1).
"""
from lexer_c import tokenizar, ErrorLexico
from arbol import Nodo

# Tokens con los que puede empezar una sentencia: conjunto FIRST(sentencia)
FIRST_SENTENCIA = {"INT", "FLOAT", "ID", "IF", "WHILE", "LLAVE_IZQ", "PRINTF"}


class ErrorSintactico(Exception):
    def __init__(self, token, esperado):
        self.token = token
        self.esperado = esperado
        encontrado = token.lexema if token.tipo != "EOF" else "fin de archivo"
        super().__init__(
            f"Línea {token.linea}, columna {token.columna}: se esperaba {esperado} "
            f"pero se encontró '{encontrado}'"
        )


class ParserC:
    def __init__(self, codigo):
        self.tokens = tokenizar(codigo)
        self.pos = 0
        self.errores = []

    # ---------- utilidades ----------
    @property
    def actual(self):
        return self.tokens[self.pos]

    def coincidir(self, tipo, descripcion=None):
        """Consume el token si es del tipo esperado; si no, lanza error."""
        tok = self.actual
        if tok.tipo != tipo:
            raise ErrorSintactico(tok, descripcion or tipo)
        self.pos += 1
        return Nodo(tipo, valor=tok.lexema)

    def sincronizar(self):
        """Recuperación en modo pánico: avanza hasta ';' o '}' para seguir analizando."""
        inicio = self.pos
        while self.actual.tipo not in ("PYC", "LLAVE_DER", "EOF"):
            self.pos += 1
        if self.actual.tipo == "PYC":
            self.pos += 1
        elif self.pos == inicio and self.actual.tipo != "EOF":
            self.pos += 1           # una '}' sobrante: se salta para no quedar en un ciclo infinito

    # ---------- reglas de la gramática ----------
    def programa(self):
        nodo = Nodo("programa")
        nodo.agregar(self.lista_sent(fin="EOF"))
        if self.actual.tipo != "EOF":
            raise ErrorSintactico(self.actual, "fin de archivo")
        return nodo

    def lista_sent(self, fin):
        nodo = Nodo("lista_sent")
        while self.actual.tipo != fin and self.actual.tipo != "EOF":
            try:
                nodo.agregar(self.sentencia())
            except ErrorSintactico as e:
                self.errores.append(str(e))
                self.sincronizar()
        return nodo

    def sentencia(self):
        t = self.actual.tipo
        nodo = Nodo("sentencia")
        if t in ("INT", "FLOAT"):
            nodo.agregar(self.declaracion())
        elif t == "ID":
            nodo.agregar(self.asignacion())
        elif t == "IF":
            nodo.agregar(self.si())
        elif t == "WHILE":
            nodo.agregar(self.mientras())
        elif t == "LLAVE_IZQ":
            nodo.agregar(self.bloque())
        elif t == "PRINTF":
            nodo.agregar(self.imprimir())
        else:
            raise ErrorSintactico(self.actual, "inicio de sentencia (int, float, id, if, while, {, printf)")
        return nodo

    def declaracion(self):
        nodo = Nodo("declaracion")
        nodo.agregar(self.tipo())
        nodo.agregar(self.coincidir("ID", "un identificador"))
        if self.actual.tipo == "ASIGNA":            # decl_ini -> '=' expr
            nodo.agregar(self.coincidir("ASIGNA"))
            nodo.agregar(self.expr())
        nodo.agregar(self.coincidir("PYC", "';'"))  # decl_ini -> ε si no hay '='
        return nodo

    def tipo(self):
        nodo = Nodo("tipo")
        if self.actual.tipo == "INT":
            nodo.agregar(self.coincidir("INT"))
        else:
            nodo.agregar(self.coincidir("FLOAT", "un tipo (int o float)"))
        return nodo

    def asignacion(self):
        nodo = Nodo("asignacion")
        nodo.agregar(self.coincidir("ID"))
        nodo.agregar(self.coincidir("ASIGNA", "'='"))
        nodo.agregar(self.expr())
        nodo.agregar(self.coincidir("PYC", "';'"))
        return nodo

    def si(self):
        nodo = Nodo("si")
        nodo.agregar(self.coincidir("IF"))
        nodo.agregar(self.coincidir("PAR_IZQ", "'('"))
        nodo.agregar(self.cond())
        nodo.agregar(self.coincidir("PAR_DER", "')'"))
        nodo.agregar(self.sentencia())
        # Problema del 'else colgante': 'else' está en FIRST(sino) y en FOLLOW(sino).
        # Se resuelve como en C: el else se asocia al if más cercano.
        if self.actual.tipo == "ELSE":
            sino = Nodo("sino")
            sino.agregar(self.coincidir("ELSE"))
            sino.agregar(self.sentencia())
            nodo.agregar(sino)
        return nodo

    def mientras(self):
        nodo = Nodo("mientras")
        nodo.agregar(self.coincidir("WHILE"))
        nodo.agregar(self.coincidir("PAR_IZQ", "'('"))
        nodo.agregar(self.cond())
        nodo.agregar(self.coincidir("PAR_DER", "')'"))
        nodo.agregar(self.sentencia())
        return nodo

    def bloque(self):
        nodo = Nodo("bloque")
        nodo.agregar(self.coincidir("LLAVE_IZQ"))
        nodo.agregar(self.lista_sent(fin="LLAVE_DER"))
        nodo.agregar(self.coincidir("LLAVE_DER", "'}'"))
        return nodo

    def imprimir(self):
        nodo = Nodo("imprimir")
        nodo.agregar(self.coincidir("PRINTF"))
        nodo.agregar(self.coincidir("PAR_IZQ", "'('"))
        nodo.agregar(self.expr())
        nodo.agregar(self.coincidir("PAR_DER", "')'"))
        nodo.agregar(self.coincidir("PYC", "';'"))
        return nodo

    def cond(self):
        nodo = Nodo("cond")
        nodo.agregar(self.expr())
        if self.actual.tipo == "OPREL":
            nodo.agregar(self.coincidir("OPREL"))
            nodo.agregar(self.expr())
        return nodo

    # expr -> termino expr_resto ; la recursión de expr_resto se hace con un while
    def expr(self):
        nodo = Nodo("expr")
        nodo.agregar(self.termino())
        while self.actual.tipo == "SUMA":
            nodo.agregar(self.coincidir("SUMA"))
            nodo.agregar(self.termino())
        return nodo

    def termino(self):
        nodo = Nodo("termino")
        nodo.agregar(self.factor())
        while self.actual.tipo == "MULT":
            nodo.agregar(self.coincidir("MULT"))
            nodo.agregar(self.factor())
        return nodo

    def factor(self):
        nodo = Nodo("factor")
        t = self.actual.tipo
        if t == "NUM":
            nodo.agregar(self.coincidir("NUM"))
        elif t == "ID":
            nodo.agregar(self.coincidir("ID"))
        elif t == "PAR_IZQ":
            nodo.agregar(self.coincidir("PAR_IZQ"))
            nodo.agregar(self.expr())
            nodo.agregar(self.coincidir("PAR_DER", "')'"))
        elif t == "SUMA" and self.actual.lexema == "-":
            nodo.agregar(self.coincidir("SUMA"))
            nodo.agregar(self.factor())
        else:
            raise ErrorSintactico(self.actual, "un número, identificador o '('")
        return nodo


def analizar(codigo):
    """Devuelve (arbol, errores). Si la lista de errores está vacía, la entrada es válida."""
    try:
        parser = ParserC(codigo)
    except ErrorLexico as e:
        return None, [f"Error léxico: {e}"]
    try:
        arbol = parser.programa()
    except ErrorSintactico as e:
        parser.errores.append(str(e))
        arbol = None
    return arbol, parser.errores

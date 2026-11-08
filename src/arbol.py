"""
arbol.py
Representación del árbol de análisis sintáctico (árbol de derivación).

Cada nodo guarda una etiqueta (no terminal o token) y una lista de hijos.
Las hojas son los tokens reales de la entrada.
"""


class Nodo:
    def __init__(self, etiqueta, hijos=None, valor=None):
        self.etiqueta = etiqueta      # p. ej. "Sentencia", "Expr", "ID"
        self.hijos = hijos or []      # lista de Nodo
        self.valor = valor            # lexema si es hoja (p. ej. "x", "10")

    def agregar(self, hijo):
        self.hijos.append(hijo)
        return hijo

    def es_hoja(self):
        return not self.hijos

    def __repr__(self):
        if self.valor is not None:
            return f"{self.etiqueta}({self.valor})"
        return self.etiqueta

    def imprimir(self, prefijo="", ultimo=True):
        """Devuelve el árbol en texto con ramas, para verlo en la terminal."""
        conector = "└── " if ultimo else "├── "
        texto = self.etiqueta if self.valor is None else f"{self.etiqueta}: '{self.valor}'"
        lineas = [prefijo + conector + texto]
        nuevo_prefijo = prefijo + ("    " if ultimo else "│   ")
        for i, hijo in enumerate(self.hijos):
            lineas.append(hijo.imprimir(nuevo_prefijo, i == len(self.hijos) - 1))
        return "\n".join(lineas)

    def a_nltk(self):
        """Convierte el árbol a nltk.Tree (sirve para dibujarlo con .draw() o pretty_print())."""
        from nltk import Tree
        if self.es_hoja():
            return self.valor if self.valor is not None else self.etiqueta
        return Tree(self.etiqueta, [h.a_nltk() for h in self.hijos])

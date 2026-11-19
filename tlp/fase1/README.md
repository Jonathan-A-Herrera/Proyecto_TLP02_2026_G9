# Proyecto TLP02-2026, Fase 1
## Parser descendente LL(1) para MiniC (subconjunto de C con 4 elementos)

Herrera Salinas, Jonathan Alcides (00379823).

MiniC acepta cuatro construcciones de C:

| Elemento | Ejemplo |
| --- | --- |
| Declaración | `int x = 5;`  `float y;` |
| Asignación | `x = (x + 2) * 3;` |
| if / else | `if (x > 0) { ... } else { ... }` |
| while | `while (i < 10) { ... }` |

Las expresiones admiten `+ - * /`, paréntesis, identificadores y números; las condiciones usan
`< > <= >= == !=`. Las llaves son obligatorias en `if` y `while`, por eso la gramática no tiene
el conflicto del "else colgante" y es LL(1) sin conflictos (17 no terminales, 30 producciones, 60 celdas en la tabla).

## Archivos

```
fase1/
├── demo.py            menú para la demostración
├── src/
│   ├── lexer.py       analizador léxico (expresiones regulares)
│   ├── gramatica.py   gramática, FIRST, FOLLOW y tabla LL(1)
│   └── parser_ll1.py  parser predictivo con pila, árbol y mensajes de error
├── tests/test_parser.py
└── ejemplos/          valido.c, con_error.c, corto.c
```

## Ejecución

Solo necesita Python 3.10 o superior; `nltk` es opcional, para dibujar el árbol en una ventana.

```bash
cd fase1
python demo.py                          # menú
python demo.py gramatica
python demo.py first                    # FIRST y FOLLOW
python demo.py tabla                    # tabla LL(1)
python demo.py traza ejemplos/corto.c   # pila paso a paso y árbol
python demo.py analizar ejemplos/valido.c
python demo.py analizar ejemplos/con_error.c
python demo.py pruebas
```

En Windows se usa `python` o `py` igual. Agregar `--ventana` a `traza` o `analizar` abre el árbol con NLTK.

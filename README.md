# Proyecto TLP02-2026, Fase 1
## Gramáticas formales y lenguaje natural: experimentando los límites de la jerarquía de Chomsky

Teoría de Lenguajes de Programación, UCA, ciclo 02-2026.

| Integrante | Carnet |
| --- | --- |
| Herrera Salinas, Jonathan Alcides | 00379823 |
| Hernández Godoy, Jonathan Daniel | 00015322 |
| Alvarado Sibrian, Diego Fernando | 00127522 |

## Qué contiene

1. Un parser descendente recursivo para **MiniC**, un subconjunto de C (declaraciones `int`/`float`, asignaciones, `if`/`else`, `while`, bloques, `printf` y expresiones aritméticas y relacionales). Construye el árbol de análisis sintáctico y reporta errores con línea y columna, con recuperación en modo pánico.
2. Una herramienta LL(1) genérica que calcula FIRST, FOLLOW, la tabla predictiva y sus conflictos.
3. Tres intentos de extender la gramática al español (v1 sin concordancia, v2 con concordancia, v3 con dependencias cruzadas) y los experimentos que muestran dónde fallan.
4. Una comparación con spaCy y con una gramática de rasgos de NLTK sobre las mismas 23 oraciones.

## Estructura

```
tlp-fase1/
├── demo.py                      menú y comandos para la demostración en vivo
├── requirements.txt
├── src/
│   ├── lexer_c.py               analizador léxico de MiniC
│   ├── parser_c.py              parser descendente recursivo de MiniC
│   ├── gramatica_c.py           la gramática de MiniC como diccionario
│   ├── ll1.py                   FIRST, FOLLOW, tabla LL(1), conflictos y parser predictivo
│   ├── arbol.py                 clase Nodo del árbol sintáctico
│   ├── gramaticas_espanol.py    léxico y gramáticas v1, v2, v3 del español
│   ├── analisis_fallas.py       experimentos de los puntos de falla
│   └── demo_nlp.py              comparación con spaCy y NLTK
├── tests/
│   ├── test_parser_c.py         casos válidos e inválidos de MiniC
│   └── test_espanol.py          lo que la CFG logra y lo que no
├── ejemplos/                    programas MiniC y oraciones de prueba
└── salidas/                     resultados generados (txt y json)
```

## Instalación

Se necesita Python 3.10, 3.11 o 3.12.

### macOS (incluye Apple Silicon M1 a M4)

```bash
cd tlp-fase1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

### Windows (PowerShell)

```powershell
cd tlp-fase1
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

Si PowerShell no deja activar el entorno, ejecutar una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repetir la activación.
En CMD la activación es `.venv\Scripts\activate.bat`.

## Ejecución

Menú interactivo (recomendado para la presentación):

```bash
python demo.py
```

Comandos directos:

```bash
python demo.py c ejemplos/programa_valido.c        # programa válido y su árbol
python demo.py c ejemplos/programa_con_errores.c   # varios errores reportados
python demo.py c ejemplos/else_colgante.c          # else asociado al if más cercano
python demo.py c "int x = 2 + 3 * 4;"              # código escrito en la línea
python demo.py tabla                               # FIRST, FOLLOW y conflictos de MiniC
python demo.py es "Las niñas que el profesor regañó están cansadas"
python demo.py fallas                              # experimentos de los puntos de falla
python demo.py nlp                                 # comparación con spaCy y NLTK
python demo.py pruebas                             # pruebas unitarias
```

Agregar `--ventana` a `c` o `es` abre el árbol en una ventana gráfica de NLTK (requiere Tkinter; en Mac con Homebrew: `brew install python-tk`).

Las pruebas también se corren con:

```bash
python -m unittest discover -s tests -v
```

## Vocabulario del español

El parser del español solo reconoce las palabras de `src/gramaticas_espanol.py` (variable `LEXICO`): determinantes (el, la, los, las, un, una), sustantivos (niño, perro, gato, profesor, libro, parque, telescopio, casa, mesa, estudiante y sus flexiones), adjetivos (negro, pequeño, cansado, alto, feliz, grande), verbos en presente y pretérito (come, comió, ve, vio, ladra, duerme, lee, dice, regaña, llega...), cópulas (es, son, está, están), adverbios, preposiciones (con, en, de, sobre), "que" y los nombres Ana, Marta, Luis y Pedro.

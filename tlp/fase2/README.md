# Proyecto TLP02-2026, Fase 2
## Benchmark: parser propio frente a spaCy, NLTK y un LLM

Teoría de Lenguajes de Programación, UCA, ciclo 02-2026.
Herrera Salinas, Jonathan Alcides (00379823).

El mismo corpus de 48 oraciones del español se pasa por cuatro enfoques y se comparan con métricas:

| Enfoque | Qué es | Script |
| --- | --- | --- |
| Parser propio | Parser predictivo LL(1) sobre nuestra CFG v2 (concordancia en los no terminales) | `src/correr_locales.py` |
| spaCy | Modelo estadístico `es_core_news_sm` + regla de aceptación por concordancia | `src/correr_locales.py` |
| NLTK | `FeatureChartParser` con gramática de rasgos | `src/correr_locales.py` |
| LLM | Modelo vía API con las reglas de la CFG en el prompt, en variantes zero-shot y few-shot | `src/correr_llm.py` |

## Estructura

```
fase2/
├── corpus/
│   ├── oraciones.txt          oraciones con nivel y etiqueta esperada (escritas a mano)
│   └── corpus.csv             corpus final: etiqueta, pertenencia a L(G) y categorías esperadas
├── src/
│   ├── gramaticas_espanol.py  léxico y CFG v2 del español
│   ├── ll1.py, arbol.py       tabla LL(1), parser predictivo y árbol
│   ├── comun.py               lectura del corpus y formato de los logs
│   ├── preparar_corpus.py     genera corpus/corpus.csv
│   ├── correr_locales.py      parser propio, spaCy y NLTK
│   ├── correr_llm.py          LLM zero-shot y few-shot
│   └── evaluar.py             calcula las métricas, las tablas y las gráficas
├── prompts/                   prompts exactos enviados al LLM
├── logs/                      salida bruta de cada enfoque (anexo del informe)
└── resultados/                tablas (csv y md) y gráficas (png)
```

## Cómo reproducir los experimentos

Requiere Python 3.10 a 3.13.

### 1. Instalar

macOS / Linux:
```bash
cd fase2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

Windows (PowerShell):
```powershell
cd fase2
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

### 2. Generar el corpus y correr los enfoques locales

```bash
python src/preparar_corpus.py
python src/correr_locales.py
```

### 3. Correr el LLM

La clave de API se pasa como variable de entorno; nunca se guarda en el código ni en los logs.

```bash
export GEMINI_API_KEY="clave"                    # Windows: $env:GEMINI_API_KEY="clave"
python src/correr_llm.py --listar-modelos           # ver los modelos disponibles
python src/correr_llm.py --proveedor gemini --modelo gemini-2.5-flash
```

Corre 96 llamadas (48 zero-shot y 48 few-shot) con temperatura 0 y una pausa de 7 s entre llamadas
para respetar el límite gratuito. Si la corrida se interrumpe, al ejecutarla otra vez continúa donde quedó.
También acepta `--proveedor anthropic` (variable `ANTHROPIC_API_KEY`) y `--proveedor openai` (`OPENAI_API_KEY`).

### 4. Calcular las métricas

```bash
python src/evaluar.py
```

Escribe `resultados/metricas.csv`, `metricas_por_nivel.csv`, `detalle_por_oracion.csv`,
`llm_frente_a_reglas.csv`, `tablas.md` y las gráficas `grafica_metricas.png` y `grafica_niveles.png`.
Con los mismos logs produce siempre las mismas tablas.

## Definiciones

La clase positiva es ACEPTA y la referencia es la columna `esperado` (si la oración es correcta en español).

- Precisión = VP / (VP + FP)
- Cobertura (recall) = VP / (VP + FN)
- Tasa de rechazo correcto = VN / (VN + FP)
- Error de etiquetado: oración aceptada correctamente cuya secuencia de categorías difiere de la esperada
- Fidelidad a L(G): porcentaje de oraciones en que el veredicto coincide con la columna `en_gramatica`,
  calculada de forma exacta con el ChartParser de NLTK sobre la misma CFG. Mide si un enfoque sigue las reglas.

## Contenido de los logs

- `logs/parser_propio.json`, `logs/spacy.json`, `logs/nltk.json`: una entrada por oración con el veredicto,
  las categorías y el árbol o el motivo del rechazo, más las versiones de las librerías.
- `logs/llm_zero_shot_llamadas.jsonl` y `logs/llm_few_shot_llamadas.jsonl`: una línea por llamada a la API
  con timestamp de envío y de respuesta, modelo, temperatura, prompt de sistema y de usuario exactos,
  respuesta de texto y respuesta completa de la API.
- `logs/llm_zero_shot.json` y `logs/llm_few_shot.json`: el resumen de esas llamadas en el formato común.

"""
demo_nlp.py
Procesa las MISMAS oraciones del conjunto de prueba con dos herramientas de NLP:

  1. spaCy (modelo estadístico es_core_news_sm): etiquetas, rasgos morfológicos
     (género, número) y árbol de dependencias. Nunca "rechaza" una oración:
     siempre devuelve el análisis más probable.
  2. NLTK con una gramática de RASGOS (FCFG): la concordancia se expresa con
     variables (?g, ?n) que se unifican, en vez de duplicar no terminales.

Uso:  python src/demo_nlp.py
"""
import os
import json
import nltk
from nltk.grammar import FeatureGrammar
from nltk.parse import FeatureChartParser

from gramaticas_espanol import LEXICO, separar
from analisis_fallas import leer_oraciones, RAIZ

# ---------------------------------------------------------------------------
# 1. spaCy
# ---------------------------------------------------------------------------
_nlp = None


def cargar_spacy():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("es_core_news_sm")
    return _nlp


def rasgo(token, nombre):
    v = token.morph.get(nombre)
    return v[0] if v else None


def revisar_concordancia(doc):
    """Reglas simples sobre la salida de spaCy: compara género y número entre
    palabras que spaCy relacionó (determinante/adjetivo con su núcleo, sujeto con su verbo)."""
    problemas = []
    for t in doc:
        if t.dep_ in ("det", "amod") or (t.dep_ == "ROOT" and t.pos_ == "ADJ"):
            objetivo = t.head if t.dep_ != "ROOT" else next((h for h in t.children if h.dep_ == "nsubj"), None)
            if objetivo is None:
                continue
            for r in ("Gender", "Number"):
                a, b = rasgo(t, r), rasgo(objetivo, r)
                if a and b and a != b:
                    problemas.append(f"{r}: '{t.text}'={a} vs '{objetivo.text}'={b}")
        if t.dep_ == "nsubj" and t.head.pos_ in ("VERB", "AUX"):
            a, b = rasgo(t, "Number"), rasgo(t.head, "Number")
            if a and b and a != b:
                problemas.append(f"Number: sujeto '{t.text}'={a} vs verbo '{t.head.text}'={b}")
    return problemas


def analizar_spacy(oracion):
    doc = cargar_spacy()(oracion)
    tokens = [{"texto": t.text, "pos": t.pos_, "dep": t.dep_, "nucleo": t.head.text,
               "genero": rasgo(t, "Gender"), "numero": rasgo(t, "Number")} for t in doc]
    return doc, tokens, revisar_concordancia(doc)


def imprimir_spacy(doc):
    lineas = [f"    {'palabra':14}{'POS':7}{'dep':10}{'núcleo':14}{'gén':5}{'núm':5}"]
    for t in doc:
        lineas.append(f"    {t.text:14}{t.pos_:7}{t.dep_:10}{t.head.text:14}"
                      f"{(rasgo(t, 'Gender') or '-'):5}{(rasgo(t, 'Number') or '-'):5}")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# 2. NLTK con gramática de rasgos
# ---------------------------------------------------------------------------
REGLAS_FCFG = r"""
% start O
O -> SN[GEN=?g, NUM=?n] SV[GEN=?g, NUM=?n]
SN[GEN=?g, NUM=?n] -> DET[GEN=?g, NUM=?n] N[GEN=?g, NUM=?n] MODS[GEN=?g, NUM=?n]
SN[GEN=?g, NUM=s] -> NP[GEN=?g]
MODS[GEN=?g, NUM=?n] ->
MODS[GEN=?g, NUM=?n] -> ADJ[GEN=?g, NUM=?n] MODS[GEN=?g, NUM=?n]
MODS[GEN=?g, NUM=?n] -> SP MODS[GEN=?g, NUM=?n]
MODS[GEN=?g, NUM=?n] -> REL[GEN=?g, NUM=?n] MODS[GEN=?g, NUM=?n]
REL[GEN=?g, NUM=?n] -> QUE SV[GEN=?g, NUM=?n]
REL[GEN=?g, NUM=?n] -> QUE SN[GEN=?h, NUM=?m] SVH[NUM=?m]
SVH[NUM=?n] -> ADVS V[NUM=?n] MODSV
SP -> PREP SN
SV[GEN=?g, NUM=?n] -> ADVS V[NUM=?n] COMP
SV[GEN=?g, NUM=?n] -> ADVS COP[NUM=?n] ADJ[GEN=?g, NUM=?n] MODSV
COMP -> SN MODSV
COMP -> MODSV
ADVS ->
ADVS -> ADV ADVS
MODSV ->
MODSV -> ADV MODSV
MODSV -> SP MODSV
MODSV -> QUE O
"""


def construir_fcfg():
    """Agrega las reglas léxicas. El género común ('c') queda SIN especificar,
    así la unificación lo deja concordar con masculino o femenino."""
    lineas = [REGLAS_FCFG.strip()]
    for palabra, entradas in LEXICO.items():
        cat, g, n = entradas[0]
        if cat in ("SEP", "RESP"):
            continue
        rasgos = []
        if g in ("m", "f"):
            rasgos.append(f"GEN={g}")
        if n in ("s", "p"):
            rasgos.append(f"NUM={n}")
        etiqueta = f"{cat}[{', '.join(rasgos)}]" if rasgos else cat
        lineas.append(f"{etiqueta} -> '{palabra}'")
    return FeatureGrammar.fromstring("\n".join(lineas))


def contar_reglas_sintacticas():
    return sum(1 for l in REGLAS_FCFG.strip().splitlines() if "->" in l)


def analizar_fcfg(parser, oracion):
    try:
        arboles = list(parser.parse(separar(oracion)))
    except ValueError:
        return 0, None
    return len(arboles), (arboles[0] if arboles else None)


# ---------------------------------------------------------------------------
def ejecutar_todo(guardar=True, mostrar_tokens=True):
    salida = []
    p = salida.append
    oraciones = leer_oraciones()
    parser_fcfg = FeatureChartParser(construir_fcfg())

    p("=" * 100)
    p("COMPARACIÓN CON NLP: spaCy (estadístico) y NLTK (gramática de rasgos)")
    p(f"Gramática de rasgos de NLTK: {contar_reglas_sintacticas()} reglas sintácticas "
      f"(la v2 sin rasgos necesitó 95 producciones para lo mismo)")
    p("=" * 100)
    resultados = []
    for i, d in enumerate(oraciones, 1):
        doc, tokens, problemas = analizar_spacy(d["oracion"])
        n_fcfg, _ = analizar_fcfg(parser_fcfg, d["oracion"])
        raiz = [t.text for t in doc if t.dep_ == "ROOT"]
        fila = {**d, "spacy_analiza": True, "spacy_raiz": raiz[0] if raiz else None,
                "spacy_inconsistencias": problemas, "spacy_tokens": tokens,
                "nltk_fcfg_arboles": n_fcfg, "nltk_fcfg": "acepta" if n_fcfg else "rechaza"}
        # Dónde pegó spaCy la frase "con el telescopio"
        for t in doc:
            if t.text == "telescopio":
                fila["spacy_adjuncion_telescopio"] = t.head.text
        resultados.append(fila)

        p(f"{i:2}. [{d['esperado']}] {d['oracion']}")
        p(f"    spaCy: siempre produce un análisis (raíz = '{fila['spacy_raiz']}'); "
          f"inconsistencias de concordancia detectadas: {problemas if problemas else 'ninguna'}")
        if "spacy_adjuncion_telescopio" in fila:
            p(f"    spaCy eligió UNA sola lectura: 'telescopio' depende de '{fila['spacy_adjuncion_telescopio']}'")
        p(f"    NLTK con rasgos: {fila['nltk_fcfg']} ({n_fcfg} árbol(es))")
        if mostrar_tokens:
            p(imprimir_spacy(doc))

    # Resumen cuantitativo
    p("=" * 100)
    p("RESUMEN")
    agram = [r for r in resultados if r["esperado"] == "A"]
    p(f"  Oraciones agramaticales: {len(agram)}. spaCy las analizó todas (no rechaza nada); "
      f"las reglas sobre sus rasgos marcaron inconsistencia en {sum(1 for r in agram if r['spacy_inconsistencias'])}.")
    for et, nombre in (("G", "gramaticales"), ("A", "agramaticales")):
        total = errores = 0
        for r in resultados:
            if r["esperado"] != et:
                continue
            for t in r["spacy_tokens"]:
                w = t["texto"].lower()
                if w in LEXICO and LEXICO[w][0][0] in ("V", "COP"):
                    total += 1
                    errores += t["pos"] not in ("VERB", "AUX")
        p(f"  Verbos mal etiquetados por spaCy en oraciones {nombre}: {errores} de {total}")
    fp = sum(1 for r in resultados if r["nltk_fcfg"] == "acepta" and r["esperado"] == "A")
    fn = sum(1 for r in resultados if r["nltk_fcfg"] == "rechaza" and r["esperado"] == "G")
    p(f"  NLTK con rasgos: aciertos={len(resultados) - fp - fn} de {len(resultados)}, FP={fp}, FN={fn}")

    if guardar:
        carpeta = os.path.join(RAIZ, "salidas")
        os.makedirs(carpeta, exist_ok=True)
        with open(os.path.join(carpeta, "resultados_nlp.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(salida))
        with open(os.path.join(carpeta, "resultados_nlp.json"), "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
    return "\n".join(salida), resultados


if __name__ == "__main__":
    texto, _ = ejecutar_todo()
    print(texto)

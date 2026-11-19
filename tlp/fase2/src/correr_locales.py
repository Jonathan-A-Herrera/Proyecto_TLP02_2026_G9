"""
correr_locales.py
Pasa el corpus completo por los tres enfoques que corren en la computadora
y guarda la salida bruta de cada uno en logs/:

  logs/parser_propio.json   parser LL(1) sobre la CFG v2 del español (concordancia en los no terminales)
  logs/spacy.json           spaCy es_core_news_sm + regla de aceptación descrita abajo
  logs/nltk.json            NLTK FeatureChartParser con una gramática de rasgos (FCFG)

Uso:  python src/correr_locales.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nltk                                                                 # noqa: E402
from nltk.grammar import FeatureGrammar, TYPE                                     # noqa: E402
from nltk.parse import FeatureChartParser                                   # noqa: E402

from comun import leer_corpus, guardar_log, normalizar, separar             # noqa: E402
from ll1 import ParserLL1, ErrorLL1                                         # noqa: E402
from gramaticas_espanol import (GRAMATICA_V2, INICIAL, LEXICO, etiquetar,   # noqa: E402
                                PalabraDesconocida)


# ---------------------------------------------------------------------------
# 1. Parser propio
# ---------------------------------------------------------------------------
def correr_parser_propio(corpus):
    parser = ParserLL1(GRAMATICA_V2, INICIAL)
    resultados = []
    for r in corpus:
        entrada = {"id": r["id"], "oracion": r["oracion"]}
        try:
            palabras, cats = etiquetar(r["oracion"], 2)
            arbol, decisiones = parser.analizar(cats, palabras)
            entrada.update(veredicto="ACEPTA",
                           categorias=[normalizar(c.split("_")[0]) for c in cats],
                           conflictos_resueltos=[f"M[{A}, {a}]" for A, a, _ in decisiones],
                           arbol=str(arbol.a_nltk()))
        except (ErrorLL1, PalabraDesconocida) as e:
            entrada.update(veredicto="RECHAZA", categorias=[], motivo=str(e))
        resultados.append(entrada)
    return guardar_log("parser_propio", {
        "descripcion": "Parser predictivo LL(1) con pila sobre la CFG v2 (44 no terminales, 95 producciones)",
        "no_terminales": len(GRAMATICA_V2),
        "producciones": sum(len(p) for p in GRAMATICA_V2.values()),
    }, resultados)


# ---------------------------------------------------------------------------
# 2. spaCy
# ---------------------------------------------------------------------------
UPOS_A_CATEGORIA = {"DET": "DET", "NOUN": "N", "PROPN": "NP", "ADJ": "ADJ", "VERB": "V", "AUX": "COP",
                    "ADV": "ADV", "ADP": "PREP", "SCONJ": "QUE", "PUNCT": "SEP", "CCONJ": "SEP"}


def rasgo(t, nombre):
    v = t.morph.get(nombre)
    return v[0] if v else None


def inconsistencias(doc):
    """Compara género y número entre las palabras que spaCy relacionó."""
    problemas = []

    def comparar(a, b, rasgos, motivo):
        for r in rasgos:
            x, y = rasgo(a, r), rasgo(b, r)
            if x and y and x != y:
                problemas.append(f"{motivo}: {r} '{a.text}'={x} vs '{b.text}'={y}")

    for t in doc:
        if t.dep_ in ("det", "amod"):
            comparar(t, t.head, ("Gender", "Number"), t.dep_)
        if t.dep_ == "nsubj":
            h = t.head
            if h.pos_ in ("VERB", "AUX"):
                comparar(t, h, ("Number",), "sujeto-verbo")
            cop = [c for c in h.children if c.dep_ == "cop"]
            if cop:                                      # oración copulativa: atributo y cópula
                comparar(t, h, ("Gender", "Number"), "sujeto-atributo")
                comparar(t, cop[0], ("Number",), "sujeto-copula")
    return problemas


def correr_spacy(corpus):
    import spacy
    nlp = spacy.load("es_core_news_sm")
    resultados = []
    for r in corpus:
        doc = nlp(r["oracion"])
        raiz = [t for t in doc if t.dep_ == "ROOT"][0]
        tiene_verbo = raiz.pos_ == "VERB" or any(c.dep_ == "cop" for c in raiz.children)
        probs = inconsistencias(doc)
        aceptada = tiene_verbo and not probs
        resultados.append({
            "id": r["id"], "oracion": r["oracion"],
            "veredicto": "ACEPTA" if aceptada else "RECHAZA",
            "categorias": [t.text == "que" and "QUE" or UPOS_A_CATEGORIA.get(t.pos_, t.pos_) for t in doc],
            "raiz": f"{raiz.text}/{raiz.pos_}", "raiz_verbal": tiene_verbo, "inconsistencias": probs,
            "tokens": [{"texto": t.text, "pos": t.pos_, "dep": t.dep_, "nucleo": t.head.text,
                        "morfologia": str(t.morph)} for t in doc],
        })
    return guardar_log("spacy", {
        "version_spacy": spacy.__version__, "modelo": "es_core_news_sm",
        "version_modelo": nlp.meta.get("version"),
        "regla_de_aceptacion": "ACEPTA si la raíz es un verbo (o un atributo con cópula) y no hay "
                               "inconsistencias de género/número entre det-sustantivo, adjetivo-sustantivo, "
                               "sujeto-verbo y sujeto-atributo según los rasgos morfológicos de spaCy",
    }, resultados)


# ---------------------------------------------------------------------------
# 3. NLTK con gramática de rasgos
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
    lineas = [REGLAS_FCFG.strip()]
    for palabra, entradas in LEXICO.items():
        cat, g, n = entradas[0]
        if cat in ("SEP", "RESP"):
            continue
        rasgos = [f"GEN={g}"] if g in ("m", "f") else []     # género común: sin GEN, unifica con ambos
        if n in ("s", "p"):
            rasgos.append(f"NUM={n}")
        lineas.append(f"{cat}[{', '.join(rasgos)}] -> '{palabra}'" if rasgos else f"{cat} -> '{palabra}'")
    return FeatureGrammar.fromstring("\n".join(lineas))


def correr_nltk(corpus):
    parser = FeatureChartParser(construir_fcfg())
    resultados = []
    for r in corpus:
        entrada = {"id": r["id"], "oracion": r["oracion"]}
        try:
            arboles = list(parser.parse(separar(r["oracion"])))
        except ValueError as e:                              # palabra sin regla léxica en la FCFG
            arboles, entrada["motivo"] = [], str(e)
        if arboles:
            pre = [st.label()[TYPE] for st in arboles[0].subtrees()          # preterminales: su único hijo es la palabra
                   if len(st) == 1 and isinstance(st[0], str)]
            entrada.update(veredicto="ACEPTA", arboles=len(arboles),
                           categorias=[normalizar(c) for c in pre], arbol=str(arboles[0]))
        else:
            entrada.update(veredicto="RECHAZA", arboles=0, categorias=[])
        resultados.append(entrada)
    return guardar_log("nltk", {
        "version_nltk": nltk.__version__,
        "descripcion": "FeatureChartParser con gramática de rasgos (GEN, NUM) unificados",
        "reglas_sintacticas": sum(1 for l in REGLAS_FCFG.strip().splitlines() if "->" in l),
    }, resultados)


if __name__ == "__main__":
    corpus = leer_corpus()
    for f in (correr_parser_propio, correr_spacy, correr_nltk):
        print("Log guardado:", f(corpus))

"""
gramaticas_espanol.py
Intentos de extender la CFG del parser para aceptar oraciones del español.

  v1: gramática "ingenua" sin concordancia (categorías sin rasgos).
  v2: concordancia de género y número codificada en los no terminales
      (SN_f_p, SV_m_s, ...), incluida la concordancia a distancia y el hueco
      de las relativas de objeto.
  v3: construcción con "respectivamente" (dependencias cruzadas).

Cada gramática usa como terminales las CATEGORÍAS que entrega el léxico
(DET, N, ADJ, V...), no las palabras. El léxico hace de analizador léxico.
"""
from itertools import product

# ---------------------------------------------------------------------------
# LÉXICO: palabra -> lista de (categoría, género, número)
# género: m, f o c (común: sirve para ambos)   número: s, p   '-' = no aplica
# ---------------------------------------------------------------------------
def _flexiones(raiz_m, raiz_f, plural_m, plural_f, cat):
    return {raiz_m: [(cat, "m", "s")], raiz_f: [(cat, "f", "s")],
            plural_m: [(cat, "m", "p")], plural_f: [(cat, "f", "p")]}


LEXICO = {}
LEXICO.update({"el": [("DET", "m", "s")], "la": [("DET", "f", "s")],
               "los": [("DET", "m", "p")], "las": [("DET", "f", "p")],
               "un": [("DET", "m", "s")], "una": [("DET", "f", "s")]})
LEXICO.update(_flexiones("niño", "niña", "niños", "niñas", "N"))
LEXICO.update(_flexiones("perro", "perra", "perros", "perras", "N"))
LEXICO.update(_flexiones("gato", "gata", "gatos", "gatas", "N"))
LEXICO.update({"profesor": [("N", "m", "s")], "profesores": [("N", "m", "p")],
               "profesora": [("N", "f", "s")], "profesoras": [("N", "f", "p")],
               "libro": [("N", "m", "s")], "libros": [("N", "m", "p")],
               "parque": [("N", "m", "s")], "telescopio": [("N", "m", "s")],
               "casa": [("N", "f", "s")], "mesa": [("N", "f", "s")],
               "estudiante": [("N", "c", "s")], "estudiantes": [("N", "c", "p")]})
LEXICO.update(_flexiones("negro", "negra", "negros", "negras", "ADJ"))
LEXICO.update(_flexiones("pequeño", "pequeña", "pequeños", "pequeñas", "ADJ"))
LEXICO.update(_flexiones("cansado", "cansada", "cansados", "cansadas", "ADJ"))
LEXICO.update(_flexiones("alto", "alta", "altos", "altas", "ADJ"))
LEXICO.update({"feliz": [("ADJ", "c", "s")], "felices": [("ADJ", "c", "p")],
               "grande": [("ADJ", "c", "s")], "grandes": [("ADJ", "c", "p")]})
# Verbos: número del sujeto; dos tiempos (presente y pretérito)
for sing, plur in [("come", "comen"), ("comió", "comieron"), ("ve", "ven"), ("vio", "vieron"),
                   ("ladra", "ladran"), ("ladró", "ladraron"), ("duerme", "duermen"),
                   ("lee", "leen"), ("leyó", "leyeron"), ("dice", "dicen"), ("dijo", "dijeron"),
                   ("regaña", "regañan"), ("regañó", "regañaron"), ("llega", "llegan"),
                   ("llegó", "llegaron")]:
    LEXICO[sing] = [("V", "-", "s")]
    LEXICO[plur] = [("V", "-", "p")]
LEXICO.update({"es": [("COP", "-", "s")], "son": [("COP", "-", "p")],
               "está": [("COP", "-", "s")], "están": [("COP", "-", "p")],
               "estaba": [("COP", "-", "s")], "estaban": [("COP", "-", "p")]})
for adv in ["rápidamente", "ayer", "mucho", "bien", "hoy", "siempre"]:
    LEXICO[adv] = [("ADV", "-", "-")]
for prep in ["con", "en", "de", "sobre"]:
    LEXICO[prep] = [("PREP", "-", "-")]
LEXICO.update({"que": [("QUE", "-", "-")],
               "ana": [("NP", "f", "s")], "marta": [("NP", "f", "s")],
               "luis": [("NP", "m", "s")], "pedro": [("NP", "m", "s")],
               ",": [("SEP", "-", "-")], "y": [("SEP", "-", "-")],
               "respectivamente": [("RESP", "-", "-")]})


class PalabraDesconocida(Exception):
    pass


def separar(oracion):
    return oracion.lower().replace(",", " , ").replace(".", " ").split()


def etiquetar(oracion, version):
    """Analizador léxico del español. Devuelve (palabras, categorías).
    v1 -> categoría sola (DET); v2/v3 -> categoría con rasgos (DET_f_p)."""
    palabras = separar(oracion)
    categorias = []
    for p in palabras:
        if p not in LEXICO:
            raise PalabraDesconocida(f"La palabra '{p}' no está en el vocabulario")
        cat, g, n = LEXICO[p][0]
        if version == 1 or cat in ("ADV", "PREP", "QUE", "SEP", "RESP"):
            categorias.append(cat)
        elif cat in ("V", "COP"):
            categorias.append(f"{cat}_{n}")
        else:
            categorias.append(f"{cat}_{g}_{n}")
    return palabras, categorias


# ---------------------------------------------------------------------------
# v1: SIN concordancia
# ---------------------------------------------------------------------------
GRAMATICA_V1 = {
    "O":         [["SN", "SV"]],
    "SN":        [["DET", "N", "MODS_N"], ["NP"]],
    "MODS_N":    [["ADJ", "MODS_N"], ["SP", "MODS_N"], ["REL", "MODS_N"], []],
    "REL":       [["QUE", "REL_RESTO"]],
    "REL_RESTO": [["SV"], ["O"]],              # relativa de sujeto | relativa de objeto
    "SP":        [["PREP", "SN"]],
    "SV":        [["ADVS", "NUCLEO_V"]],
    "NUCLEO_V":  [["V", "COMP"], ["COP", "ADJ", "MODS_V"]],
    "ADVS":      [["ADV", "ADVS"], []],
    "COMP":      [["SN", "MODS_V"], ["MODS_V"]],
    "MODS_V":    [["ADV", "MODS_V"], ["SP", "MODS_V"], ["SUB"], []],
    "SUB":       [["QUE", "O"]],               # subordinada sustantiva: dice que ...
}
INICIAL = "O"


# ---------------------------------------------------------------------------
# v2: CON concordancia. Se generan los no terminales para cada combinación de rasgos.
# ---------------------------------------------------------------------------
GENEROS = ["m", "f"]
NUMEROS = ["s", "p"]


def generar_v2(generos=GENEROS, numeros=NUMEROS):
    """Genera la gramática con rasgos. Con otros valores de rasgos sirve para medir
    cuánto crece la gramática (p. ej. si se agrega la persona gramatical)."""
    g2 = {}
    combinaciones = list(product(generos, numeros))

    # O -> SN_g_n SV_g_n  (sujeto y verbo concuerdan; g también por el atributo: "están cansadas")
    g2["O"] = [[f"SN_{g}_{n}", f"SV_{g}_{n}"] for g, n in combinaciones]

    for g, n in combinaciones:
        # El nombre propio solo es singular
        sn = [[f"DET_{g}_{n}", f"NUC_{g}_{n}"]]
        if n.endswith("s"):
            sn.append([f"NP_{g}_s"])
        g2[f"SN_{g}_{n}"] = sn
        # Núcleo: sustantivo del mismo género o de género común (estudiante)
        g2[f"NUC_{g}_{n}"] = [[f"N_{g}_{n}", f"MODS_N_{g}_{n}"], [f"N_c_{n}", f"MODS_N_{g}_{n}"]]
        # Modificadores del nombre: el adjetivo concuerda con el sustantivo
        g2[f"MODS_N_{g}_{n}"] = [[f"ADJ_{g}_{n}", f"MODS_N_{g}_{n}"], [f"ADJ_c_{n}", f"MODS_N_{g}_{n}"],
                                 ["SP", f"MODS_N_{g}_{n}"], [f"REL_{g}_{n}", f"MODS_N_{g}_{n}"], []]
        # Relativa: de sujeto (el verbo concuerda con el antecedente) o de objeto (con hueco)
        g2[f"REL_{g}_{n}"] = [["QUE", f"REL_RESTO_{g}_{n}"]]
        g2[f"REL_RESTO_{g}_{n}"] = [[f"SV_{g}_{n}"], ["O_HUECO"]]
        # SV: el verbo concuerda en número; el atributo (cansadas) en género y número
        g2[f"SV_{g}_{n}"] = [["ADVS", f"NUCLEO_V_{g}_{n}"]]
        g2[f"NUCLEO_V_{g}_{n}"] = [[f"V_{n}", "COMP"],
                                   [f"COP_{n}", f"ATRIB_{g}_{n}", "MODS_V"]]
        g2[f"ATRIB_{g}_{n}"] = [[f"ADJ_{g}_{n}"], [f"ADJ_c_{n}"]]
        # Oración con hueco de objeto: "que el profesor regañó ___"
        g2[f"SV_HUECO_{g}_{n}"] = [["ADVS", f"V_{n}", "MODS_V"]]

    g2["O_HUECO"] = [[f"SN_{g}_{n}", f"SV_HUECO_{g}_{n}"] for g, n in combinaciones]
    # SP factorizada por la izquierda. Sin factorizar (SP -> PREP SN_m_s | PREP SN_f_s ...)
    # las 4 alternativas empiezan con PREP y la tabla LL(1) tiene un conflicto en M[SP, PREP].
    g2["SP"] = [["PREP", "SN_X"]]
    g2["SN_X"] = [[f"SN_{g}_{n}"] for g, n in combinaciones]
    g2["ADVS"] = [["ADV", "ADVS"], []]
    g2["COMP"] = [[f"SN_{g}_{n}", "MODS_V"] for g, n in combinaciones] + [["MODS_V"]]
    g2["MODS_V"] = [["ADV", "MODS_V"], ["SP", "MODS_V"], ["SUB"], []]
    g2["SUB"] = [["QUE", "O"]]
    return g2


GRAMATICA_V2 = generar_v2()


# ---------------------------------------------------------------------------
# v3: "respectivamente". Ana, Luis y Pedro son alta, alto y alto respectivamente.
# El i-ésimo nombre concuerda con el i-ésimo adjetivo: dependencias CRUZADAS.
# ---------------------------------------------------------------------------
# v3a: lista de nombres y lista de adjetivos independientes (no controla el emparejamiento)
GRAMATICA_V3A = {
    "O":     [["LNP", "COP_p", "LADJ", "RESP"]],
    "LNP":   [["NPX", "SEP", "LNP"], ["NPX", "SEP", "NPX"]],
    "NPX":   [["NP_f_s"], ["NP_m_s"]],
    "LADJ":  [["ADJX", "SEP", "LADJ"], ["ADJX", "SEP", "ADJX"]],
    "ADJX":  [["ADJ_f_s"], ["ADJ_m_s"]],
}
# v3b: lo mejor que puede hacer una CFG para "emparejar": anidar (espejo, como paréntesis).
# Empareja el primer nombre con el ÚLTIMO adjetivo, que es justo lo contrario del español.
GRAMATICA_V3B = {
    "O":  [["E", "RESP"]],
    "E":  [["NP_f_s", "SEP", "E", "SEP", "ADJ_f_s"], ["NP_m_s", "SEP", "E", "SEP", "ADJ_m_s"],
           ["NP_f_s", "COP_p", "ADJ_f_s"], ["NP_m_s", "COP_p", "ADJ_m_s"]],
}

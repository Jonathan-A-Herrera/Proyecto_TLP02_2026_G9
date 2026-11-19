"""
evaluar.py
Lee el corpus y los logs de cada enfoque y calcula todas las métricas del informe.
Es determinista: con los mismos archivos de entrada produce exactamente las mismas tablas.

Definiciones (la clase positiva es ACEPTA; la etiqueta de referencia es 'esperado' del corpus):
  VP  aceptó una oración correcta         FP  aceptó una oración incorrecta
  VN  rechazó una oración incorrecta      FN  rechazó una oración correcta
  Precisión              VP / (VP + FP)
  Cobertura (recall)     VP / (VP + FN)
  Tasa de rechazo correcto  VN / (VN + FP)
  Error de etiquetado    oración bien aceptada (VP) cuya secuencia de categorías difiere de la esperada
  Fidelidad a L(G)       % de oraciones donde el veredicto coincide con la pertenencia a la gramática
                         (columna en_gramatica): mide si el enfoque sigue las reglas formales.

Uso:  python src/evaluar.py
Salida: resultados/*.csv, resultados/tablas.md y resultados/*.png
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comun import leer_corpus, LOGS, RESULTADOS          # noqa: E402

ENFOQUES = [("parser_propio", "Parser propio"), ("spacy", "spaCy"), ("nltk", "NLTK"),
            ("llm_zero_shot", "LLM zero-shot"), ("llm_few_shot", "LLM few-shot")]
COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]   # orden fijo por enfoque


def cargar_logs():
    logs = {}
    for clave, nombre in ENFOQUES:
        ruta = os.path.join(LOGS, f"{clave}.json")
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            logs[clave] = {"nombre": nombre, "meta": {k: v for k, v in d.items() if k != "resultados"},
                           "res": {str(r["id"]): r for r in d["resultados"]}}
    return logs


def div(a, b):
    return round(a / b, 3) if b else None


def clasificar(esperado, veredicto):
    acepto = veredicto == "ACEPTA"
    if esperado == "ACEPTA":
        return "VP" if acepto else "FN"
    return "FP" if acepto else "VN"


def metricas(corpus, res):
    c = {"VP": 0, "VN": 0, "FP": 0, "FN": 0}
    etiquetado, tokens_bien, tokens_total, fiel, invalidas = 0, 0, 0, 0, 0
    for r in corpus:
        salida = res[r["id"]]
        v = salida["veredicto"]
        if v not in ("ACEPTA", "RECHAZA"):
            invalidas += 1
        tipo = clasificar(r["esperado"], v)
        c[tipo] += 1
        fiel += (v == "ACEPTA") == (r["en_gramatica"] == "SI")
        if tipo == "VP":
            esp, obt = r["categorias_esperadas"], salida.get("categorias", [])
            etiquetado += esp != obt
            tokens_total += len(esp)
            tokens_bien += sum(a == b for a, b in zip(esp, obt))
    n = len(corpus)
    return {**c, "precision": div(c["VP"], c["VP"] + c["FP"]), "cobertura": div(c["VP"], c["VP"] + c["FN"]),
            "rechazo_correcto": div(c["VN"], c["VN"] + c["FP"]), "exactitud": div(c["VP"] + c["VN"], n),
            "errores_etiquetado": etiquetado, "acierto_categorias_tokens": div(tokens_bien, tokens_total),
            "fidelidad_LG": div(fiel, n), "respuestas_invalidas": invalidas}


def escribir_csv(nombre, filas):
    ruta = os.path.join(RESULTADOS, nombre)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def pct(x):
    return "-" if x is None else f"{x * 100:.1f} %"


def tabla_md(encabezado, filas):
    out = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    out += ["| " + " | ".join(str(x) for x in f) + " |" for f in filas]
    return "\n".join(out)


def graficas(generales, por_nivel):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#8a8984", "axes.labelcolor": "#52514e",
                         "xtick.color": "#52514e", "ytick.color": "#52514e", "figure.facecolor": "white"})
    claves = [g["clave"] for g in generales]

    # 1) Precisión, cobertura y rechazo correcto por enfoque
    medidas = [("precision", "Precisión"), ("cobertura", "Cobertura"), ("rechazo_correcto", "Rechazo correcto")]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ancho = 0.8 / len(generales)
    for i, g in enumerate(generales):
        xs = [m + (i - (len(generales) - 1) / 2) * ancho for m in range(len(medidas))]
        ys = [(g[k] or 0) * 100 for k, _ in medidas]
        barras = ax.bar(xs, ys, ancho - 0.02, color=COLORES[ENFOQUES.index((g["clave"], g["enfoque"]))],
                        label=g["enfoque"], edgecolor="white", linewidth=1)
        for b, y in zip(barras, ys):
            ax.text(b.get_x() + b.get_width() / 2, y + 1.5, f"{y:.0f}", ha="center", va="bottom",
                    fontsize=7, color="#0b0b0b")
    ax.set_xticks(range(len(medidas)), [n for _, n in medidas])
    ax.set_ylim(0, 112)
    ax.set_ylabel("%")
    ax.yaxis.grid(True, color="#e5e4df", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=len(generales), loc="upper center", bbox_to_anchor=(0.5, 1.13), fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTADOS, "grafica_metricas.png"), dpi=200)
    plt.close(fig)

    # 2) Exactitud por nivel de complejidad
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    niveles = ["1", "2", "3"]
    for i, clave in enumerate(claves):
        fila = [p for p in por_nivel if p["clave"] == clave]
        xs = [n + (i - (len(claves) - 1) / 2) * ancho for n in range(3)]
        ys = [next(p["exactitud"] for p in fila if p["nivel"] == n) * 100 for n in niveles]
        barras = ax.bar(xs, ys, ancho - 0.02, color=COLORES[[c for c, _ in ENFOQUES].index(clave)],
                        label=fila[0]["enfoque"], edgecolor="white", linewidth=1)
        for b, y in zip(barras, ys):
            ax.text(b.get_x() + b.get_width() / 2, y + 1.5, f"{y:.0f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(3), ["Nivel 1 (simples)", "Nivel 2 (intermedias)", "Nivel 3 (complejas)"])
    ax.set_ylim(0, 112)
    ax.set_ylabel("Exactitud (%)")
    ax.yaxis.grid(True, color="#e5e4df", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=len(claves), loc="upper center", bbox_to_anchor=(0.5, 1.17), fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTADOS, "grafica_niveles.png"), dpi=200)
    plt.close(fig)


def main():
    os.makedirs(RESULTADOS, exist_ok=True)
    corpus = leer_corpus()
    logs = cargar_logs()
    faltan = [n for c, n in ENFOQUES if c not in logs]

    generales, por_nivel, detalle = [], [], []
    for clave, nombre in ENFOQUES:
        if clave not in logs:
            continue
        res = logs[clave]["res"]
        generales.append({"clave": clave, "enfoque": nombre, **metricas(corpus, res)})
        for n in "123":
            sub = [r for r in corpus if r["nivel"] == n]
            m = metricas(sub, res)
            por_nivel.append({"clave": clave, "enfoque": nombre, "nivel": n, "oraciones": len(sub),
                              "VP": m["VP"], "VN": m["VN"], "FP": m["FP"], "FN": m["FN"],
                              "exactitud": m["exactitud"]})

    for r in corpus:
        fila = {"id": r["id"], "nivel": r["nivel"], "oracion": r["oracion"], "esperado": r["esperado"],
                "en_gramatica": r["en_gramatica"], "fenomeno": r["fenomeno"]}
        for clave, nombre in ENFOQUES:
            if clave in logs:
                s = logs[clave]["res"][r["id"]]
                tipo = clasificar(r["esperado"], s["veredicto"])
                if tipo == "VP" and s.get("categorias", []) != r["categorias_esperadas"]:
                    tipo = "VP*"            # aceptada bien pero con error de etiquetado
                fila[nombre] = tipo
        detalle.append(fila)

    escribir_csv("metricas.csv", generales)
    escribir_csv("metricas_por_nivel.csv", por_nivel)
    escribir_csv("detalle_por_oracion.csv", detalle)

    # Comportamiento del LLM frente a las reglas
    llm = []
    for clave in ("llm_zero_shot", "llm_few_shot"):
        if clave not in logs:
            continue
        res = logs[clave]["res"]
        fuera = [r for r in corpus if r["esperado"] == "ACEPTA" and r["en_gramatica"] == "NO"]
        dentro = [r for r in corpus if r["en_gramatica"] == "SI"]
        agram = [r for r in corpus if r["esperado"] == "RECHAZA"]
        llm.append({
            "variante": logs[clave]["nombre"],
            "correctas_fuera_de_G": len(fuera),
            "aceptadas_por_conocimiento_general": sum(res[r["id"]]["veredicto"] == "ACEPTA" for r in fuera),
            "derivables_en_G": len(dentro),
            "derivables_rechazadas": sum(res[r["id"]]["veredicto"] != "ACEPTA" for r in dentro),
            "incorrectas": len(agram),
            "incorrectas_aceptadas": sum(res[r["id"]]["veredicto"] == "ACEPTA" for r in agram),
            "fidelidad_LG": metricas(corpus, res)["fidelidad_LG"],
        })
    if llm:
        escribir_csv("llm_frente_a_reglas.csv", llm)
    if "llm_zero_shot" in logs and "llm_few_shot" in logs:
        z, f = logs["llm_zero_shot"]["res"], logs["llm_few_shot"]["res"]
        cambios = [{"id": r["id"], "oracion": r["oracion"], "esperado": r["esperado"],
                    "en_gramatica": r["en_gramatica"], "zero_shot": z[r["id"]]["veredicto"],
                    "few_shot": f[r["id"]]["veredicto"]}
                   for r in corpus if z[r["id"]]["veredicto"] != f[r["id"]]["veredicto"]]
        if cambios:
            escribir_csv("llm_cambios_zero_vs_few.csv", cambios)

    # Tablas en texto
    md = ["# Resultados", ""]
    if faltan:
        md += [f"Enfoques sin log todavía: {', '.join(faltan)}", ""]
    md += ["## Métricas generales (48 oraciones)", "",
           tabla_md(["Enfoque", "VP", "VN", "FP", "FN", "Precisión", "Cobertura", "Rechazo correcto",
                     "Exactitud", "Errores de etiquetado", "Fidelidad a L(G)"],
                    [[g["enfoque"], g["VP"], g["VN"], g["FP"], g["FN"], pct(g["precision"]), pct(g["cobertura"]),
                      pct(g["rechazo_correcto"]), pct(g["exactitud"]), g["errores_etiquetado"],
                      pct(g["fidelidad_LG"])] for g in generales]), "",
           "## Exactitud por nivel", "",
           tabla_md(["Enfoque", "Nivel 1", "Nivel 2", "Nivel 3"],
                    [[g["enfoque"]] + [pct(next(p["exactitud"] for p in por_nivel
                                                 if p["clave"] == g["clave"] and p["nivel"] == n))
                                       for n in "123"] for g in generales]), ""]
    if llm:
        md += ["## LLM frente a las reglas formales", "",
               tabla_md(["Variante", "Correctas fuera de G aceptadas", "Derivables en G rechazadas",
                         "Incorrectas aceptadas", "Fidelidad a L(G)"],
                        [[x["variante"], f"{x['aceptadas_por_conocimiento_general']} de {x['correctas_fuera_de_G']}",
                          f"{x['derivables_rechazadas']} de {x['derivables_en_G']}",
                          f"{x['incorrectas_aceptadas']} de {x['incorrectas']}", pct(x["fidelidad_LG"])]
                         for x in llm]), ""]
    md += ["## Detalle por oración (VP* = aceptada bien con error de etiquetado)", "",
           tabla_md(list(detalle[0].keys()), [list(d.values()) for d in detalle])]
    with open(os.path.join(RESULTADOS, "tablas.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    graficas(generales, por_nivel)
    print("\n".join(md[:md.index("## Detalle por oración (VP* = aceptada bien con error de etiquetado)")]))
    print(f"Archivos escritos en {RESULTADOS}")


if __name__ == "__main__":
    main()

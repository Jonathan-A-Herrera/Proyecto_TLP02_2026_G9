"""
comun.py
Funciones compartidas por todos los scripts de la Fase 2:
leer el corpus, guardar logs y normalizar las categorías gramaticales.
"""
import csv
import json
import os
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_CSV = os.path.join(RAIZ, "corpus", "corpus.csv")
LOGS = os.path.join(RAIZ, "logs")
RESULTADOS = os.path.join(RAIZ, "resultados")
PROMPTS = os.path.join(RAIZ, "prompts")

# Conjunto de categorías con el que se compara la estructura esperada.
# 'respectivamente' se compara como ADV porque así lo etiquetan todas las herramientas.
CATEGORIAS = ["DET", "N", "NP", "ADJ", "V", "COP", "ADV", "PREP", "QUE", "SEP"]
NORMALIZAR = {"RESP": "ADV"}


def normalizar(cat):
    cat = (cat or "").upper().strip()
    return NORMALIZAR.get(cat, cat)


def ahora():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def leer_corpus():
    with open(CORPUS_CSV, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for r in filas:
        r["categorias_esperadas"] = r["categorias_esperadas"].split()
    return filas


def guardar_log(nombre, metadatos, resultados):
    """Guarda la salida bruta de un enfoque: metadatos de la corrida + una entrada por oración."""
    os.makedirs(LOGS, exist_ok=True)
    ruta = os.path.join(LOGS, f"{nombre}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"enfoque": nombre, "fecha": ahora(), **metadatos, "resultados": resultados},
                  f, ensure_ascii=False, indent=2)
    return ruta


def separar(oracion):
    return oracion.lower().replace(",", " , ").replace(".", " ").split()

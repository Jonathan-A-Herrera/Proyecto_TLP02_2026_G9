"""
correr_llm.py
Pasa el corpus por un LLM vía API, entregándole en el prompt las reglas de producción
de nuestra CFG (v2) y el léxico. Corre dos variantes:

  zero_shot   solo reglas + léxico
  few_shot    reglas + léxico + 4 ejemplos resueltos (ninguno está en el corpus)

Cada llamada queda registrada en logs/llm_<variante>_llamadas.jsonl con su timestamp,
el prompt exacto enviado y la respuesta completa del modelo. Al terminar se escribe
logs/llm_<variante>.json con el mismo formato que los demás enfoques.

Uso (la clave NUNCA se escribe en el código; se pasa como variable de entorno):
    export GEMINI_API_KEY="tu_clave"                 # Mac / Linux
    python src/correr_llm.py --proveedor gemini

    $env:GEMINI_API_KEY="tu_clave"                   # Windows PowerShell
    python src/correr_llm.py --proveedor gemini

Opciones:
    --proveedor gemini | anthropic | openai
    --modelo NOMBRE          (si no se indica, se usa el de MODELOS_POR_DEFECTO)
    --variante zero_shot | few_shot | ambas   (por defecto ambas)
    --pausa SEGUNDOS         espera entre llamadas, para no pasar el límite gratuito (por defecto 7)
    --listar-modelos         muestra los modelos disponibles con tu clave (solo Gemini)

Si la corrida se corta, al volver a ejecutarla continúa desde la última oración registrada.
"""
import argparse
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comun import leer_corpus, guardar_log, normalizar, separar, ahora, LOGS, PROMPTS   # noqa: E402
from gramaticas_espanol import GRAMATICA_V2, INICIAL, LEXICO                       # noqa: E402

MODELOS_POR_DEFECTO = {"gemini": "gemini-2.5-flash", "anthropic": "claude-haiku-5-5", "openai": "gpt-4o-mini"}
VARIABLE_CLAVE = {"gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
TEMPERATURA = 0
MAX_TOKENS = 2048

# ---------------------------------------------------------------------------
# Construcción del prompt
# ---------------------------------------------------------------------------
def texto_gramatica():
    lineas = []
    for A in [INICIAL] + [k for k in GRAMATICA_V2 if k != INICIAL]:
        alternativas = [" ".join(p) if p else "ε" for p in GRAMATICA_V2[A]]
        lineas.append(f"{A} -> " + " | ".join(alternativas))
    return "\n".join(lineas)


def texto_lexico():
    """Cada palabra con su terminal: categoría_género_número (c = género común)."""
    por_terminal = {}
    for palabra, entradas in LEXICO.items():
        cat, g, n = entradas[0]
        if cat in ("V", "COP"):
            terminal = f"{cat}_{n}"
        elif cat in ("ADV", "PREP", "QUE", "SEP", "RESP"):
            terminal = cat
        else:
            terminal = f"{cat}_{g}_{n}"
        por_terminal.setdefault(terminal, []).append(palabra)
    return "\n".join(f"{t}: {', '.join(ps)}" for t, ps in sorted(por_terminal.items()))


INSTRUCCIONES = """Eres un analizador sintáctico formal. Tu única tarea es decidir si una secuencia de palabras \
puede derivarse desde el símbolo inicial O usando EXCLUSIVAMENTE la gramática libre de contexto y el léxico \
que siguen. No uses tu conocimiento general del español: una oración correcta en español que no se pueda \
derivar con estas reglas debe RECHAZARSE, y una oración que sí se derive debe ACEPTARSE.

Notación: los símbolos en mayúsculas con sufijos (_m/_f/_c = género masculino/femenino/común, _s/_p = número) \
son no terminales o terminales. Los terminales son las categorías del léxico. ε es la cadena vacía.

GRAMÁTICA (símbolo inicial O):
{gramatica}

LÉXICO (terminal: palabras):
{lexico}

Responde ÚNICAMENTE con un objeto JSON, sin texto adicional, con esta forma:
{{"veredicto": "ACEPTA" o "RECHAZA",
  "categorias": [una categoría por palabra de entrada, sin sufijos de rasgos, tomada de: DET, N, NP, ADJ, V, COP, ADV, PREP, QUE, SEP, RESP],
  "justificacion": "una frase: la derivación usada o la regla que impide derivar la oración"}}"""

EJEMPLOS = [
    ("El gato negro duerme",
     {"veredicto": "ACEPTA", "categorias": ["DET", "N", "ADJ", "V"],
      "justificacion": "O -> SN_m_s SV_m_s; SN_m_s -> DET_m_s NUC_m_s; NUC_m_s -> N_m_s MODS_N_m_s; "
                       "MODS_N_m_s -> ADJ_m_s MODS_N_m_s; SV_m_s -> ADVS NUCLEO_V_m_s; NUCLEO_V_m_s -> V_s COMP; COMP -> MODS_V"}),
    ("Las perras ladraron ayer",
     {"veredicto": "ACEPTA", "categorias": ["DET", "N", "V", "ADV"],
      "justificacion": "O -> SN_f_p SV_f_p; NUCLEO_V_f_p -> V_p COMP; COMP -> MODS_V; MODS_V -> ADV MODS_V"}),
    ("La gato duerme",
     {"veredicto": "RECHAZA", "categorias": ["DET", "N", "V"],
      "justificacion": "Después de DET_f_s la regla NUC_f_s exige N_f_s o N_c_s y 'gato' es N_m_s"}),
    ("Duerme el gato",
     {"veredicto": "RECHAZA", "categorias": ["V", "DET", "N"],
      "justificacion": "Toda derivación de O empieza con SN (DET o NP); ninguna regla permite iniciar con V, "
                       "aunque la oración sea correcta en español"}),
]


def prompt_sistema(variante):
    texto = INSTRUCCIONES.format(gramatica=texto_gramatica(), lexico=texto_lexico())
    if variante == "few_shot":
        texto += "\n\nEJEMPLOS RESUELTOS:"
        for oracion, salida in EJEMPLOS:
            texto += (f"\n\nEntrada: {oracion}\nPalabras: {json.dumps(separar(oracion), ensure_ascii=False)}"
                      f"\nSalida: {json.dumps(salida, ensure_ascii=False)}")
    return texto


def prompt_usuario(oracion):
    return (f"Entrada: {oracion}\nPalabras: {json.dumps(separar(oracion), ensure_ascii=False)}\n"
            "Salida:")


# ---------------------------------------------------------------------------
# Llamadas a cada API (solo biblioteca estándar: no hay que instalar nada)
# ---------------------------------------------------------------------------
def contexto_ssl():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def post(url, cabeceras, cuerpo):
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode(), method="POST",
                                 headers={"content-type": "application/json", **cabeceras})
    with urllib.request.urlopen(req, timeout=120, context=contexto_ssl()) as r:
        return json.loads(r.read().decode())


def llamar(proveedor, modelo, clave, sistema, usuario):
    """Devuelve (texto_respuesta, respuesta_json_completa)."""
    if proveedor == "gemini":
        datos = post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                     {"x-goog-api-key": clave},
                     {"systemInstruction": {"parts": [{"text": sistema}]},
                      "contents": [{"role": "user", "parts": [{"text": usuario}]}],
                      "generationConfig": {"temperature": TEMPERATURA, "maxOutputTokens": MAX_TOKENS * 4,
                                           "responseMimeType": "application/json"}})
        partes = datos["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in partes if not p.get("thought")), datos
    if proveedor == "anthropic":
        datos = post("https://api.anthropic.com/v1/messages",
                     {"x-api-key": clave, "anthropic-version": "2023-06-01"},
                     {"model": modelo, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURA,
                      "system": sistema, "messages": [{"role": "user", "content": usuario}]})
        return "".join(b.get("text", "") for b in datos["content"]), datos
    datos = post("https://api.openai.com/v1/chat/completions", {"authorization": f"Bearer {clave}"},
                 {"model": modelo, "temperature": TEMPERATURA, "response_format": {"type": "json_object"},
                  "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]})
    return datos["choices"][0]["message"]["content"], datos


def interpretar(texto):
    """Extrae el JSON de la respuesta. Si el modelo no respetó el formato, se registra como inválida."""
    m = re.search(r"\{.*\}", texto, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    v = str(obj.get("veredicto", "")).upper()
    if v not in ("ACEPTA", "RECHAZA"):
        return None
    return {"veredicto": v, "categorias": [normalizar(c) for c in obj.get("categorias", [])],
            "justificacion": obj.get("justificacion", "")}


# ---------------------------------------------------------------------------
def correr_variante(proveedor, modelo, clave, variante, pausa):
    corpus = leer_corpus()
    sistema = prompt_sistema(variante)
    huella = hashlib.sha256(sistema.encode()).hexdigest()[:16]
    os.makedirs(PROMPTS, exist_ok=True)
    with open(os.path.join(PROMPTS, f"{variante}.txt"), "w", encoding="utf-8") as f:
        f.write(sistema + "\n\n----- mensaje de usuario (plantilla) -----\n" + prompt_usuario("<oración>"))

    ruta_jsonl = os.path.join(LOGS, f"llm_{variante}_llamadas.jsonl")
    hechas = {}
    if os.path.exists(ruta_jsonl):
        with open(ruta_jsonl, encoding="utf-8") as f:
            for linea in f:
                reg = json.loads(linea)
                if reg.get("error") is None and reg["proveedor"] == proveedor and reg["modelo"] == modelo:
                    hechas[reg["id"]] = reg

    os.makedirs(LOGS, exist_ok=True)
    with open(ruta_jsonl, "a", encoding="utf-8") as log:
        for i, r in enumerate(corpus, 1):
            if r["id"] in hechas:
                continue
            usuario = prompt_usuario(r["oracion"])
            for intento in range(1, 6):
                enviado = ahora()
                reg = {"id": r["id"], "oracion": r["oracion"], "variante": variante, "proveedor": proveedor,
                       "modelo": modelo, "temperatura": TEMPERATURA, "intento": intento,
                       "timestamp_envio": enviado, "huella_prompt_sistema": huella,
                       "prompt_sistema": sistema, "prompt_usuario": usuario}
                try:
                    texto, crudo = llamar(proveedor, modelo, clave, sistema, usuario)
                    reg.update(timestamp_respuesta=ahora(), respuesta_texto=texto, respuesta_api=crudo,
                               interpretada=interpretar(texto), error=None)
                except urllib.error.HTTPError as e:
                    cuerpo = e.read().decode(errors="replace")
                    reg.update(timestamp_respuesta=ahora(), error=f"HTTP {e.code}: {cuerpo[:500]}")
                except Exception as e:                                  # red, tiempo de espera, formato
                    reg.update(timestamp_respuesta=ahora(), error=f"{type(e).__name__}: {e}")
                log.write(json.dumps(reg, ensure_ascii=False) + "\n")
                log.flush()
                if reg["error"] is None:
                    hechas[r["id"]] = reg
                    v = reg["interpretada"]["veredicto"] if reg["interpretada"] else "RESPUESTA INVÁLIDA"
                    print(f"[{variante}] {i:2}/{len(corpus)} {v:18} {r['oracion']}")
                    break
                print(f"[{variante}] {i:2}/{len(corpus)} error (intento {intento}): {reg['error'][:160]}")
                if "HTTP 400" in reg["error"] or "HTTP 401" in reg["error"] or "HTTP 403" in reg["error"] \
                        or "HTTP 404" in reg["error"]:
                    sys.exit("Error de clave o de nombre de modelo; revisa el mensaje de arriba.")
                time.sleep(pausa * intento * 2)                         # 429 o falla temporal: esperar más
            time.sleep(pausa)

    resultados = []
    for r in corpus:
        reg = hechas.get(r["id"])
        if reg is None:
            resultados.append({"id": r["id"], "oracion": r["oracion"], "veredicto": "SIN_RESPUESTA", "categorias": []})
            continue
        interp = reg["interpretada"]
        resultados.append({"id": r["id"], "oracion": r["oracion"],
                           "veredicto": interp["veredicto"] if interp else "RESPUESTA_INVALIDA",
                           "categorias": interp["categorias"] if interp else [],
                           "justificacion": interp["justificacion"] if interp else reg["respuesta_texto"],
                           "timestamp_respuesta": reg["timestamp_respuesta"]})
    print("Log guardado:", guardar_log(f"llm_{variante}", {
        "proveedor": proveedor, "modelo": modelo, "temperatura": TEMPERATURA, "max_tokens": MAX_TOKENS,
        "huella_prompt_sistema": huella, "prompt_en": f"prompts/{variante}.txt",
        "llamadas_en": f"logs/llm_{variante}_llamadas.jsonl"}, resultados))


def listar_modelos(clave):
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models",
                                 headers={"x-goog-api-key": clave})
    with urllib.request.urlopen(req, timeout=60, context=contexto_ssl()) as r:
        for m in json.loads(r.read().decode()).get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                print(m["name"].replace("models/", ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proveedor", choices=["gemini", "anthropic", "openai"], default="gemini")
    ap.add_argument("--modelo")
    ap.add_argument("--variante", choices=["zero_shot", "few_shot", "ambas"], default="ambas")
    ap.add_argument("--pausa", type=float, default=7.0)
    ap.add_argument("--listar-modelos", action="store_true")
    ap.add_argument("--solo-prompts", action="store_true", help="solo escribe prompts/*.txt, sin llamar a la API")
    a = ap.parse_args()

    if a.solo_prompts:
        os.makedirs(PROMPTS, exist_ok=True)
        for v in ("zero_shot", "few_shot"):
            with open(os.path.join(PROMPTS, f"{v}.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_sistema(v) + "\n\n----- mensaje de usuario (plantilla) -----\n"
                        + prompt_usuario("<oración>"))
        print("Prompts escritos en", PROMPTS)
        return

    clave = os.environ.get(VARIABLE_CLAVE[a.proveedor])
    if not clave:
        sys.exit(f"Falta la variable de entorno {VARIABLE_CLAVE[a.proveedor]} con tu clave de API.")
    if a.listar_modelos:
        return listar_modelos(clave)
    modelo = a.modelo or MODELOS_POR_DEFECTO[a.proveedor]
    variantes = ["zero_shot", "few_shot"] if a.variante == "ambas" else [a.variante]
    print(f"Proveedor: {a.proveedor} | modelo: {modelo} | temperatura: {TEMPERATURA}")
    for v in variantes:
        correr_variante(a.proveedor, modelo, clave, v, a.pausa)


if __name__ == "__main__":
    main()

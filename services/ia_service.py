import os
import requests

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

def _key():
    return os.environ.get("GROQ_API_KEY", "")


def _primer_producto(contexto):
    for linea in contexto.split("\n"):
        if linea.startswith("- ") and "|" in linea:
            return linea.split("|")[0].replace("- ", "").strip()
    return None


def buscar_competencia(termino, ubicacion):
    try:
        from duckduckgo_search import DDGS
        query = f"{termino} precio {ubicacion} comprar"
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return None
        lineas = []
        for r in results:
            titulo = r.get("title", "")[:60]
            cuerpo = r.get("body", "")[:130]
            if titulo and cuerpo:
                lineas.append(f"· {titulo}\n  {cuerpo}")
        return "\n".join(lineas) if lineas else None
    except Exception as e:
        print("DDGS error:", e)
        return None


def resumen_dia_ia(stats):
    GROQ_API_KEY = _key()
    fecha_str = __import__("datetime").date.today().strftime("%d/%m/%Y")
    if not GROQ_API_KEY:
        total = stats.get("total_ventas", 0)
        ops   = stats.get("cant_operaciones", 0)
        return f"Hoy recaudaste ${total:,.0f} en {ops} operaciones. (Configurá GROQ_API_KEY para el resumen con IA)"

    metodos = stats.get("por_metodo", {})
    metodos_str = ", ".join(f"{k}: ${v:,.0f}" for k, v in metodos.items()) or "ninguno"

    prompt = f"""Sos el asesor de un negocio de panadería/confitería. Escribí un resumen breve del día.
Usá el voseo rioplatense. Sin markdown. Máximo 3 oraciones. Sé positivo pero honesto.

DATOS DEL {fecha_str}:
- Total recaudado: ${stats.get('total_ventas', 0):,.0f}
- Caja libre: ${stats.get('total_caja', 0):,.0f}
- Ventas de productos: ${stats.get('total_productos', 0):,.0f}
- Desglose por método: {metodos_str}
- Gastos del día: ${stats.get('total_gastos', 0):,.0f}
- Ganancia estimada: ${stats.get('ganancia_neta', 0):,.0f}
- Operaciones totales: {stats.get('cant_operaciones', 0)}

Resumen del día:"""

    try:
        res = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 180,
                "temperature": 0.75,
            },
            timeout=35,
        )
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("ERROR IA cierre:", e)
        total = stats.get("total_ventas", 0)
        ops   = stats.get("cant_operaciones", 0)
        return f"Hoy recaudaste ${total:,.0f} en {ops} operaciones."


def preguntar_ia(contexto, pregunta):
    GROQ_API_KEY = _key()
    if not GROQ_API_KEY:
        return "Para activar la IA configurá la variable de entorno GROQ_API_KEY con tu clave de Groq (groq.com, es gratis)."

    ubicacion = "Argentina"
    if "Ubicación:" in contexto:
        try:
            ubicacion = contexto.split("Ubicación:")[1].split("\n")[0].strip()
        except Exception:
            pass

    termino = _primer_producto(contexto) or pregunta[:50]
    competencia = buscar_competencia(termino, ubicacion)

    if competencia:
        seccion_mercado = f"PRECIOS DE COMPETENCIA EN {ubicacion.upper()} (fuente: web):\n{competencia}"
    else:
        seccion_mercado = "MERCADO: No se encontraron precios de competencia disponibles."

    prompt = f"""Sos un asesor de negocios experto. Respondé de forma concreta en máximo 5 oraciones.

NEGOCIO DEL USUARIO:
{contexto}

{seccion_mercado}

PREGUNTA DEL USUARIO: {pregunta}

Analizá los precios del usuario vs la competencia y dá una recomendación concreta:"""

    try:
        res = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 350,
                "temperature": 0.7,
            },
            timeout=30,
        )
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("ERROR IA:", e)
        return "Error conectando con la IA. Verificá que GROQ_API_KEY esté configurada correctamente."

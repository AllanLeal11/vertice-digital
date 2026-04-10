import os
from anthropic import Anthropic
from .router import detectar_agente
from .marketing import MARKETING_PROMPT
from .ventas import VENTAS_PROMPT
from .desarrollador import DESARROLLADOR_PROMPT, procesar_respuesta_desarrollador
from .soporte import SOPORTE_PROMPT
from .asistente import ASISTENTE_PROMPT
from .disenador import DISENADOR_PROMPT

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

AGENTES = {
    "marketing":     {"prompt": MARKETING_PROMPT,     "nombre": "Director de Marketing"},
    "ventas":        {"prompt": VENTAS_PROMPT,         "nombre": "Director Comercial"},
    "desarrollador": {"prompt": DESARROLLADOR_PROMPT,  "nombre": "Lead Developer"},
    "soporte":       {"prompt": SOPORTE_PROMPT,        "nombre": "Jefe de Soporte"},
    "asistente":     {"prompt": ASISTENTE_PROMPT,      "nombre": "Asistente Ejecutivo"},
    "disenador":     {"prompt": DISENADOR_PROMPT,      "nombre": "Diseñador Gráfico"},
}

def calcular_tokens(mensaje: str, agente_key: str) -> int:
    """Calcula los tokens necesarios según el tipo de tarea."""
    if agente_key != "desarrollador":
        return 2000

    msg = mensaje.lower()

    palabras_grandes = [
        "sitio completo", "página completa", "web completa", "landing page completa",
        "varias secciones", "múltiples secciones", "hero", "portafolio",
        "e-commerce", "tienda", "completo", "profesional", "empresa", "full"
    ]
    palabras_pequenas = [
        "botón", "navbar", "footer", "componente", "fix", "corregir",
        "arreglar", "cambiar", "actualizar", "pequeño", "simple", "snippet"
    ]
    palabras_medianas = [
        "página", "web", "landing", "formulario", "contacto",
        "menú", "restaurant", "negocio", "servicios"
    ]

    if any(p in msg for p in palabras_grandes):
        return 8000
    elif any(p in msg for p in palabras_pequenas):
        return 2000
    elif any(p in msg for p in palabras_medianas):
        return 5000
    else:
        return 4000

def responder(mensaje: str, historial: list = None, agente_forzado: str = "auto") -> dict:
    if historial is None:
        historial = []

    if agente_forzado and agente_forzado != "auto" and agente_forzado in AGENTES:
        agente_key = agente_forzado
    else:
        agente_key = detectar_agente(mensaje)

    agente = AGENTES[agente_key]
    mensajes = historial + [{"role": "user", "content": mensaje}]
    max_tokens = calcular_tokens(mensaje, agente_key)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=agente["prompt"],
        messages=mensajes
    )

    respuesta_raw = response.content[0].text
    netlify_url = None
    netlify_error = None

    if agente_key == "desarrollador":
        resultado = procesar_respuesta_desarrollador(respuesta_raw)
        respuesta_raw = resultado["respuesta_limpia"]
        netlify_url = resultado.get("netlify_url")
        netlify_error = resultado.get("netlify_error")

    return {
        "agente": agente_key,
        "nombre_agente": agente["nombre"],
        "respuesta": respuesta_raw,
        "netlify_url": netlify_url,
        "netlify_error": netlify_error,
    }

def responder_paralelo(mensaje: str) -> dict:
    """Desarrollador y Diseñador trabajan simultáneamente."""
    import threading

    resultado_dev = {}
    resultado_dis = {}
    max_tokens = calcular_tokens(mensaje, "desarrollador")

    def trabajo_dev():
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=DESARROLLADOR_PROMPT,
            messages=[{"role": "user", "content": mensaje}]
        )
        raw = r.content[0].text
        resultado = procesar_respuesta_desarrollador(raw)
        resultado_dev["respuesta"] = resultado["respuesta_limpia"]
        resultado_dev["netlify_url"] = resultado.get("netlify_url")
        resultado_dev["netlify_error"] = resultado.get("netlify_error")

    def trabajo_dis():
        prompt_diseno = f"""El desarrollador está trabajando en esto: {mensaje}

Tu trabajo es revisar el enfoque del desarrollador y proponer mejoras visuales y de UX específicas.
Si el desarrollador va a crear código, sugerí mejoras de diseño concretas con valores CSS exactos."""
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=DISENADOR_PROMPT,
            messages=[{"role": "user", "content": prompt_diseno}]
        )
        resultado_dis["respuesta"] = r.content[0].text

    t1 = threading.Thread(target=trabajo_dev)
    t2 = threading.Thread(target=trabajo_dis)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return {
        "modo": "paralelo",
        "respuesta_dev": resultado_dev.get("respuesta", ""),
        "nombre_dev": "Lead Developer",
        "netlify_url": resultado_dev.get("netlify_url"),
        "netlify_error": resultado_dev.get("netlify_error"),
        "respuesta_diseno": resultado_dis.get("respuesta", ""),
        "nombre_diseno": "Diseñador Gráfico"
    }

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

def responder(mensaje: str, historial: list = None, agente_forzado: str = "auto") -> dict:
    if historial is None:
        historial = []

    if agente_forzado and agente_forzado != "auto" and agente_forzado in AGENTES:
        agente_key = agente_forzado
    else:
        agente_key = detectar_agente(mensaje)

    agente = AGENTES[agente_key]
    mensajes = historial + [{"role": "user", "content": mensaje}]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=agente["prompt"],
        messages=mensajes
    )

    respuesta_raw = response.content[0].text
    netlify_url = None
    netlify_error = None

    # Si es el desarrollador, procesar posible deploy a Netlify
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

    def trabajo_dev():
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
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

import os
from anthropic import Anthropic
from .router import detectar_agente
from .marketing import MARKETING_PROMPT
from .ventas import VENTAS_PROMPT
from .desarrollador import DESARROLLADOR_PROMPT
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

    return {
        "agente": agente_key,
        "nombre_agente": agente["nombre"],
        "respuesta": response.content[0].text
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
        resultado_dev["respuesta"] = r.content[0].text

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
        "respuesta_diseno": resultado_dis.get("respuesta", ""),
        "nombre_diseno": "Diseñador Gráfico"
    }

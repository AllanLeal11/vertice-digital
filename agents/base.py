import os
from anthropic import Anthropic
from .router import detectar_agente
from .marketing import MARKETING_PROMPT
from .ventas import VENTAS_PROMPT
from .desarrollador import DESARROLLADOR_PROMPT
from .soporte import SOPORTE_PROMPT
from .asistente import ASISTENTE_PROMPT

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

AGENTES = {
    "marketing":    {"prompt": MARKETING_PROMPT,    "nombre": "Agente de Marketing"},
    "ventas":       {"prompt": VENTAS_PROMPT,        "nombre": "Agente de Ventas"},
    "desarrollador":{"prompt": DESARROLLADOR_PROMPT, "nombre": "Agente Técnico"},
    "soporte":      {"prompt": SOPORTE_PROMPT,       "nombre": "Agente de Soporte"},
    "asistente":    {"prompt": ASISTENTE_PROMPT,     "nombre": "Asistente General"},
}

def responder(mensaje: str, historial: list = None) -> dict:
    """
    Recibe un mensaje, detecta el agente correcto y devuelve la respuesta.
    historial: lista de {"role": "user"/"assistant", "content": "..."} 
    """
    if historial is None:
        historial = []

    agente_key = detectar_agente(mensaje)
    agente = AGENTES[agente_key]

    mensajes = historial + [{"role": "user", "content": mensaje}]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=agente["prompt"],
        messages=mensajes
    )

    respuesta = response.content[0].text

    return {
        "agente": agente_key,
        "nombre_agente": agente["nombre"],
        "respuesta": respuesta
    }

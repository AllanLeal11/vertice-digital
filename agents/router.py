import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ROUTER_PROMPT = """Eres el router de Vértice Digital, una empresa de TI profesional en Costa Rica.
Tu única tarea es analizar el mensaje del cliente y responder con UNA SOLA PALABRA indicando qué agente debe atender:

- "marketing" → preguntas sobre redes sociales, publicidad, estrategia digital, SEO
- "ventas" → preguntas sobre precios, servicios, cotizaciones, contratos
- "desarrollador" → preguntas técnicas, bugs, desarrollo web, apps, código
- "soporte" → problemas con servicios existentes, errores, mantenimiento
- "asistente" → cualquier otra consulta general, información de la empresa

Responde SOLO con una de esas palabras, sin explicación."""

def detectar_agente(mensaje: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system=ROUTER_PROMPT,
        messages=[{"role": "user", "content": mensaje}]
    )
    agente = response.content[0].text.strip().lower()
    agentes_validos = ["marketing", "ventas", "desarrollador", "soporte", "asistente"]
    return agente if agente in agentes_validos else "asistente"

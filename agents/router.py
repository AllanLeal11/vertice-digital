import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ROUTER_PROMPT = """Eres el router de Vértice Digital, una empresa de TI profesional en Costa Rica.
Tu única tarea es analizar el mensaje y responder con UNA SOLA PALABRA indicando qué agente debe atender:

- "marketing" → redes sociales, publicidad, contenido, Instagram, Facebook, TikTok, SEO, posts, campañas, estrategia digital
- "ventas" → precios, cotizaciones, propuestas, contratos, servicios, cuánto cuesta, planes, paquetes
- "desarrollador" → código, bugs, desarrollo web, apps, HTML, CSS, JavaScript, Python, Flask, base de datos, API, deploy
- "soporte" → problemas con servicios existentes, errores, algo no funciona, mantenimiento, caído, lento
- "disenador" → diseño visual, UI, UX, colores, tipografía, logos, identidad de marca, Canva, estética, interfaz
- "asistente" → cualquier otra consulta general, información de la empresa, gestión, emails, organización

Responde SOLO con una de esas palabras, sin explicación."""

def detectar_agente(mensaje: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system=ROUTER_PROMPT,
        messages=[{"role": "user", "content": mensaje}]
    )
    agente = response.content[0].text.strip().lower()
    agentes_validos = ["marketing", "ventas", "desarrollador", "soporte", "disenador", "asistente"]
    return agente if agente in agentes_validos else "asistente"

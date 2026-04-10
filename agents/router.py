import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ROUTER_PROMPT = """Eres el router de Vértice Digital. Analizás el mensaje y respondés con UNA SOLA PALABRA:

- "marketing" → redes sociales, publicidad, SEO, contenido, posts, campañas
- "ventas" → precios, cotizaciones, propuestas, contratos, clientes nuevos
- "desarrollador" → código, web, app, página, sitio, programar, sistema, bot, deploy
- "soporte" → errores, problemas, bugs, caído, lento, arreglar
- "disenador" → diseño, logo, colores, tipografía, identidad visual
- "asistente" → agenda, email, tareas, organización, recordatorio, resumen

Si el mensaje pide crear algo visual o una web/app, respondé "desarrollador".

Respondé SOLO con una de esas palabras."""

PALABRAS_PARALELO = [
    'web', 'página', 'pagina', 'sitio', 'app', 'aplicación', 'aplicacion',
    'diseño', 'diseno', 'interfaz', 'ui', 'landing', 'frontend'
]

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

def es_tarea_paralela(mensaje: str) -> bool:
    """Detecta si la tarea requiere desarrollador + diseñador trabajando juntos."""
    msg = mensaje.lower()
    return any(p in msg for p in PALABRAS_PARALELO)

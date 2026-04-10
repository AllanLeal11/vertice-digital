import os
import threading
from anthropic import Anthropic
from .router import detectar_agente, detectar_combinacion
from .marketing import MARKETING_PROMPT
from .ventas import VENTAS_PROMPT
from .desarrollador import DESARROLLADOR_PROMPT
from .soporte import SOPORTE_PROMPT
from .asistente import ASISTENTE_PROMPT
from .disenador import DISENADOR_PROMPT

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Extended thinking: el agente razona internamente antes de responder
THINKING_BUDGET = 2000   # tokens internos de razonamiento
MAX_TOKENS = 8000        # tokens totales (thinking + respuesta)

AGENTES = {
    "marketing":     {"prompt": MARKETING_PROMPT,     "nombre": "Director de Marketing"},
    "ventas":        {"prompt": VENTAS_PROMPT,         "nombre": "Director Comercial"},
    "desarrollador": {"prompt": DESARROLLADOR_PROMPT,  "nombre": "Lead Developer"},
    "soporte":       {"prompt": SOPORTE_PROMPT,        "nombre": "Jefe de Soporte"},
    "asistente":     {"prompt": ASISTENTE_PROMPT,      "nombre": "Asistente Ejecutivo"},
    "disenador":     {"prompt": DISENADOR_PROMPT,      "nombre": "Diseñador Gráfico"},
}

def _llamar_claude(system_prompt: str, mensajes: list) -> str:
    """Llama a Claude con extended thinking habilitado y retorna solo el texto."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=MAX_TOKENS,
        thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET},
        system=system_prompt,
        messages=mensajes
    )
    # Extraer solo los bloques de texto (ignorar bloques de thinking internos)
    return next((b.text for b in response.content if b.type == "text"), "")

def responder(mensaje: str, historial: list = None, agente_forzado: str = "auto") -> dict:
    if historial is None:
        historial = []

    # Detectar si hay combinación paralela (a menos que se fuerce un agente específico)
    if agente_forzado in ("auto", "asistente"):
        combinacion = detectar_combinacion(mensaje)
        if combinacion:
            return responder_paralelo(mensaje, combinacion)

    # Agente único
    if agente_forzado and agente_forzado != "auto" and agente_forzado in AGENTES:
        agente_key = agente_forzado
    else:
        agente_key = detectar_agente(mensaje)

    agente = AGENTES[agente_key]
    mensajes = historial + [{"role": "user", "content": mensaje}]

    texto = _llamar_claude(agente["prompt"], mensajes)

    return {
        "agente": agente_key,
        "nombre_agente": agente["nombre"],
        "respuesta": texto,
        "modo": "normal"
    }

def responder_paralelo(mensaje: str, combinacion: dict) -> dict:
    """Múltiples agentes trabajan simultáneamente según la combinación detectada."""
    resultados = {}

    def trabajo_agente(agente_key: str):
        agente = AGENTES[agente_key]
        contexto = f"""Estás trabajando en equipo con otros agentes de Vértice Digital en esta tarea: {mensaje}

Equipo activo: {combinacion['descripcion']}

Vos sos el {agente['nombre']}. Ejecutá tu parte completa sin esperar a los demás.
Sé específico, concreto y entregá tu parte lista para usar."""

        texto = _llamar_claude(agente["prompt"], [{"role": "user", "content": contexto}])
        resultados[agente_key] = {
            "respuesta": texto,
            "nombre": agente["nombre"]
        }

    threads = []
    for agente_key in combinacion["agentes"]:
        t = threading.Thread(target=trabajo_agente, args=(agente_key,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return {
        "modo": "paralelo",
        "combinacion": combinacion["nombre"],
        "descripcion": combinacion["descripcion"],
        "resultados": resultados,
        "agente": combinacion["agentes"][0],
        "nombre_agente": combinacion["descripcion"],
        "respuesta": resultados.get(combinacion["agentes"][0], {}).get("respuesta", "")
    }

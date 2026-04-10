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

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=agente["prompt"],
        messages=mensajes
    )

    return {
        "agente": agente_key,
        "nombre_agente": agente["nombre"],
        "respuesta": response.content[0].text,
        "modo": "normal"
    }

def responder_paralelo(mensaje: str, combinacion: dict) -> dict:
    """Múltiples agentes trabajan simultáneamente según la combinación detectada."""
    resultados = {}

    def trabajo_agente(agente_key: str):
        agente = AGENTES[agente_key]
        # Prompt contextualizado para trabajo en equipo
        contexto = f"""Estás trabajando en equipo con otros agentes de Vértice Digital en esta tarea: {mensaje}

Equipo activo: {combinacion['descripcion']}

Vos sos el {agente['nombre']}. Ejecutá tu parte completa sin esperar a los demás.
Sé específico, concreto y entregá tu parte lista para usar."""

        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=agente["prompt"],
            messages=[{"role": "user", "content": contexto}]
        )
        resultados[agente_key] = {
            "respuesta": r.content[0].text,
            "nombre": agente["nombre"]
        }

    # Lanzar todos los agentes en paralelo
    threads = []
    for agente_key in combinacion["agentes"]:
        t = threading.Thread(target=trabajo_agente, args=(agente_key,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Construir respuesta con todos los resultados
    return {
        "modo": "paralelo",
        "combinacion": combinacion["nombre"],
        "descripcion": combinacion["descripcion"],
        "resultados": resultados,
        # Compatibilidad con frontend: primer agente como respuesta principal
        "agente": combinacion["agentes"][0],
        "nombre_agente": combinacion["descripcion"],
        "respuesta": resultados.get(combinacion["agentes"][0], {}).get("respuesta", "")
    }

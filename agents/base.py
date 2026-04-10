import os
import json
import threading
from anthropic import Anthropic
from .router import detectar_agente, detectar_combinacion
from .marketing import MARKETING_PROMPT
from .ventas import VENTAS_PROMPT
from .desarrollador import DESARROLLADOR_PROMPT
from .soporte import SOPORTE_PROMPT
from .asistente import ASISTENTE_PROMPT
from .disenador import DISENADOR_PROMPT
from .herramientas import TOOLS, buscar_negocios_maps, buscar_en_web

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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


def _ejecutar_herramienta(nombre: str, params: dict) -> str:
    """Despacha la llamada a la herramienta correcta y retorna JSON string."""
    if nombre == "buscar_negocios_maps":
        result = buscar_negocios_maps(
            consulta=params.get("consulta", ""),
            ubicacion=params.get("ubicacion", "Liberia, Guanacaste, Costa Rica"),
            radio_metros=params.get("radio_metros", 5000),
        )
    elif nombre == "buscar_en_web":
        result = buscar_en_web(consulta=params.get("consulta", ""))
    else:
        result = {"error": f"Herramienta desconocida: {nombre}"}
    return json.dumps(result, ensure_ascii=False)


def _bloque_a_dict(block) -> dict:
    """Convierte un ContentBlock del SDK a dict serializable para la API."""
    if block.type == "thinking":
        return {"type": "thinking", "thinking": block.thinking}
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {}


def _llamar_claude(system_prompt: str, mensajes: list) -> str:
    """
    Llama a Claude con extended thinking y herramientas habilitadas.
    Ejecuta el loop de tool use hasta obtener la respuesta final.
    """
    messages = list(mensajes)

    for _ in range(5):  # máximo 5 rondas de tool use por respuesta
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=MAX_TOKENS,
            thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET},
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # Si no hay más herramientas que llamar, retornar el texto final
        if response.stop_reason != "tool_use":
            return next((b.text for b in response.content if b.type == "text"), "")

        # Ejecutar cada herramienta solicitada
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                resultado = _ejecutar_herramienta(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": resultado,
                })

        # Agregar turno del asistente + resultados de herramientas al historial
        messages.append({"role": "assistant", "content": [_bloque_a_dict(b) for b in response.content]})
        messages.append({"role": "user", "content": tool_results})

    return next((b.text for b in response.content if b.type == "text"), "No pude completar la búsqueda.")


def responder(mensaje: str, historial: list = None, agente_forzado: str = "auto") -> dict:
    if historial is None:
        historial = []

    if agente_forzado in ("auto", "asistente"):
        combinacion = detectar_combinacion(mensaje)
        if combinacion:
            return responder_paralelo(mensaje, combinacion)

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
        "modo": "normal",
    }


def responder_paralelo(mensaje: str, combinacion: dict) -> dict:
    """Múltiples agentes trabajan simultáneamente según la combinación detectada."""
    resultados = {}

    def trabajo_agente(agente_key: str):
        agente = AGENTES[agente_key]
        contexto = (
            f"Estás trabajando en equipo con otros agentes de Vértice Digital en esta tarea: {mensaje}\n\n"
            f"Equipo activo: {combinacion['descripcion']}\n\n"
            f"Vos sos el {agente['nombre']}. Ejecutá tu parte completa sin esperar a los demás.\n"
            f"Podés usar las herramientas de búsqueda si necesitás datos reales.\n"
            f"Sé específico, concreto y entregá tu parte lista para usar."
        )
        texto = _llamar_claude(agente["prompt"], [{"role": "user", "content": contexto}])
        resultados[agente_key] = {"respuesta": texto, "nombre": agente["nombre"]}

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
        "respuesta": resultados.get(combinacion["agentes"][0], {}).get("respuesta", ""),
    }

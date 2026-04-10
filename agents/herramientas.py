"""
Herramientas externas disponibles para todos los agentes:
- Google Maps: buscar negocios por zona y categoría
- DuckDuckGo: búsqueda web en tiempo real (gratis, sin API key)
"""
import os
import requests
from duckduckgo_search import DDGS

GOOGLE_MAPS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")


def buscar_negocios_maps(consulta: str, ubicacion: str, radio_metros: int = 5000) -> dict:
    """Busca negocios en Google Maps Places API."""
    if not GOOGLE_MAPS_KEY:
        return {"error": "GOOGLE_MAPS_API_KEY no configurada en Railway"}

    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": f"{consulta} en {ubicacion}",
                "language": "es",
                "key": GOOGLE_MAPS_KEY,
            },
            timeout=10,
        )
        data = resp.json()

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            return {"error": f"Maps API devolvió: {data.get('status')}", "resultados": []}

        resultados = []
        for place in data.get("results", [])[:10]:
            resultados.append({
                "nombre":    place.get("name"),
                "direccion": place.get("formatted_address"),
                "rating":    place.get("rating"),
                "tipos":     place.get("types", [])[:3],
                "abierto":   place.get("opening_hours", {}).get("open_now"),
                "place_id":  place.get("place_id"),
            })

        return {"total": len(resultados), "resultados": resultados}

    except Exception as e:
        return {"error": str(e)}


def buscar_en_web(consulta: str) -> dict:
    """Busca información actual en internet usando DuckDuckGo (gratis, sin API key)."""
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(consulta, max_results=8, region="cr-es"))

        resultados = [
            {
                "titulo":      r.get("title"),
                "url":         r.get("href"),
                "descripcion": r.get("body"),
            }
            for r in raw
        ]
        return {"total": len(resultados), "resultados": resultados}

    except Exception as e:
        return {"error": str(e)}


# ─── Definiciones de herramientas para la API de Anthropic ────────────────────

TOOLS = [
    {
        "name": "buscar_negocios_maps",
        "description": (
            "Busca negocios reales en Google Maps por zona y categoría. "
            "Úsala cuando necesités encontrar restaurantes, hoteles, clínicas, tiendas, "
            "u otros negocios en una ubicación específica de Costa Rica."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "Tipo de negocio o búsqueda (ej: 'restaurantes', 'hoteles', 'clínicas dentales')"
                },
                "ubicacion": {
                    "type": "string",
                    "description": "Ciudad o zona (ej: 'Liberia, Guanacaste, Costa Rica')"
                },
                "radio_metros": {
                    "type": "integer",
                    "description": "Radio de búsqueda en metros (default 5000)",
                    "default": 5000
                }
            },
            "required": ["consulta", "ubicacion"]
        }
    },
    {
        "name": "buscar_en_web",
        "description": (
            "Busca información actual en internet. Úsala para verificar sitios web, "
            "redes sociales, contactos de empresas, precios de competencia, "
            "noticias recientes o cualquier dato que necesite ser actual."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "Términos de búsqueda (ej: 'Restaurante Don Carlos Liberia sitio web')"
                }
            },
            "required": ["consulta"]
        }
    }
]

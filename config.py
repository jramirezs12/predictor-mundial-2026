"""Configuración de fuentes de datos en vivo y claves de API.

Puedes poner las claves de tres formas (en orden de prioridad):
  1. Variables de entorno (recomendado):  FOOTBALL_DATA_KEY, ODDS_API_KEY
  2. Directamente aquí abajo (rápido para probar).
  3. Dejarlas vacías: la app usará la fuente pública gratis de ESPN para
     resultados y, sin clave de cuotas, mostrará recomendaciones del modelo.

Cómo conseguir las claves (gratis, ~2 min):
  - Resultados:  https://www.football-data.org/client/register  (competición WC)
  - Cuotas:      https://the-odds-api.com/  (tier gratis 500 req/mes)
"""

import os

# --- Claves de API (rellena aquí o usa variables de entorno) ---
FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

# --- Comportamiento en vivo ---
AUTO_REFRESH_SECONDS = 180        # cada cuánto refresca el servidor en segundo plano
ODDS_REGION = "us"                # región de cuotas para The Odds API (us, uk, eu)
ESPN_LEAGUE = "fifa.world"        # slug de la liga en la API pública de ESPN

# --- Normalización de nombres de equipos ---
# Las APIs usan nombres distintos a los nuestros. Mapea ALIAS -> nombre canónico.
TEAM_ALIASES = {
    "USA": "United States",
    "United States of America": "United States",
    "Czech Republic": "Czechia",
    "Turkey": "Türkiye",
    "Turkiye": "Türkiye",
    "Korea Republic": "South Korea",
    "Republic of Korea": "South Korea",
    "Korea, South": "South Korea",
    "IR Iran": "Iran",
    "Iran IR": "Iran",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Ivory Coast (Côte d'Ivoire)": "Ivory Coast",
    "DR Congo": "DR Congo",
    "Congo DR": "DR Congo",
    "Democratic Republic of the Congo": "DR Congo",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Bosnia-Herzegovina": "Bosnia & Herzegovina",
    "Curacao": "Curaçao",
    "Cabo Verde": "Cape Verde",
    "Cape Verde Islands": "Cape Verde",
    "Saudi Arabia (KSA)": "Saudi Arabia",
    "South Africa (RSA)": "South Africa",
}


def canonical_team(name: str) -> str | None:
    """Devuelve el nombre canónico de un equipo, o None si no se reconoce."""
    if not name:
        return None
    name = name.strip()
    if name in TEAM_ALIASES:
        return TEAM_ALIASES[name]
    return name  # se valida luego contra data.TEAMS

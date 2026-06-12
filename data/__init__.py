"""Ensambla todos los datos del Mundial 2026 en estructuras que consume el
motor de predicción y el servidor."""

from __future__ import annotations

from .teams import TEAM_DATA, GROUP_DRAW, HOSTS
from .players import KEY_PLAYERS
from .stadiums import STADIUMS
from .schedule import BRACKET_TEMPLATE, PHASE_WINDOWS, build_group_fixtures


def _build_team(name: str) -> dict:
    info = TEAM_DATA[name]
    team = {
        "name": name,
        "code": info["code"],
        "elo": info["elo"],
        "fifa_rank": info.get("fifa_rank"),
        "confederation": info.get("confederation", ""),
        "discipline": info.get("discipline", 1.0),
        "players": KEY_PLAYERS.get(name, []),
    }
    if "gf_avg" in info:
        team["gf_avg"] = info["gf_avg"]
    if "ga_avg" in info:
        team["ga_avg"] = info["ga_avg"]
    return team


# Diccionario nombre -> equipo completo.
TEAMS = {name: _build_team(name) for name in TEAM_DATA}

# Grupos con objetos de equipo completos.
GROUPS = {g: [TEAMS[n] for n in names] for g, names in GROUP_DRAW.items()}

# ELO medio de referencia del torneo (calibra las fuerzas ataque/defensa).
REFERENCE_ELO = sum(t["elo"] for t in TEAMS.values()) / len(TEAMS)

# Calendario de fase de grupos (72 partidos).
SCHEDULE = build_group_fixtures(GROUP_DRAW, STADIUMS)

# Sincroniza el ELO de referencia con el motor.
try:
    from engine import match_model
    match_model.REFERENCE_ELO = REFERENCE_ELO
except Exception:  # pragma: no cover
    pass

__all__ = [
    "TEAMS", "GROUPS", "GROUP_DRAW", "HOSTS", "STADIUMS",
    "BRACKET_TEMPLATE", "PHASE_WINDOWS", "SCHEDULE", "REFERENCE_ELO",
]

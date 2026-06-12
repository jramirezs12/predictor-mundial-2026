"""Calendario y estructura del bracket del Mundial 2026.

- Fase de grupos: 11–27 jun 2026 · 72 partidos (6 por grupo).
- Avanzan: 1º y 2º de cada grupo (24) + 8 mejores terceros = 32.
- Eliminación: 32avos → 16avos → 4tos → semis → final (19 jul, MetLife).

NOTA sobre el bracket: FIFA usa una tabla predeterminada para asignar a los 8
mejores terceros según de qué grupos salgan. Esa permutación exacta no estaba
publicada en las fuentes consultadas, así que el bracket de abajo es una
plantilla REPRESENTATIVA y balanceada (12 ganadores + 12 segundos + 8 terceros
= 32 equipos, sin revanchas inmediatas del mismo grupo). La simulación Monte
Carlo es válida; solo el emparejamiento fino de 32avos es aproximado.
"""

# Cada par son los dos "slots" de un cruce de 32avos:
#   W<g> = 1º del grupo g, R<g> = 2º del grupo g, T<n> = n-ésimo mejor 3º (1-8).
# El orden de la lista define el árbol: los índices 0-1 se cruzan en 16avos, etc.
BRACKET_TEMPLATE = [
    ("WA", "T1"), ("RE", "RF"),
    ("WB", "T2"), ("RG", "RH"),
    ("WC", "T3"), ("RI", "RJ"),
    ("WD", "T4"), ("RK", "RL"),
    ("WE", "T5"), ("WI", "RB"),
    ("WF", "T6"), ("WJ", "RA"),
    ("WG", "T7"), ("WK", "RD"),
    ("WH", "T8"), ("WL", "RC"),
]

# Ventana de cada fase (para mostrar en el calendario).
PHASE_WINDOWS = {
    "group": "11–27 jun 2026",
    "r32": "28 jun – 3 jul 2026",
    "r16": "4–7 jul 2026",
    "qf": "9–11 jul 2026",
    "sf": "14–15 jul 2026",
    "final": "19 jul 2026 · MetLife Stadium",
}


def build_group_fixtures(group_draw: dict, stadiums: list) -> list:
    """Genera los 72 partidos de fase de grupos (orden de jornadas estándar de
    un round-robin de 4: J1 1-4/2-3, J2 1-3/4-2, J3 1-2/3-4)."""
    rounds = [((0, 3), (1, 2)), ((0, 2), (3, 1)), ((0, 1), (2, 3))]
    fixtures = []
    venue_i = 0
    n_venues = len(stadiums)
    for gname, teams in group_draw.items():
        for matchday, pairs in enumerate(rounds, start=1):
            for hi, ai in pairs:
                stadium = stadiums[venue_i % n_venues]
                venue_i += 1
                fixtures.append({
                    "stage": "group",
                    "group": gname,
                    "matchday": matchday,
                    "home": teams[hi],
                    "away": teams[ai],
                    "venue": f'{stadium["name"]} · {stadium["city"]}',
                    "window": PHASE_WINDOWS["group"],
                })
    return fixtures

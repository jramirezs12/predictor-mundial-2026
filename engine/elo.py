"""Modelo ELO para selecciones.

Cada equipo tiene un rating. La probabilidad de que el local gane se basa en
la diferencia de ratings, con un ajuste por ventaja de localía:

    P(gana A) = 1 / (1 + 10 ^ (-(EloA - EloB + ventaja) / 400))

El ELO no distingue empates por sí solo, así que se reparte una porción de la
probabilidad hacia el empate en función de lo parejo que sea el partido. Esto
nos da un primer estimador 1X2 que luego se cruza con el modelo de goles.
"""

from __future__ import annotations


# Ventaja de localía expresada en puntos ELO. En mundiales el factor cancha es
# menor que en clubes; ~65 pts equivale a ~0.3 goles de ventaja promedio.
DEFAULT_HOME_ADVANTAGE = 65.0


def expected_score(elo_a: float, elo_b: float, home_advantage: float = 0.0) -> float:
    """Probabilidad esperada (entre 0 y 1) de que A puntúe contra B.

    Es el valor clásico de ELO: 1 / (1 + 10^(-d/400)).
    """
    diff = (elo_a + home_advantage) - elo_b
    return 1.0 / (1.0 + 10.0 ** (-diff / 400.0))


def match_probabilities(elo_a: float, elo_b: float,
                        home_advantage: float = 0.0,
                        draw_base: float = 0.27) -> dict:
    """Devuelve probabilidades 1X2 (gana A / empate / gana B) según ELO.

    `draw_base` es la probabilidad de empate cuando los equipos son idénticos.
    A medida que crece la diferencia de fuerza, el empate se vuelve menos
    probable. Esta es una aproximación; el motor principal usa el modelo de
    goles (Poisson/Dixon-Coles) para el 1X2 definitivo, pero el ELO sirve para
    calibrar la fuerza relativa y los lambdas.
    """
    p_a_raw = expected_score(elo_a, elo_b, home_advantage)

    # Cuanto más parejo el partido, más espacio para el empate.
    # |p_a_raw - 0.5| va de 0 (parejo) a 0.5 (paliza segura).
    closeness = 1.0 - 2.0 * abs(p_a_raw - 0.5)
    p_draw = draw_base * closeness

    remaining = 1.0 - p_draw
    p_a = remaining * p_a_raw
    p_b = remaining * (1.0 - p_a_raw)
    return {"home": p_a, "draw": p_draw, "away": p_b}


def update_rating(elo: float, opponent_elo: float, result: float,
                  k: float = 40.0, goal_diff: int = 0,
                  home_advantage: float = 0.0) -> float:
    """Actualiza un rating tras un partido (para mantener ratings al día).

    result: 1.0 victoria, 0.5 empate, 0.0 derrota.
    Incluye multiplicador por diferencia de goles, como el ELO de selecciones
    de eloratings.net.
    """
    exp = expected_score(elo, opponent_elo, home_advantage)
    # Multiplicador por margen de victoria (estilo World Football Elo).
    if goal_diff >= 2:
        margin = 1.0 + (goal_diff - 1) * 0.5 if goal_diff == 2 else (11 + goal_diff) / 8.0
    else:
        margin = 1.0
    return elo + k * margin * (result - exp)


def win_probability_no_draw(elo_a: float, elo_b: float,
                            home_advantage: float = 0.0) -> float:
    """Probabilidad de que A avance en eliminatoria (sin empates: hay prórroga
    y penales). Se usa en fases de eliminación directa para resolver el ganador
    cuando el modelo de goles produce empate."""
    return expected_score(elo_a, elo_b, home_advantage)

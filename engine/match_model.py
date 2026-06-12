"""Modelo de partido: convierte fuerza de equipos en goles esperados (lambdas)
y produce TODAS las estadísticas de un enfrentamiento.

Stack combinado (como recomienda la investigación):
  - ELO calibra la fuerza relativa -> fuerzas de ataque/defensa.
  - Esas fuerzas + promedio goleador de la competición -> lambdas (Poisson).
  - Dixon-Coles corrige los marcadores bajos.
  - De la matriz de marcadores salen 1X2, over/under, BTTS, hándicaps, etc.
  - Tarjetas y goleadores se modelan aparte sobre la intensidad del partido.
"""

from __future__ import annotations

import math

from . import elo as elo_mod
from . import poisson as poisson_mod


# Goles promedio por equipo en un partido de Mundial (total ~2.7).
LEAGUE_AVG_GOALS_PER_TEAM = 1.35
# Sensibilidad de ataque/defensa al ELO (por punto). Calibrada para que las
# probabilidades 1X2 del modelo se acerquen a las de un mercado eficiente y no
# sea sobreconfiado en partidos muy disparejos.
ELO_ATTACK_SENSITIVITY = 0.00135
ELO_DEFENSE_SENSITIVITY = 0.00135
# ELO medio de referencia del torneo (se recalibra con los datos reales).
REFERENCE_ELO = 1825.0
# Ventaja de localía en goles para selecciones anfitrionas.
HOME_GOAL_BOOST = 0.20
# Correlación Dixon-Coles para marcadores bajos.
DIXON_COLES_RHO = -0.13
# Tarjetas amarillas base por equipo por partido (referencia mundialista).
BASE_YELLOWS_PER_TEAM = 1.95
BASE_REDS_PER_TEAM = 0.11
# Córners base por equipo por partido.
BASE_CORNERS_PER_TEAM = 5.0


def _elo_attack_strength(team_elo: float, ref_elo: float) -> float:
    return math.exp(ELO_ATTACK_SENSITIVITY * (team_elo - ref_elo))


def _elo_defense_strength(team_elo: float, ref_elo: float) -> float:
    # Más ELO -> concede menos -> fuerza defensiva < 1 (multiplica los goles
    # que le hacen). Por eso el signo negativo.
    return math.exp(-ELO_DEFENSE_SENSITIVITY * (team_elo - ref_elo))


def team_strengths(team: dict, ref_elo: float | None = None,
                   data_weight: float = 0.35) -> tuple[float, float]:
    """Devuelve (ataque, defensa) relativos al promedio (1.0 = media).

    Parte del ELO y, si el equipo trae estadísticas reales de goles
    (`gf_avg` goles a favor, `ga_avg` goles en contra por partido), las mezcla.
    """
    if ref_elo is None:
        ref_elo = REFERENCE_ELO
    atk = _elo_attack_strength(team["elo"], ref_elo)
    dfn = _elo_defense_strength(team["elo"], ref_elo)

    gf = team.get("gf_avg")
    ga = team.get("ga_avg")
    if gf is not None and gf > 0:
        data_atk = gf / LEAGUE_AVG_GOALS_PER_TEAM
        atk = (1 - data_weight) * atk + data_weight * data_atk
    if ga is not None and ga > 0:
        data_dfn = ga / LEAGUE_AVG_GOALS_PER_TEAM
        dfn = (1 - data_weight) * dfn + data_weight * data_dfn
    return atk, dfn


def expected_goals(home: dict, away: dict, *,
                   neutral: bool = True,
                   home_is_host: bool = False,
                   ref_elo: float | None = None) -> tuple[float, float]:
    """Calcula los lambdas (goles esperados) de local y visitante.

    En un Mundial la mayoría de partidos son en campo neutral, salvo los del
    país anfitrión. `home_is_host` aplica la ventaja de localía real.
    """
    if ref_elo is None:
        ref_elo = REFERENCE_ELO
    atk_h, dfn_h = team_strengths(home, ref_elo)
    atk_a, dfn_a = team_strengths(away, ref_elo)

    lam_home = LEAGUE_AVG_GOALS_PER_TEAM * atk_h * dfn_a
    lam_away = LEAGUE_AVG_GOALS_PER_TEAM * atk_a * dfn_h

    if home_is_host:
        # Solo el anfitrión recibe el empujón de localía real.
        lam_home += HOME_GOAL_BOOST
        lam_away = max(0.15, lam_away - HOME_GOAL_BOOST * 0.5)

    # Pequeño ajuste ELO sobre la supremacía para no depender solo del producto
    # ataque*defensa (mantiene coherencia con el rating relativo).
    elo_adv = home.get("elo", ref_elo) - away.get("elo", ref_elo)
    if home_is_host:
        elo_adv += elo_mod.DEFAULT_HOME_ADVANTAGE
    supremacy_shift = elo_adv / 2100.0  # suave
    lam_home = max(0.12, lam_home + supremacy_shift)
    lam_away = max(0.12, lam_away - supremacy_shift)
    return lam_home, lam_away


def _expected_cards(lam_home: float, lam_away: float,
                    home: dict, away: dict) -> dict:
    """Modela tarjetas. Partidos parejos/tensos => más tarjetas."""
    total_goals = lam_home + lam_away
    # Intensidad: partidos cerrados (poca diferencia de goles esperada) y de
    # bajo marcador suelen ser más ásperos.
    closeness = 1.0 / (1.0 + abs(lam_home - lam_away))
    intensity = 0.85 + 0.4 * closeness

    disc_h = home.get("discipline", 1.0)
    disc_a = away.get("discipline", 1.0)

    yellow_h = BASE_YELLOWS_PER_TEAM * disc_h * intensity
    yellow_a = BASE_YELLOWS_PER_TEAM * disc_a * intensity
    red_h = BASE_REDS_PER_TEAM * disc_h * intensity
    red_a = BASE_REDS_PER_TEAM * disc_a * intensity

    return {
        "yellow_home": round(yellow_h, 2),
        "yellow_away": round(yellow_a, 2),
        "yellow_total": round(yellow_h + yellow_a, 2),
        "red_home": round(red_h, 3),
        "red_away": round(red_a, 3),
        "red_total": round(red_h + red_a, 3),
        # Probabilidad de que haya al menos una roja (Poisson).
        "prob_any_red": round(1 - poisson_mod.poisson_pmf(0, red_h + red_a), 3),
        # Over 3.5 tarjetas amarillas totales.
        "prob_over_3_5_yellows": round(
            1 - sum(poisson_mod.poisson_pmf(k, yellow_h + yellow_a) for k in range(4)), 3),
    }


def _expected_corners(lam_home: float, lam_away: float,
                      home: dict, away: dict) -> dict:
    """Córners aproximados: escalan con la presión ofensiva (lambda)."""
    corners_h = BASE_CORNERS_PER_TEAM * (0.6 + 0.4 * lam_home / LEAGUE_AVG_GOALS_PER_TEAM)
    corners_a = BASE_CORNERS_PER_TEAM * (0.6 + 0.4 * lam_away / LEAGUE_AVG_GOALS_PER_TEAM)
    total = corners_h + corners_a
    return {
        "corners_home": round(corners_h, 1),
        "corners_away": round(corners_a, 1),
        "corners_total": round(total, 1),
        "prob_over_9_5_corners": round(
            1 - sum(poisson_mod.poisson_pmf(k, total) for k in range(10)), 3),
    }


def _player_projection(team: dict, team_lambda: float, top: int = 4) -> list[dict]:
    """Reparte los goles esperados del equipo entre sus jugadores clave según
    su 'goal_share' y calcula P(marca al menos 1) y goles esperados."""
    players = team.get("players", [])
    if not players:
        return []
    scorers = [p for p in players if p.get("goal_share", 0) > 0]
    scorers.sort(key=lambda p: p.get("goal_share", 0), reverse=True)
    out = []
    for p in scorers[:top]:
        lam_p = team_lambda * p["goal_share"]
        out.append({
            "name": p["name"],
            "position": p.get("position", ""),
            "club": p.get("club", ""),
            "expected_goals": round(lam_p, 3),
            "prob_to_score": round(1 - poisson_mod.poisson_pmf(0, lam_p), 3),
            "prob_brace": round(1 - sum(poisson_mod.poisson_pmf(k, lam_p) for k in range(2)), 3),
        })
    return out


def predict_match(home: dict, away: dict, *,
                  home_is_host: bool = False,
                  stage: str = "group",
                  ref_elo: float | None = None,
                  max_goals: int = 10) -> dict:
    """Predicción completa de un partido con TODAS las estadísticas."""
    lam_home, lam_away = expected_goals(
        home, away, home_is_host=home_is_host, ref_elo=ref_elo)

    matrix = poisson_mod.score_matrix(lam_home, lam_away, DIXON_COLES_RHO, max_goals)
    outcomes = poisson_mod.outcome_probabilities(matrix)
    elo_outcomes = elo_mod.match_probabilities(
        home["elo"], away["elo"],
        elo_mod.DEFAULT_HOME_ADVANTAGE if home_is_host else 0.0)

    # Mezcla suave: el modelo de goles manda, el ELO calibra (70/30).
    blended = {
        k: round(0.7 * outcomes[k] + 0.3 * elo_outcomes[k], 4)
        for k in ("home", "draw", "away")
    }
    s = sum(blended.values())
    blended = {k: v / s for k, v in blended.items()}

    ou25 = poisson_mod.over_under(matrix, 2.5)
    ou15 = poisson_mod.over_under(matrix, 1.5)
    ou35 = poisson_mod.over_under(matrix, 3.5)
    btts = poisson_mod.both_teams_to_score(matrix)
    cs = poisson_mod.clean_sheet_probabilities(matrix)
    dc = poisson_mod.double_chance(blended)
    ah = poisson_mod.asian_handicap_minus_one(matrix)

    result = {
        "home_team": home["name"],
        "away_team": away["name"],
        "stage": stage,
        "expected_goals": {
            "home": round(lam_home, 2),
            "away": round(lam_away, 2),
            "total": round(lam_home + lam_away, 2),
        },
        "result_1x2": {
            "home_win": round(blended["home"], 4),
            "draw": round(blended["draw"], 4),
            "away_win": round(blended["away"], 4),
        },
        "double_chance": {k: round(v, 4) for k, v in dc.items()},
        "most_likely_scores": [
            {"score": f'{s["home"]}-{s["away"]}', "prob": round(s["prob"], 4)}
            for s in poisson_mod.most_likely_scores(matrix, 6)
        ],
        "goals_markets": {
            "over_1_5": round(ou15["over"], 4), "under_1_5": round(ou15["under"], 4),
            "over_2_5": round(ou25["over"], 4), "under_2_5": round(ou25["under"], 4),
            "over_3_5": round(ou35["over"], 4), "under_3_5": round(ou35["under"], 4),
            "btts_yes": round(btts["yes"], 4), "btts_no": round(btts["no"], 4),
        },
        "clean_sheet": {
            "home": round(cs["home"], 4), "away": round(cs["away"], 4),
        },
        "asian_handicap": {k: round(v, 4) for k, v in ah.items()},
        "cards": _expected_cards(lam_home, lam_away, home, away),
        "corners": _expected_corners(lam_home, lam_away, home, away),
        "players": {
            "home": _player_projection(home, lam_home),
            "away": _player_projection(away, lam_away),
        },
    }
    return result

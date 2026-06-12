"""Modelo de Poisson y corrección Dixon-Coles para la distribución de goles.

Poisson puro:  P(X = k) = e^(-lambda) * lambda^k / k!
donde lambda = goles esperados de un equipo.

Dixon-Coles añade un parámetro de dependencia (rho) que corrige el defecto del
Poisson puro: subestima los marcadores 0-0, 1-0, 0-1 y sobreestima el 1-1.
"""

from __future__ import annotations

import math


def poisson_pmf(k: int, lam: float) -> float:
    """Probabilidad de Poisson de observar exactamente k goles."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def dixon_coles_tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    """Factor de corrección tau(x, y) de Dixon-Coles para marcadores bajos."""
    if x == 0 and y == 0:
        return 1.0 - lam * mu * rho
    if x == 0 and y == 1:
        return 1.0 + lam * rho
    if x == 1 and y == 0:
        return 1.0 + mu * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(lam_home: float, lam_away: float,
                 rho: float = -0.13, max_goals: int = 10) -> list[list[float]]:
    """Matriz de probabilidades de cada marcador (home goals x away goals).

    matrix[i][j] = P(local marca i, visitante marca j), ya corregida por
    Dixon-Coles y renormalizada para que sume 1.
    """
    matrix = [[0.0] * (max_goals + 1) for _ in range(max_goals + 1)]
    total = 0.0
    for i in range(max_goals + 1):
        p_home = poisson_pmf(i, lam_home)
        for j in range(max_goals + 1):
            p_away = poisson_pmf(j, lam_away)
            tau = dixon_coles_tau(i, j, lam_home, lam_away, rho)
            p = p_home * p_away * tau
            if p < 0:
                p = 0.0
            matrix[i][j] = p
            total += p
    if total > 0:
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                matrix[i][j] /= total
    return matrix


def outcome_probabilities(matrix: list[list[float]]) -> dict:
    """A partir de la matriz de marcadores calcula el 1X2."""
    p_home = p_draw = p_away = 0.0
    n = len(matrix)
    for i in range(n):
        for j in range(n):
            p = matrix[i][j]
            if i > j:
                p_home += p
            elif i == j:
                p_draw += p
            else:
                p_away += p
    return {"home": p_home, "draw": p_draw, "away": p_away}


def most_likely_scores(matrix: list[list[float]], top: int = 5) -> list[dict]:
    """Lista de los marcadores más probables."""
    scores = []
    n = len(matrix)
    for i in range(n):
        for j in range(n):
            scores.append({"home": i, "away": j, "prob": matrix[i][j]})
    scores.sort(key=lambda s: s["prob"], reverse=True)
    return scores[:top]


def over_under(matrix: list[list[float]], line: float = 2.5) -> dict:
    """Probabilidad de Over/Under para una línea de goles totales."""
    p_over = 0.0
    n = len(matrix)
    for i in range(n):
        for j in range(n):
            if i + j > line:
                p_over += matrix[i][j]
    return {"over": p_over, "under": 1.0 - p_over}


def both_teams_to_score(matrix: list[list[float]]) -> dict:
    """Probabilidad de que ambos equipos marquen (BTTS / Ambos anotan)."""
    p_yes = 0.0
    n = len(matrix)
    for i in range(1, n):
        for j in range(1, n):
            p_yes += matrix[i][j]
    return {"yes": p_yes, "no": 1.0 - p_yes}


def clean_sheet_probabilities(matrix: list[list[float]]) -> dict:
    """Probabilidad de portería a cero (clean sheet) para cada equipo."""
    n = len(matrix)
    # Local deja a cero -> visitante marca 0.
    p_home_cs = sum(matrix[i][0] for i in range(n))
    # Visitante deja a cero -> local marca 0.
    p_away_cs = sum(matrix[0][j] for j in range(n))
    return {"home": p_home_cs, "away": p_away_cs}


def expected_total_goals(matrix: list[list[float]]) -> float:
    n = len(matrix)
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += (i + j) * matrix[i][j]
    return total


def double_chance(outcomes: dict) -> dict:
    """Mercados de doble oportunidad."""
    return {
        "1X": outcomes["home"] + outcomes["draw"],
        "12": outcomes["home"] + outcomes["away"],
        "X2": outcomes["draw"] + outcomes["away"],
    }


def asian_handicap_minus_one(matrix: list[list[float]]) -> dict:
    """Handicap asiático -1 para el local (gana por 2+)."""
    n = len(matrix)
    p_cover = sum(matrix[i][j] for i in range(n) for j in range(n) if i - j >= 2)
    p_push = sum(matrix[i][j] for i in range(n) for j in range(n) if i - j == 1)
    return {"home_-1": p_cover, "push": p_push, "away_+1": 1.0 - p_cover - p_push}

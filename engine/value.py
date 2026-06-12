"""Análisis de valor: detecta apuestas mal valoradas comparando la probabilidad
del MODELO con la cuota de la casa de apuestas, y dimensiona la apuesta con el
criterio de Kelly.

Conceptos:
  - Cuota decimal `o`: si aciertas, cobras `o` por cada 1 apostado (ganancia o-1).
  - Probabilidad implícita de la casa: `1/o` (incluye su margen).
  - VALOR (apuesta de valor): existe cuando la prob. del modelo `p` es mayor que
    la implícita de la casa -> el valor esperado es positivo.
        EV por unidad = p*o - 1     (positivo = apuesta con valor)
  - Criterio de Kelly: fracción óptima de la banca a apostar para maximizar el
    crecimiento a largo plazo:
        f* = (p*o - 1) / (o - 1)
    En la práctica se usa "Kelly fraccionado" (1/4 o 1/2 de f*) porque el Kelly
    completo es muy volátil y nuestras probabilidades tienen incertidumbre.
"""

from __future__ import annotations

import random


def implied_probability(decimal_odds: float) -> float:
    """Probabilidad que implica una cuota de la casa (con su margen)."""
    if decimal_odds <= 1.0:
        return 1.0
    return 1.0 / decimal_odds


def devig(odds: list) -> list:
    """Quita el margen de la casa: convierte un conjunto de cuotas de un mismo
    mercado (ej. 1, X, 2) en probabilidades 'justas' que suman 1.

    La suma de las probabilidades implícitas de una casa es > 1 (ese exceso es
    su margen/ganancia). Repartiéndolo proporcionalmente obtenemos la mejor
    estimación de probabilidad real del mercado, sin margen.
    """
    implied = [1.0 / o if o and o > 1 else 0.0 for o in odds]
    s = sum(implied)
    if s <= 0:
        return [0.0 for _ in odds]
    return [p / s for p in implied]


def expected_value(model_prob: float, decimal_odds: float) -> float:
    """Valor esperado por unidad apostada. Positivo => apuesta con valor."""
    return model_prob * decimal_odds - 1.0


def edge(model_prob: float, decimal_odds: float) -> float:
    """Ventaja: cuánto subestima la casa el resultado (prob modelo - implícita)."""
    return model_prob - implied_probability(decimal_odds)


def kelly_fraction(model_prob: float, decimal_odds: float) -> float:
    """Fracción de Kelly (completa). 0 si no hay valor."""
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    f = (model_prob * decimal_odds - 1.0) / b
    return max(0.0, min(1.0, f))


def analyze(model_prob: float, decimal_odds: float,
            kelly_multiplier: float = 0.25) -> dict:
    """Análisis completo de una apuesta dada la prob del modelo y la cuota."""
    ev = expected_value(model_prob, decimal_odds)
    full_kelly = kelly_fraction(model_prob, decimal_odds)
    return {
        "model_prob": round(model_prob, 4),
        "fair_odds": round(1.0 / model_prob, 2) if model_prob > 0 else None,
        "book_odds": round(decimal_odds, 2),
        "implied_prob": round(implied_probability(decimal_odds), 4),
        "edge": round(edge(model_prob, decimal_odds), 4),
        "ev": round(ev, 4),
        "is_value": ev > 0,
        "kelly_full": round(full_kelly, 4),
        "kelly_stake_fraction": round(full_kelly * kelly_multiplier, 4),
    }


def simulate_bankroll(bets: list, start_bankroll: float, target: float,
                      kelly_multiplier: float = 0.25, n_sims: int = 10000,
                      seed: int = 2026) -> dict:
    """Simulación Monte Carlo de la evolución de la banca apostando, en orden,
    una lista de apuestas de valor con stake de Kelly fraccionado.

    bets: lista de {"model_prob": p, "book_odds": o}.
    Devuelve percentiles de la banca final, prob. de terminar con ganancia y
    prob. de alcanzar el objetivo `target` en algún momento.
    """
    rng = random.Random(seed)
    finals = []
    reached = 0
    busted = 0  # banca prácticamente perdida (<1% del inicio)
    for _ in range(n_sims):
        bankroll = start_bankroll
        hit_target = False
        for bet in bets:
            p = bet["model_prob"]
            o = bet["book_odds"]
            f = kelly_fraction(p, o) * kelly_multiplier
            stake = bankroll * f
            if rng.random() < p:
                bankroll += stake * (o - 1.0)
            else:
                bankroll -= stake
            if bankroll >= target:
                hit_target = True
            if bankroll < start_bankroll * 0.01:
                break
        finals.append(bankroll)
        if hit_target:
            reached += 1
        if bankroll < start_bankroll * 0.01:
            busted += 1

    finals.sort()

    def pctl(q):
        idx = min(len(finals) - 1, int(q * len(finals)))
        return round(finals[idx], 0)

    return {
        "n_sims": n_sims,
        "n_bets": len(bets),
        "start": start_bankroll,
        "target": target,
        "median": pctl(0.50),
        "p10": pctl(0.10),
        "p25": pctl(0.25),
        "p75": pctl(0.75),
        "p90": pctl(0.90),
        "mean": round(sum(finals) / len(finals), 0),
        "prob_profit": round(sum(1 for x in finals if x > start_bankroll) / n_sims, 4),
        "prob_reach_target": round(reached / n_sims, 4),
        "prob_bust": round(busted / n_sims, 4),
    }

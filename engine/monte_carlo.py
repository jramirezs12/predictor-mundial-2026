"""Simulación Monte Carlo del Mundial 2026 completo.

Formato 2026 (48 equipos):
  - 12 grupos (A-L) de 4 equipos, todos contra todos.
  - Avanzan los 2 primeros de cada grupo (24) + los 8 mejores terceros = 32.
  - Eliminación directa: 32avos -> 16avos -> 8vos -> 4tos -> semis -> final.

Se sortean miles de torneos muestreando marcadores con los lambdas del modelo
de goles. Agregando todas las simulaciones obtenemos la probabilidad de que
cada selección llegue a cada ronda y gane el título.
"""

from __future__ import annotations

import math
import random

from . import match_model
from . import elo as elo_mod


def sample_poisson(lam: float, rng: random.Random) -> int:
    """Genera un número de goles ~ Poisson(lam) (algoritmo de Knuth)."""
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def simulate_score(home: dict, away: dict, rng: random.Random,
                   home_is_host: bool = False) -> tuple[int, int]:
    lam_h, lam_a = match_model.expected_goals(home, away, home_is_host=home_is_host)
    return sample_poisson(lam_h, rng), sample_poisson(lam_a, rng)


def simulate_group(teams: list[dict], rng: random.Random,
                   hosts: set[str] | None = None) -> list[dict]:
    """Simula un grupo (round robin) y devuelve los equipos ordenados con sus
    puntos y diferencia de gol."""
    hosts = hosts or set()
    table = {t["name"]: {"team": t, "pts": 0, "gf": 0, "ga": 0, "gd": 0, "w": 0}
             for t in teams}
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            a, b = teams[i], teams[j]
            host = a["name"] in hosts
            ha, hb = simulate_score(a, b, rng, home_is_host=host)
            ta, tb = table[a["name"]], table[b["name"]]
            ta["gf"] += ha; ta["ga"] += hb
            tb["gf"] += hb; tb["ga"] += ha
            if ha > hb:
                ta["pts"] += 3; ta["w"] += 1
            elif hb > ha:
                tb["pts"] += 3; tb["w"] += 1
            else:
                ta["pts"] += 1; tb["pts"] += 1
    for row in table.values():
        row["gd"] = row["gf"] - row["ga"]
    ranked = sorted(table.values(),
                    key=lambda r: (r["pts"], r["gd"], r["gf"], rng.random()),
                    reverse=True)
    return ranked


def _knockout_winner(a: dict, b: dict, rng: random.Random) -> dict:
    """Resuelve un cruce de eliminación directa (con prórroga/penales)."""
    ha, hb = simulate_score(a, b, rng)
    if ha > hb:
        return a
    if hb > ha:
        return b
    # Empate -> prórroga/penales resueltos por ELO.
    p = elo_mod.win_probability_no_draw(a["elo"], b["elo"])
    return a if rng.random() < p else b


def simulate_tournament(groups: dict, bracket_template: list, rng: random.Random,
                        hosts: set[str] | None = None) -> dict:
    """Simula un torneo completo. Devuelve hasta dónde llegó cada equipo.

    bracket_template: lista de 16 cruces de 32avos, cada uno (slotA, slotB)
    donde un slot es 'W<grupo>' (1º), 'R<grupo>' (2º) o 'T<n>' (n-ésimo mejor
    tercero, 1-8).
    """
    hosts = hosts or set()
    standings = {}      # grupo -> ranked list
    thirds = []
    for gname, teams in groups.items():
        ranked = simulate_group(teams, rng, hosts)
        standings[gname] = ranked
        thirds.append({"group": gname, "row": ranked[2]})

    # 8 mejores terceros.
    thirds.sort(key=lambda x: (x["row"]["pts"], x["row"]["gd"], x["row"]["gf"],
                               rng.random()), reverse=True)
    best_thirds = [t["row"]["team"] for t in thirds[:8]]

    def resolve(slot: str) -> dict:
        if slot.startswith("W"):
            return standings[slot[1:]][0]["team"]
        if slot.startswith("R"):
            return standings[slot[1:]][1]["team"]
        if slot.startswith("T"):
            return best_thirds[int(slot[1:]) - 1]
        raise ValueError(f"slot inválido: {slot}")

    # Rondas alcanzadas (para estadística agregada).
    reached = {}
    def mark(team, stage):
        reached[team["name"]] = stage

    # Todos los equipos arrancan en "group".
    for teams in groups.values():
        for t in teams:
            reached[t["name"]] = "group"

    # 32avos.
    round_teams = []
    for slot_a, slot_b in bracket_template:
        ta, tb = resolve(slot_a), resolve(slot_b)
        round_teams.append((ta, tb))
    for ta, tb in round_teams:
        mark(ta, "r32"); mark(tb, "r32")

    stage_order = ["r16", "qf", "sf", "final", "champion"]
    winners = []
    for ta, tb in round_teams:
        winners.append(_knockout_winner(ta, tb, rng))

    stages = ["r16", "qf", "sf", "final"]
    for stage in stages:
        for w in winners:
            mark(w, stage)
        next_round = []
        for i in range(0, len(winners), 2):
            w = _knockout_winner(winners[i], winners[i + 1], rng)
            next_round.append(w)
        winners = next_round
    champion = winners[0]
    mark(champion, "champion")

    return {"reached": reached, "champion": champion["name"]}


STAGE_RANK = {"group": 0, "r32": 1, "r16": 2, "qf": 3, "sf": 4,
              "final": 5, "champion": 6}


def run_simulations(groups: dict, bracket_template: list, n: int = 10000,
                    hosts: set[str] | None = None, seed: int = 2026) -> dict:
    """Corre N torneos y agrega probabilidades por equipo."""
    rng = random.Random(seed)
    all_teams = [t["name"] for teams in groups.values() for t in teams]
    counters = {name: {"r32": 0, "r16": 0, "qf": 0, "sf": 0,
                       "final": 0, "champion": 0} for name in all_teams}

    for _ in range(n):
        res = simulate_tournament(groups, bracket_template, rng, hosts)
        for name, stage in res["reached"].items():
            r = STAGE_RANK[stage]
            for st in ("r32", "r16", "qf", "sf", "final", "champion"):
                if r >= STAGE_RANK[st]:
                    counters[name][st] += 1

    probs = {}
    for name, c in counters.items():
        probs[name] = {k: round(v / n, 4) for k, v in c.items()}
    # Ordenar por probabilidad de campeón.
    ranked = sorted(probs.items(), key=lambda kv: kv[1]["champion"], reverse=True)
    return {"n": n, "probabilities": dict(ranked)}

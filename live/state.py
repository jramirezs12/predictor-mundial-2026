"""Estado en vivo del torneo.

A partir de la lista de resultados jugados:
  - Recalcula el ELO de cada selección (parte del ELO base y lo actualiza
    partido a partido en orden cronológico).
  - Recalcula las clasificaciones reales de cada grupo (puntos, GF, GA).
  - Expone el ELO actual para que las predicciones de los partidos restantes
    usen la forma real del torneo, no solo los ratings de pretemporada.

Todo es idempotente: recalcula desde cero cada vez que llegan resultados
nuevos, así que llamarlo varias veces no acumula errores.
"""

from __future__ import annotations

import threading

import data
from data.teams import TEAM_DATA, GROUP_DRAW, HOSTS
from engine import elo as elo_mod

_lock = threading.Lock()
_results: list = []          # resultados normalizados (jugados y/o programados)
_elo: dict = {}              # ELO actual por equipo
_last_updated: str | None = None
_source: str = "—"           # de dónde vinieron los datos


# K-factor por fase (importancia del partido, estilo World Football Elo).
_K_BY_STAGE = {"group": 50.0, "r32": 55.0, "r16": 55.0,
               "qf": 60.0, "sf": 60.0, "final": 60.0}


def _base_elo() -> dict:
    return {name: info["elo"] for name, info in TEAM_DATA.items()}


def _finished(r: dict) -> bool:
    return (r.get("status") == "finished"
            and r.get("home_goals") is not None
            and r.get("away_goals") is not None)


def _recompute_elo():
    """Recalcula el ELO desde el base aplicando cada resultado terminado."""
    elo = _base_elo()
    finished = [r for r in _results if _finished(r)]
    finished.sort(key=lambda r: (r.get("date") or "", r.get("home", "")))
    for r in finished:
        h, a = r["home"], r["away"]
        if h not in elo or a not in elo:
            continue
        hg, ag = r["home_goals"], r["away_goals"]
        if hg > ag:
            res_h = 1.0
        elif hg < ag:
            res_h = 0.0
        else:
            res_h = 0.5
        gd = abs(hg - ag)
        stage = r.get("stage", "group")
        k = _K_BY_STAGE.get(stage, 50.0)
        # Ventaja de localía solo si el local es anfitrión en fase de grupos.
        home_adv = (elo_mod.DEFAULT_HOME_ADVANTAGE
                    if (h in HOSTS and stage == "group") else 0.0)
        new_h = elo_mod.update_rating(elo[h], elo[a], res_h, k=k,
                                      goal_diff=gd, home_advantage=home_adv)
        new_a = elo_mod.update_rating(elo[a], elo[h], 1.0 - res_h, k=k,
                                      goal_diff=gd, home_advantage=-home_adv)
        elo[h], elo[a] = new_h, new_a
    return elo


def set_results(results: list, source: str, updated: str):
    """Guarda los resultados normalizados y recalcula el estado."""
    global _results, _elo, _last_updated, _source
    with _lock:
        _results = results or []
        _elo = _recompute_elo()
        _source = source
        _last_updated = updated


def current_elo(name: str) -> float:
    return _elo.get(name, TEAM_DATA.get(name, {}).get("elo", 1500))


def team(name: str) -> dict:
    """Equipo con el ELO ACTUAL (forma real del torneo)."""
    base = dict(data.TEAMS[name])
    base["elo"] = round(current_elo(name), 1)
    base["base_elo"] = TEAM_DATA[name]["elo"]
    return base


def has_live_data() -> bool:
    return bool(_results)


def status() -> dict:
    played = [r for r in _results if _finished(r)]
    return {
        "last_updated": _last_updated,
        "source": _source,
        "total_results": len(_results),
        "played": len(played),
        "has_live_data": has_live_data(),
        "elo_changes": _elo_changes(),
    }


def _elo_changes() -> list:
    """Mayores movimientos de ELO respecto al base (top 8 por |delta|)."""
    if not _elo:
        return []
    changes = []
    for name, e in _elo.items():
        base = TEAM_DATA[name]["elo"]
        d = e - base
        if abs(d) >= 1:
            changes.append({"team": name, "elo": round(e, 1),
                            "base": base, "delta": round(d, 1)})
    changes.sort(key=lambda c: abs(c["delta"]), reverse=True)
    return changes[:8]


def results() -> list:
    return list(_results)


def group_standings() -> dict:
    """Clasificación real de cada grupo según los partidos ya jugados."""
    tables = {}
    for gname, names in GROUP_DRAW.items():
        rows = {n: {"team": n, "played": 0, "w": 0, "d": 0, "l": 0,
                    "gf": 0, "ga": 0, "gd": 0, "pts": 0} for n in names}
        group_set = set(names)
        for r in _results:
            if not _finished(r):
                continue
            h, a = r["home"], r["away"]
            if h not in group_set or a not in group_set:
                continue
            hg, ag = r["home_goals"], r["away_goals"]
            rh, ra = rows[h], rows[a]
            rh["played"] += 1; ra["played"] += 1
            rh["gf"] += hg; rh["ga"] += ag
            ra["gf"] += ag; ra["ga"] += hg
            if hg > ag:
                rh["w"] += 1; rh["pts"] += 3; ra["l"] += 1
            elif hg < ag:
                ra["w"] += 1; ra["pts"] += 3; rh["l"] += 1
            else:
                rh["d"] += 1; ra["d"] += 1; rh["pts"] += 1; ra["pts"] += 1
        for row in rows.values():
            row["gd"] = row["gf"] - row["ga"]
        ranked = sorted(rows.values(),
                        key=lambda x: (x["pts"], x["gd"], x["gf"]), reverse=True)
        tables[gname] = ranked
    return tables

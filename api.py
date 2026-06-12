"""Capa de aplicación: une el motor de predicción con los datos del Mundial
2026 y expone funciones de alto nivel que consume el servidor web."""

from __future__ import annotations

from engine import match_model, monte_carlo, value
import data
from live import state as live_state, refresh as live_refresh


# Cache de la simulación Monte Carlo (es lo más costoso).
_sim_cache: dict = {}


def _team(name: str) -> dict | None:
    """Equipo con el ELO ACTUAL (en vivo si hay datos del torneo, base si no)."""
    if name not in data.TEAMS:
        return None
    if live_state.has_live_data():
        return live_state.team(name)
    return data.TEAMS[name]


def _live_groups() -> dict:
    """Grupos con el ELO en vivo, para la simulación Monte Carlo."""
    if not live_state.has_live_data():
        return data.GROUPS
    return {g: [live_state.team(t["name"]) for t in teams]
            for g, teams in data.GROUPS.items()}


def list_teams() -> list[dict]:
    out = []
    for gname, teams in data.GROUPS.items():
        for t in teams:
            live = _team(t["name"])
            out.append({
                "name": t["name"],
                "code": t.get("code", ""),
                "group": gname,
                "elo": live["elo"],
                "base_elo": t["elo"],
                "fifa_rank": t.get("fifa_rank"),
                "confederation": t.get("confederation", ""),
                "is_host": t["name"] in data.HOSTS,
            })
    out.sort(key=lambda x: x["elo"], reverse=True)
    return out


def list_groups() -> dict:
    result = {}
    for gname, teams in data.GROUPS.items():
        result[gname] = [{
            "name": t["name"], "code": t.get("code", ""), "elo": _team(t["name"])["elo"],
            "fifa_rank": t.get("fifa_rank"), "is_host": t["name"] in data.HOSTS,
        } for t in teams]
    return result


def get_team(name: str) -> dict | None:
    return _team(name)


def predict(home_name: str, away_name: str, stage: str = "group") -> dict | None:
    home = _team(home_name)
    away = _team(away_name)
    if not home or not away:
        return None
    host = home_name in data.HOSTS and stage == "group"
    return match_model.predict_match(home, away, home_is_host=host, stage=stage)


def group_stage_predictions() -> dict:
    """Predicción de los 72 partidos de fase de grupos (con ELO en vivo)."""
    result = {}
    for gname, teams in data.GROUPS.items():
        matches = []
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                a, b = _team(teams[i]["name"]), _team(teams[j]["name"])
                host = a["name"] in data.HOSTS
                pred = match_model.predict_match(a, b, home_is_host=host, stage="group")
                matches.append(pred)
        result[gname] = matches
    return result


def list_stadiums() -> list[dict]:
    return data.STADIUMS


def list_schedule() -> list[dict]:
    """Calendario con predicción incorporada cuando ambos equipos se conocen."""
    out = []
    for m in getattr(data, "SCHEDULE", []):
        entry = dict(m)
        h, a = m.get("home"), m.get("away")
        if h in data.TEAMS and a in data.TEAMS:
            host = h in data.HOSTS and m.get("stage", "group") == "group"
            entry["prediction"] = match_model.predict_match(
                data.TEAMS[h], data.TEAMS[a],
                home_is_host=host, stage=m.get("stage", "group"))
        out.append(entry)
    return out


def match_markets(home_name: str, away_name: str, stage: str = "group") -> dict | None:
    """Mercados de un partido con la probabilidad del MODELO y su cuota justa,
    listos para comparar contra la cuota de una casa de apuestas."""
    pred = predict(home_name, away_name, stage)
    if pred is None:
        return None
    r = pred["result_1x2"]
    g = pred["goals_markets"]
    dc = pred["double_chance"]
    cs = pred["clean_sheet"]
    markets = [
        {"key": "home_win", "label": f"Gana {home_name}", "model_prob": r["home_win"]},
        {"key": "draw", "label": "Empate", "model_prob": r["draw"]},
        {"key": "away_win", "label": f"Gana {away_name}", "model_prob": r["away_win"]},
        {"key": "dc_1x", "label": f"Doble: {home_name} o empate (1X)", "model_prob": dc["1X"]},
        {"key": "dc_x2", "label": f"Doble: empate o {away_name} (X2)", "model_prob": dc["X2"]},
        {"key": "over_2_5", "label": "Más de 2.5 goles", "model_prob": g["over_2_5"]},
        {"key": "under_2_5", "label": "Menos de 2.5 goles", "model_prob": g["under_2_5"]},
        {"key": "over_1_5", "label": "Más de 1.5 goles", "model_prob": g["over_1_5"]},
        {"key": "btts_yes", "label": "Ambos anotan: Sí", "model_prob": g["btts_yes"]},
        {"key": "btts_no", "label": "Ambos anotan: No", "model_prob": g["btts_no"]},
        {"key": "cs_home", "label": f"{home_name} deja portería a cero", "model_prob": cs["home"]},
        {"key": "cs_away", "label": f"{away_name} deja portería a cero", "model_prob": cs["away"]},
    ]
    for m in markets:
        m["model_prob"] = round(m["model_prob"], 4)
        m["fair_odds"] = round(1.0 / m["model_prob"], 2) if m["model_prob"] > 0 else None
    return {
        "home_team": home_name, "away_team": away_name, "stage": stage,
        "markets": markets,
    }


def analyze_value(bets: list, kelly_multiplier: float = 0.25) -> list:
    """Analiza una lista de apuestas {model_prob, book_odds, label?}."""
    out = []
    for b in bets:
        a = value.analyze(b["model_prob"], b["book_odds"], kelly_multiplier)
        a["label"] = b.get("label", "")
        a["market"] = b.get("market", "")
        out.append(a)
    return out


def simulate_portfolio(bets: list, start: float, target: float,
                       kelly_multiplier: float = 0.25, n: int = 10000) -> dict:
    """Simula la evolución de la banca apostando las apuestas de valor dadas."""
    clean = [{"model_prob": b["model_prob"], "book_odds": b["book_odds"]} for b in bets]
    return value.simulate_bankroll(clean, start, target, kelly_multiplier, n)


def simulate(n: int = 10000) -> dict:
    if n in _sim_cache:
        return _sim_cache[n]
    res = monte_carlo.run_simulations(
        _live_groups(), data.BRACKET_TEMPLATE, n=n, hosts=data.HOSTS)
    _sim_cache[n] = res
    return res


# ---------------------------------------------------------------------------
# Modo en vivo: actualización, escáner de valor y recomendaciones
# ---------------------------------------------------------------------------
def refresh_live() -> dict:
    """Obtiene resultados/cuotas frescos y recalcula todo. Invalida caches."""
    summary = live_refresh.refresh()
    _sim_cache.clear()
    return summary


def live_status() -> dict:
    s = live_state.status()
    s["summary"] = live_refresh.last_summary()
    return s


def live_standings() -> dict:
    return live_state.group_standings()


def live_results() -> list:
    return live_state.results()


# Edge (vs mercado sin margen) por encima del cual la discrepancia se considera
# descalibración del modelo, no valor fiable. El value betting real es de 2-12%.
PLAUSIBLE_EDGE_MAX = 0.12


def _devig_market_probs(odds: dict) -> dict:
    """Probabilidades 'justas' del mercado (sin margen) por mercado del modelo."""
    out = {}
    h, d, a = odds.get("home"), odds.get("draw"), odds.get("away")
    if h and d and a:
        ph, pd, pa = value.devig([h, d, a])
        out["home_win"], out["draw"], out["away_win"] = ph, pd, pa
    ov, un = odds.get("over"), odds.get("under")
    if ov and un:
        po, pu = value.devig([ov, un])
        out["over_2_5"], out["under_2_5"] = po, pu
    return out


def value_scan(kelly_multiplier: float = 0.25) -> dict:
    """Escanea TODOS los partidos próximos con cuotas reales. Compara la
    probabilidad del modelo con la del mercado SIN margen (de-vig) y clasifica
    cada apuesta de valor por fiabilidad según el tamaño del edge."""
    plausible, high = [], []
    scanned = 0
    for m in live_state.results():
        if m["status"] == "finished":
            continue
        odds = m.get("odds")
        if not odds:
            continue
        scanned += 1
        mk = match_markets(m["home"], m["away"], m.get("stage", "group"))
        if not mk:
            continue
        probs = {x["key"]: x["model_prob"] for x in mk["markets"]}
        labels = {x["key"]: x["label"] for x in mk["markets"]}
        market_fair = _devig_market_probs(odds)
        odds_for_market = {"home_win": odds.get("home"), "draw": odds.get("draw"),
                           "away_win": odds.get("away"), "over_2_5": odds.get("over"),
                           "under_2_5": odds.get("under")}
        for market_key, book in odds_for_market.items():
            p = probs.get(market_key)
            fair = market_fair.get(market_key)
            if not book or book <= 1.0 or p is None or fair is None:
                continue
            ev = p * book - 1.0
            if ev <= 0:
                continue
            edge = p - fair          # vs mercado sin margen
            a = value.analyze(p, book, kelly_multiplier)
            a.update({
                "match": f'{m["home"]} vs {m["away"]}',
                "home": m["home"], "away": m["away"],
                "stage": m.get("stage", "group"), "date": m.get("date"),
                "market": market_key, "label": labels.get(market_key, market_key),
                "market_prob": round(fair, 4), "edge": round(edge, 4),
                "provider": odds.get("provider", ""),
            })
            if 0 < edge <= PLAUSIBLE_EDGE_MAX:
                a["reliability"] = "plausible"
                plausible.append(a)
            else:
                a["reliability"] = "alto"   # discrepancia grande: poco fiable
                high.append(a)
    plausible.sort(key=lambda x: x["edge"], reverse=True)
    high.sort(key=lambda x: x["edge"], reverse=True)
    return {
        "scanned_matches": scanned,
        "has_odds": scanned > 0,
        "source": live_refresh.last_summary().get("source_odds", "—"),
        "plausible": plausible,
        "high_discrepancy": high,
        "count_plausible": len(plausible),
        "count_high": len(high),
    }


def recommendations(top: int = 12) -> dict:
    """Apuestas recomendadas del torneo.

    - Si hay cuotas reales: las de mayor valor esperado (EV+).
    - Si no hay cuotas: los 'picks' de mayor convicción del modelo
      (resultados más probables de los próximos partidos), marcados como tales.
    """
    scan = value_scan()
    if scan["has_odds"] and scan["plausible"]:
        from datetime import datetime
        bets = scan["plausible"]
        # Ordena de la más próxima a la más lejana (por fecha de inicio).
        bets_by_date = sorted(bets, key=lambda b: b.get("date") or "9999")
        today = datetime.now().date().isoformat()

        # Recomendada de hoy: mejor edge entre los partidos de hoy.
        todays = [b for b in bets if (b.get("date") or "")[:10] == today]
        if todays:
            todays.sort(key=lambda b: b["edge"], reverse=True)
            today_pick = {"when": "hoy", "matches_today": len(set(b["match"] for b in todays)),
                          "bet": todays[0]}
        elif bets_by_date:
            today_pick = {"when": "proxima", "matches_today": 0,
                          "bet": bets_by_date[0]}
        else:
            today_pick = {"when": "ninguna", "matches_today": 0, "bet": None}

        return {"mode": "value", "source": scan["source"],
                "bets": bets_by_date[:top],
                "today": today_pick,
                "note": "Ordenadas de la más próxima a la más lejana. Edge "
                        "plausible (2-12%) vs el mercado sin margen. Las de "
                        "discrepancia alta NO se recomiendan (descalibración)."}

    # Sin cuotas -> picks del modelo por convicción.
    picks = []
    for m in live_state.results() if live_state.has_live_data() else []:
        if m["status"] == "finished":
            continue
        mk = match_markets(m["home"], m["away"], m.get("stage", "group"))
        if not mk:
            continue
        best = max(mk["markets"], key=lambda x: x["model_prob"])
        picks.append({
            "match": f'{m["home"]} vs {m["away"]}',
            "label": best["label"], "model_prob": best["model_prob"],
            "fair_odds": best["fair_odds"], "date": m.get("date"),
            "stage": m.get("stage", "group"),
        })
    # Si aún no hay datos en vivo, usa el calendario base de fase de grupos.
    if not picks:
        for m in data.SCHEDULE:
            mk = match_markets(m["home"], m["away"], "group")
            if not mk:
                continue
            best = max(mk["markets"], key=lambda x: x["model_prob"])
            picks.append({
                "match": f'{m["home"]} vs {m["away"]}',
                "label": best["label"], "model_prob": best["model_prob"],
                "fair_odds": best["fair_odds"],
                "matchday": m.get("matchday"), "group": m.get("group"),
                "stage": "group",
            })
    picks.sort(key=lambda x: x["model_prob"], reverse=True)
    return {"mode": "picks", "source": "modelo", "bets": picks[:top]}

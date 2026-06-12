"""Fuentes de datos en vivo (resultados y cuotas reales).

Prioridad y estrategia:
  - RESULTADOS:
      1. football-data.org (si hay FOOTBALL_DATA_KEY)  -> robusto.
      2. ESPN API pública (sin clave)                  -> respaldo que SIEMPRE
         funciona y además trae cuotas gratis (DraftKings).
  - CUOTAS:
      1. The Odds API (si hay ODDS_API_KEY)            -> mejor cobertura.
      2. Las que vengan embebidas en ESPN              -> gratis, sin clave.

Solo usa urllib de la librería estándar (cero dependencias).
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from datetime import date, timedelta, datetime, timezone

import config
import data
from data.teams import GROUP_DRAW

USER_AGENT = "WC2026-Predictor/1.0 (academic project)"
TOURNAMENT_START = date(2026, 6, 11)
TOURNAMENT_END = date(2026, 7, 19)

_TEAM_TO_GROUP = {t: g for g, names in GROUP_DRAW.items() for t in names}

_STAGE_FROM_SLUG = {
    "group-stage": "group", "round-of-32": "r32", "round-of-16": "r16",
    "quarterfinals": "qf", "semifinals": "sf", "3rd-place": "sf",
    "final": "final",
}


def _http_get(url: str, headers: dict | None = None, timeout: int = 12) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError,
            json.JSONDecodeError):
        return None


# ----------------------------------------------------------------------------
# Conversión de cuotas
# ----------------------------------------------------------------------------
def american_to_decimal(american) -> float | None:
    """Convierte cuota americana (-125, +390) a decimal (2.10, 4.90)."""
    try:
        a = float(american)
    except (TypeError, ValueError):
        return None
    if a == 0:
        return None
    if a > 0:
        return round(1.0 + a / 100.0, 3)
    return round(1.0 + 100.0 / abs(a), 3)


def _find_number(obj):
    """Busca recursivamente el primer valor numérico 'de cuota' en un dict
    anidado de ESPN (open/close -> odds/american/value/moneyLine)."""
    if obj is None:
        return None
    if isinstance(obj, (int, float)):
        return obj
    if isinstance(obj, str):
        try:
            return float(obj.replace("+", ""))
        except ValueError:
            return None
    if isinstance(obj, dict):
        # Prioriza 'close' sobre 'open', y claves de precio conocidas.
        for key in ("close", "current"):
            if key in obj:
                v = _find_number(obj[key])
                if v is not None:
                    return v
        for key in ("odds", "american", "moneyLine", "value", "open"):
            if key in obj:
                v = _find_number(obj[key])
                if v is not None:
                    return v
    return None


# ----------------------------------------------------------------------------
# ESPN (sin clave) — resultados + cuotas
# ----------------------------------------------------------------------------
def _espn_parse_event(event: dict) -> dict | None:
    try:
        comp = event["competitions"][0]
        competitors = comp["competitors"]
    except (KeyError, IndexError, TypeError):
        return None

    home = away = None
    hg = ag = None
    for c in competitors:
        name = config.canonical_team(
            (c.get("team") or {}).get("displayName") or (c.get("team") or {}).get("name"))
        if name not in data.TEAMS:
            return None
        score = c.get("score")
        try:
            goals = int(score) if score not in (None, "", "-") else None
        except (ValueError, TypeError):
            goals = None
        if c.get("homeAway") == "home":
            home, hg = name, goals
        else:
            away, ag = name, goals
    if not home or not away:
        return None

    st = ((comp.get("status") or {}).get("type") or {}).get("state", "pre")
    status = {"pre": "scheduled", "in": "in_progress", "post": "finished"}.get(st, "scheduled")
    if status != "finished":
        hg = ag = None

    slug = (event.get("season") or {}).get("slug", "group-stage")
    stage = _STAGE_FROM_SLUG.get(slug, "group")
    group = _TEAM_TO_GROUP.get(home) if stage == "group" else None

    odds = _espn_parse_odds(comp)

    return {
        "espn_id": event.get("id"),
        "date": event.get("date"),
        "home": home, "away": away,
        "home_goals": hg, "away_goals": ag,
        "status": status, "stage": stage, "group": group,
        "odds": odds,
    }


def _espn_parse_odds(comp: dict) -> dict | None:
    raw_list = comp.get("odds") or []
    raw = next((o for o in raw_list if o), None)
    if not raw:
        return None
    ml = raw.get("moneyline") or {}
    home = american_to_decimal(_find_number(ml.get("home")))
    away = american_to_decimal(_find_number(ml.get("away")))
    draw = american_to_decimal(_find_number(ml.get("draw")
                                            or (raw.get("drawOdds") or {}).get("moneyLine")))
    total = raw.get("total") or {}
    over = american_to_decimal(_find_number(total.get("over")))
    under = american_to_decimal(_find_number(total.get("under")))
    line = raw.get("overUnder")
    out = {"home": home, "draw": draw, "away": away,
           "over": over, "under": under, "line": line,
           "provider": (raw.get("provider") or {}).get("name", "ESPN")}
    if not any(v for k, v in out.items() if k in ("home", "draw", "away", "over", "under")):
        return None
    return out


def fetch_espn(today: date | None = None) -> list:
    """Recorre los días del torneo (desde el inicio hasta hoy+8) y devuelve los
    partidos normalizados con resultados y cuotas embebidas."""
    today = today or datetime.now(timezone.utc).date()
    start = TOURNAMENT_START
    end = min(TOURNAMENT_END, today + timedelta(days=8))
    matches = {}
    d = start
    while d <= end:
        ymd = d.strftime("%Y%m%d")
        url = (f"https://site.api.espn.com/apis/site/v2/sports/soccer/"
               f"{config.ESPN_LEAGUE}/scoreboard?dates={ymd}")
        payload = _http_get(url)
        if payload and isinstance(payload, dict):
            for ev in payload.get("events", []):
                m = _espn_parse_event(ev)
                if m:
                    matches[m["espn_id"] or f'{m["home"]}-{m["away"]}'] = m
        d += timedelta(days=1)
    return list(matches.values())


# ----------------------------------------------------------------------------
# football-data.org (con clave) — resultados
# ----------------------------------------------------------------------------
def fetch_football_data() -> list | None:
    if not config.FOOTBALL_DATA_KEY:
        return None
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    payload = _http_get(url, headers={"X-Auth-Token": config.FOOTBALL_DATA_KEY})
    if not payload or "matches" not in payload:
        return None
    out = []
    for m in payload["matches"]:
        home = config.canonical_team((m.get("homeTeam") or {}).get("name"))
        away = config.canonical_team((m.get("awayTeam") or {}).get("name"))
        if home not in data.TEAMS or away not in data.TEAMS:
            continue
        ft = (m.get("score") or {}).get("fullTime") or {}
        status_raw = m.get("status", "")
        status = "finished" if status_raw == "FINISHED" else (
            "in_progress" if status_raw in ("IN_PLAY", "PAUSED") else "scheduled")
        out.append({
            "espn_id": f'fd-{m.get("id")}',
            "date": m.get("utcDate"),
            "home": home, "away": away,
            "home_goals": ft.get("home") if status == "finished" else None,
            "away_goals": ft.get("away") if status == "finished" else None,
            "status": status,
            "stage": "group" if (m.get("stage") == "GROUP_STAGE") else "r32",
            "group": _TEAM_TO_GROUP.get(home),
            "odds": None,
        })
    return out


# ----------------------------------------------------------------------------
# The Odds API (con clave) — cuotas
# ----------------------------------------------------------------------------
def fetch_odds_api() -> dict | None:
    """Devuelve {(home, away): odds_dict}. None si no hay clave o falla."""
    if not config.ODDS_API_KEY:
        return None
    url = (f"https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/"
           f"?apiKey={config.ODDS_API_KEY}&regions={config.ODDS_REGION}"
           f"&markets=h2h,totals&oddsFormat=decimal")
    payload = _http_get(url)
    if not payload or not isinstance(payload, list):
        return None
    result = {}
    for game in payload:
        home = config.canonical_team(game.get("home_team"))
        away = config.canonical_team(game.get("away_team"))
        if home not in data.TEAMS or away not in data.TEAMS:
            continue
        books = game.get("bookmakers") or []
        if not books:
            continue
        # Usa la mejor (más alta) cuota disponible entre casas para cada resultado.
        best = {"home": None, "draw": None, "away": None,
                "over": None, "under": None, "line": 2.5, "provider": "The Odds API (mejor)"}
        for bk in books:
            for mk in bk.get("markets", []):
                if mk["key"] == "h2h":
                    for oc in mk.get("outcomes", []):
                        nm = config.canonical_team(oc.get("name"))
                        price = oc.get("price")
                        slot = "home" if nm == home else ("away" if nm == away else "draw")
                        if price and (best[slot] is None or price > best[slot]):
                            best[slot] = price
                elif mk["key"] == "totals":
                    for oc in mk.get("outcomes", []):
                        if oc.get("point") == 2.5:
                            slot = "over" if oc.get("name") == "Over" else "under"
                            price = oc.get("price")
                            if price and (best[slot] is None or price > best[slot]):
                                best[slot] = price
        result[(home, away)] = best
    return result

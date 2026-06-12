"""Orquestador de actualización en vivo.

Elige la mejor fuente disponible para resultados y cuotas, fusiona todo,
adjunta las cuotas a cada partido y actualiza el estado del torneo.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import sources, state

_last_summary: dict = {"ok": False, "message": "sin actualizar todavía"}


def refresh() -> dict:
    """Obtiene datos frescos y recalcula el estado. Devuelve un resumen."""
    global _last_summary
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # --- Resultados ---
    results = sources.fetch_football_data()
    src_results = "football-data.org"
    if not results:
        results = sources.fetch_espn()
        src_results = "ESPN (público)"
    if results is None:
        results = []
        src_results = "—"

    # --- Cuotas ---
    odds_map = sources.fetch_odds_api()
    src_odds = "The Odds API"
    if not odds_map:
        # Usa las cuotas embebidas de ESPN (ya vienen en cada partido).
        odds_map = {(m["home"], m["away"]): m["odds"]
                    for m in results if m.get("odds")}
        src_odds = "ESPN/DraftKings" if odds_map else "—"

    # Adjunta cuotas a cada partido (sobrescribe con la mejor fuente).
    n_odds = 0
    for m in results:
        key = (m["home"], m["away"])
        if key in odds_map and odds_map[key]:
            m["odds"] = odds_map[key]
        if m.get("odds"):
            n_odds += 1

    state.set_results(results, source=f"{src_results} + {src_odds}", updated=now)

    played = sum(1 for m in results if m["status"] == "finished")
    _last_summary = {
        "ok": True,
        "updated": now,
        "source_results": src_results,
        "source_odds": src_odds,
        "total_matches": len(results),
        "played": played,
        "with_odds": n_odds,
    }
    return _last_summary


def last_summary() -> dict:
    return _last_summary

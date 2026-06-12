# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from live import sources, state
import api, data

# 1) Conversión de cuotas americanas -> decimal
assert abs(sources.american_to_decimal(-125) - 1.8) < 0.01
assert abs(sources.american_to_decimal(+390) - 4.9) < 0.01
print("1) Cuotas americanas->decimal OK")

# 2) Parser ESPN con un evento sintético (forma real verificada)
event = {
    "id": "760416", "date": "2026-06-12T19:00Z",
    "season": {"slug": "group-stage"},
    "competitions": [{
        "status": {"type": {"state": "post"}},
        "competitors": [
            {"homeAway": "home", "score": "2", "team": {"displayName": "Mexico"}},
            {"homeAway": "away", "score": "0", "team": {"displayName": "South Africa"}},
        ],
        "odds": [{
            "provider": {"name": "DraftKings"},
            "overUnder": 2.5,
            "moneyline": {"home": {"close": {"odds": -300}},
                          "away": {"close": {"odds": +700}},
                          "draw": {"close": {"odds": +400}}},
            "total": {"over": {"close": {"odds": -110}},
                      "under": {"close": {"odds": -110}}},
        }],
    }],
}
m = sources._espn_parse_event(event)
print("2) Parser ESPN:", m["home"], m["home_goals"], "-", m["away_goals"], m["away"],
      "| status", m["status"], "| grupo", m["group"], "| odds home", m["odds"]["home"])
assert m["home"] == "Mexico" and m["home_goals"] == 2 and m["status"] == "finished"
assert m["group"] == "A"

# 3) Recalcular ELO + standings con resultados sintéticos
base_mex = data.TEAM_DATA["Mexico"]["elo"]
results = [
    {"home": "Mexico", "away": "South Africa", "home_goals": 2, "away_goals": 0,
     "status": "finished", "stage": "group", "group": "A", "date": "2026-06-11T19:00Z", "odds": None},
    {"home": "South Korea", "away": "Czechia", "home_goals": 1, "away_goals": 1,
     "status": "finished", "stage": "group", "group": "A", "date": "2026-06-12T19:00Z", "odds": None},
    # Próximo partido con cuotas de valor (cuota muy alta para el favorito)
    {"home": "Mexico", "away": "Czechia", "home_goals": None, "away_goals": None,
     "status": "scheduled", "stage": "group", "group": "A", "date": "2026-06-18T19:00Z",
     "odds": {"home": 3.5, "draw": 4.0, "away": 5.0, "over": 1.9, "under": 1.9, "line": 2.5, "provider": "Test"}},
]
state.set_results(results, "test", "2026-06-12 20:00 UTC")
print("3) ELO Mexico base", base_mex, "-> live", round(state.current_elo("Mexico"), 1),
      "(debe subir tras ganar)")
assert state.current_elo("Mexico") > base_mex

st = state.group_standings()["A"]
print("   Standings A:", [(r["team"], r["pts"], r["gd"]) for r in st])
assert st[0]["team"] == "Mexico" and st[0]["pts"] == 3

# 4) Escáner de valor con de-vig y clasificación de fiabilidad
scan = api.value_scan()
print(f'4) Escaneados: {scan["scanned_matches"]} | plausibles: {scan["count_plausible"]} '
      f'| discrepancia alta: {scan["count_high"]}')
for b in (scan["plausible"] + scan["high_discrepancy"])[:5]:
    print(f"   [{b['reliability']:9}] {b['match']:20} {b['label']:18} "
          f"cuota={b['book_odds']} edge={b['edge']:+.1%} EV={b['ev']:+.1%}")
assert scan["scanned_matches"] >= 1

# 5) Recomendaciones
rec = api.recommendations(5)
print("5) Recomendaciones modo:", rec["mode"], "| n:", len(rec["bets"]))

# 6) Predicción usa ELO en vivo
p = api.predict("Mexico", "Czechia")
print("6) Mexico vs Czechia (ELO vivo) 1X2:", p["result_1x2"])

print("\nTODOS LOS CHECKS EN VIVO OK")

import data, api

print("Equipos:", len(data.TEAMS), "| ELO ref:", round(data.REFERENCE_ELO, 1))
print("Partidos de grupo:", len(data.SCHEDULE))

m = api.predict("Spain", "Uruguay")
print("\nSpain vs Uruguay:")
print("  xG:", m["expected_goals"])
print("  1X2:", m["result_1x2"])
print("  Over2.5:", m["goals_markets"]["over_2_5"], "BTTS:", m["goals_markets"]["btts_yes"])
print("  Marcadores:", m["most_likely_scores"][:3])
print("  Amarillas total:", m["cards"]["yellow_total"], "Prob roja:", m["cards"]["prob_any_red"])
print("  Goleadores ESP:", [(p["name"], p["prob_to_score"]) for p in m["players"]["home"]])

m2 = api.predict("Mexico", "South Africa")
print("\nMexico(anfitrion) vs South Africa 1X2:", m2["result_1x2"])

print("\nMonte Carlo 2000 sims (top 8 campeon):")
sim = api.simulate(2000)
for i, (name, p) in enumerate(list(sim["probabilities"].items())[:8], 1):
    print(f"  {i}. {name:16} campeon={p['champion']*100:5.1f}%  semis={p['sf']*100:5.1f}%  octavos={p['r16']*100:5.1f}%")

# Verificar que las probabilidades 1X2 suman 1
s = sum(m["result_1x2"].values())
print("\nSuma 1X2 (debe ser ~1.0):", round(s, 4))

# --- Análisis de valor (EV + Kelly) ---
from engine import value
print("\nAnálisis de valor:")
a_val = value.analyze(0.55, 2.10)   # modelo 55% vs cuota 2.10 (implícita 47.6%)
a_non = value.analyze(0.55, 1.70)   # modelo 55% vs cuota 1.70 (implícita 58.8%)
print(f"  Con valor: EV={a_val['ev']:+.3f} valor={a_val['is_value']} kelly={a_val['kelly_stake_fraction']}")
print(f"  Sin valor: EV={a_non['ev']:+.3f} valor={a_non['is_value']} kelly={a_non['kelly_stake_fraction']}")
assert a_val["is_value"] and not a_non["is_value"]

sim_bank = value.simulate_bankroll(
    [{"model_prob": 0.20, "book_odds": 5.5}, {"model_prob": 0.24, "book_odds": 4.2}],
    start_bankroll=50000, target=4000000, kelly_multiplier=0.5, n_sims=5000)
print(f"  Banca 50k->4M: mediana={sim_bank['median']:.0f} "
      f"prob_ganancia={sim_bank['prob_profit']:.1%} "
      f"prob_objetivo={sim_bank['prob_reach_target']:.2%}")
print("\nTodos los checks OK.")

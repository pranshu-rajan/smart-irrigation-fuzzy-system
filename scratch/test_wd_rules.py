"""Scratch test script to verify complete 100% coverage rule design for WaterDemandFIS."""

import sys
sys.path.insert(0, ".")
import numpy as np
import pandas as pd
from fuzzy_engine.universes import get_fuzzy_variable

etc_var = get_fuzzy_variable("etc")
def_var = get_fuzzy_variable("crop_water_deficit")
rain_var = get_fuzzy_variable("effective_rainfall")
demand_var = get_fuzzy_variable("water_demand")

RULES = [
    # =========================================================================
    # LAYER 1: HEAVY / TORRENTIAL RAINFALL RELIEF (P_eff is High or Very High)
    # Precipitation quenches immediate water demand.
    # =========================================================================
    {"id": 1, "antecedents": {"effective_rainfall": "very_high", "crop_water_deficit": ["none", "low"]}, "consequent": "very_low"},
    {"id": 2, "antecedents": {"effective_rainfall": "very_high", "crop_water_deficit": "moderate"}, "consequent": "low"},
    {"id": 3, "antecedents": {"effective_rainfall": "very_high", "crop_water_deficit": "high"}, "consequent": "moderate"},
    {"id": 4, "antecedents": {"effective_rainfall": "very_high", "crop_water_deficit": "very_high"}, "consequent": "moderate"},

    {"id": 5, "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "none"}, "consequent": "very_low"},
    {"id": 6, "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "low"}, "consequent": "low"},
    {"id": 7, "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "moderate"}, "consequent": "moderate"},
    {"id": 8, "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "high"}, "consequent": "moderate"},
    {"id": 9, "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "very_high"}, "consequent": "high"},

    # =========================================================================
    # LAYER 2: MODERATE RAINFALL REGIME (P_eff is Moderate)
    # Balanced rainfall providing partial demand reduction.
    # =========================================================================
    {"id": 10, "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "none"}, "consequent": "very_low"},
    {"id": 11, "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "low"}, "consequent": "low"},
    {"id": 12, "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "moderate"}, "consequent": "moderate"},
    {"id": 13, "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "high"}, "consequent": "high"},
    {"id": 14, "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "very_high"}, "consequent": "high"},

    # =========================================================================
    # LAYER 3: BASELINE ETC X DEFICIT KERNEL (P_eff is None or Low)
    # Comprehensive 25-rule matrix governing clear-sky / light shower conditions.
    # =========================================================================
    # ETc is Very Low (< 2.5 mm/day)
    {"id": 15, "antecedents": {"etc": "very_low", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]}, "consequent": "very_low"},
    {"id": 16, "antecedents": {"etc": "very_low", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]}, "consequent": "low"},
    {"id": 17, "antecedents": {"etc": "very_low", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]}, "consequent": "moderate"},
    {"id": 18, "antecedents": {"etc": "very_low", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]}, "consequent": "moderate"},
    {"id": 19, "antecedents": {"etc": "very_low", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]}, "consequent": "high"},

    # ETc is Low (1.5 - 5.5 mm/day)
    {"id": 20, "antecedents": {"etc": "low", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]}, "consequent": "very_low"},
    {"id": 21, "antecedents": {"etc": "low", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]}, "consequent": "low"},
    {"id": 22, "antecedents": {"etc": "low", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]}, "consequent": "moderate"},
    {"id": 23, "antecedents": {"etc": "low", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]}, "consequent": "high"},
    {"id": 24, "antecedents": {"etc": "low", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]}, "consequent": "high"},

    # ETc is Moderate (4.5 - 9.5 mm/day)
    {"id": 25, "antecedents": {"etc": "moderate", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]}, "consequent": "low"},
    {"id": 26, "antecedents": {"etc": "moderate", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]}, "consequent": "moderate"},
    {"id": 27, "antecedents": {"etc": "moderate", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]}, "consequent": "moderate"},
    {"id": 28, "antecedents": {"etc": "moderate", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]}, "consequent": "high"},
    {"id": 29, "antecedents": {"etc": "moderate", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]}, "consequent": "very_high"},

    # ETc is High (8.5 - 12.5 mm/day)
    {"id": 30, "antecedents": {"etc": "high", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]}, "consequent": "moderate"},
    {"id": 31, "antecedents": {"etc": "high", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]}, "consequent": "moderate"},
    {"id": 32, "antecedents": {"etc": "high", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]}, "consequent": "high"},
    {"id": 33, "antecedents": {"etc": "high", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]}, "consequent": "high"},
    {"id": 34, "antecedents": {"etc": "high", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]}, "consequent": "very_high"},

    # ETc is Very High (11.5 - 15.0 mm/day)
    {"id": 35, "antecedents": {"etc": "very_high", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]}, "consequent": "moderate"},
    {"id": 36, "antecedents": {"etc": "very_high", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]}, "consequent": "high"},
    {"id": 37, "antecedents": {"etc": "very_high", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]}, "consequent": "high"},
    {"id": 38, "antecedents": {"etc": "very_high", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]}, "consequent": "very_high"},
    {"id": 39, "antecedents": {"etc": "very_high", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]}, "consequent": "very_high"},
]

z_grid = np.linspace(demand_var.universe.min_val, demand_var.universe.max_val, 501)
output_mf_matrix = {name: mf.evaluate(z_grid) for name, mf in demand_var.sets.items()}

def evaluate_demand(etc: float, deficit: float, rain: float) -> float:
    mu_etc = etc_var.evaluate(etc, clamp=True)
    mu_def = def_var.evaluate(deficit, clamp=True)
    mu_rain = rain_var.evaluate(rain, clamp=True)

    memberships = {
        "etc": mu_etc,
        "crop_water_deficit": mu_def,
        "effective_rainfall": mu_rain,
    }

    consequent_activations = {name: 0.0 for name in demand_var.set_names}

    for rule in RULES:
        weights = []
        for v_name, term_or_terms in rule["antecedents"].items():
            v_mu = memberships[v_name]
            if isinstance(term_or_terms, list):
                w = max(v_mu[t] for t in term_or_terms)
            else:
                w = v_mu[term_or_terms]
            weights.append(w)

        firing_strength = min(weights) if weights else 0.0
        target = rule["consequent"]
        if firing_strength > consequent_activations[target]:
            consequent_activations[target] = float(firing_strength)

    # Implication & Aggregation
    agg_mu = np.zeros_like(z_grid)
    for term_name, beta in consequent_activations.items():
        if beta > 0.0:
            clipped = np.minimum(beta, output_mf_matrix[term_name])
            agg_mu = np.maximum(agg_mu, clipped)

    total_area = np.sum(agg_mu)
    if total_area < 1e-9:
        return 0.0

    return float(np.sum(z_grid * agg_mu) / total_area)

# Test sanity cases
c1 = evaluate_demand(etc=0.5, deficit=0.0, rain=25.0)  # Very Low Demand
c2 = evaluate_demand(etc=3.0, deficit=1.0, rain=10.0)  # Low Demand
c3 = evaluate_demand(etc=7.0, deficit=6.0, rain=2.0)   # Moderate Demand
c4 = evaluate_demand(etc=10.5, deficit=10.0, rain=0.0) # High Demand
c5 = evaluate_demand(etc=13.5, deficit=13.0, rain=0.0) # Very High Demand

print(f"Sanity Case 1 (Very Low): {c1:.2f}%")
print(f"Sanity Case 2 (Low):      {c2:.2f}%")
print(f"Sanity Case 3 (Moderate): {c3:.2f}%")
print(f"Sanity Case 4 (High):     {c4:.2f}%")
print(f"Sanity Case 5 (Extreme):  {c5:.2f}%")

# Test Rain mitigation
cm_dry = evaluate_demand(etc=8.0, deficit=7.0, rain=1.0)
cm_rain = evaluate_demand(etc=8.0, deficit=0.0, rain=15.0)
print(f"Rain Mitigation: Dry={cm_dry:.2f}% vs Rain={cm_rain:.2f}%, Delta={cm_rain - cm_dry:.2f}%")

# Test Grid Coverage (10,000 random points)
zero_area_count = 0
rng = np.random.default_rng(42)
for _ in range(10000):
    e = rng.uniform(0.0, 15.0)
    d = rng.uniform(0.0, 15.0)
    r = rng.uniform(0.0, 50.0)
    res = evaluate_demand(e, d, r)
    if res == 0.0:
        zero_area_count += 1
print(f"Zero-area occurrences in 10000 points: {zero_area_count}")

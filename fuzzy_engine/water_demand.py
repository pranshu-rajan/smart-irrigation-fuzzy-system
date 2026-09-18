"""
FIS 3: Water Demand Fuzzy Inference System.

Evaluates normalized crop water requirement [0.0, 100.0]% based on:
1. Crop Evapotranspiration (ETc): [0.0, 15.0] mm/day
   - Linguistic terms: Very Low, Low, Moderate, High, Very High
2. Crop Water Deficit (WD): [0.0, 15.0] mm/day
   - Physical definition: max(ETc - Effective_Rainfall, 0)
   - Linguistic terms: None, Low, Moderate, High, Very High
3. Effective Rainfall (P_eff): [0.0, 50.0] mm
   - Linguistic terms: None, Low, Moderate, High, Very High

Output:
1. Water Demand: [0.0, 100.0] %
   - Linguistic terms: Very Low, Low, Moderate, High, Very High

Inference Engine:
- Type: Mamdani Fuzzy Inference System
- AND operator: Minimum
- OR operator: Maximum
- Implication operator: Minimum (Mamdani min-truncation)
- Aggregation operator: Maximum
- Defuzzification: Centroid (Center of Gravity)
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from fuzzy_engine.universes import get_fuzzy_variable
from fuzzy_engine.variables import FuzzyVariable


class WaterDemandFIS:
    """
    Mamdani Fuzzy Inference System for Crop Water Demand.

    Parameters
    ----------
    resolution : int, optional
        Number of discrete points across the output universe [0, 100]% for centroid
        defuzzification. Default is 501 points (0.2% resolution).
    """

    # Comprehensive Hierarchical Engineering Rule Base (39 Rules):
    #
    # LAYER 1: HEAVY / TORRENTIAL RAINFALL MITIGATION (P_eff in {high, very_high})
    # When significant precipitation is received, immediate water demand is suppressed
    # regardless of atmospheric ETc demand, while deficit dominance is recognized if
    # legacy accumulated deficit is severe. (9 rules)
    #
    # LAYER 2: MODERATE RAINFALL REGIME (P_eff in {moderate})
    # Moderate rain satisfies modest deficits but provides only partial relief against
    # elevated crop water deficits. (5 rules)
    #
    # LAYER 3: DRY / MINIMAL RAIN BASELINE KERNEL (P_eff in {none, low})
    # Complete 5x5 Cartesian product of ETc and Deficit ensuring full coverage across
    # all transpirational and deficit regimes when rainfall is absent or negligible. (25 rules)
    RULES: List[Dict[str, Any]] = [
        # =========================================================================
        # LAYER 1: HEAVY / TORRENTIAL RAINFALL MITIGATION (9 Rules)
        # =========================================================================
        {
            "id": 1,
            "antecedents": {"effective_rainfall": "very_high", "crop_water_deficit": "none"},
            "consequent": "very_low",
            "desc": "Torrential rain and zero deficit eliminate water demand",
        },
        {
            "id": 2,
            "antecedents": {"effective_rainfall": "very_high", "crop_water_deficit": ["low", "moderate"]},
            "consequent": "very_low",
            "desc": "Torrential rain replenishes modest deficits",
        },
        {
            "id": 3,
            "antecedents": {"effective_rainfall": "very_high", "crop_water_deficit": "high"},
            "consequent": "low",
            "desc": "Torrential rain substantially mitigates high deficit",
        },
        {
            "id": 4,
            "antecedents": {"effective_rainfall": "very_high", "crop_water_deficit": "very_high"},
            "consequent": "moderate",
            "desc": "Torrential rain tempers extreme deficit",
        },
        {
            "id": 5,
            "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "none"},
            "consequent": "very_low",
            "desc": "Substantial rainfall with no deficit keeps demand very low",
        },
        {
            "id": 6,
            "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "low"},
            "consequent": "low",
            "desc": "Substantial rainfall easily meets low deficit",
        },
        {
            "id": 7,
            "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "moderate"},
            "consequent": "low",
            "desc": "Substantial rainfall overcomes moderate deficit",
        },
        {
            "id": 8,
            "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "high"},
            "consequent": "moderate",
            "desc": "Substantial rainfall leaves residual demand under high deficit",
        },
        {
            "id": 9,
            "antecedents": {"effective_rainfall": "high", "crop_water_deficit": "very_high"},
            "consequent": "high",
            "desc": "Severe deficit partially alleviated by high rain",
        },

        # =========================================================================
        # LAYER 2: MODERATE RAINFALL REGIME (5 Rules)
        # =========================================================================
        {
            "id": 10,
            "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "none"},
            "consequent": "very_low",
            "desc": "Moderate rain with no deficit maintains very low demand",
        },
        {
            "id": 11,
            "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "low"},
            "consequent": "low",
            "desc": "Moderate rain neutralizes low deficit",
        },
        {
            "id": 12,
            "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "moderate"},
            "consequent": "moderate",
            "desc": "Moderate rain balances moderate deficit",
        },
        {
            "id": 13,
            "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "high"},
            "consequent": "high",
            "desc": "Moderate rain cannot satisfy high deficit",
        },
        {
            "id": 14,
            "antecedents": {"effective_rainfall": "moderate", "crop_water_deficit": "very_high"},
            "consequent": "very_high",
            "desc": "Severe deficit dominates moderate rainfall",
        },

        # =========================================================================
        # LAYER 3: DRY / MINIMAL RAINFALL BASELINE KERNEL (25 Rules)
        # Active when effective rainfall is negligible (none or low).
        # =========================================================================
        # ETc: Very Low
        {
            "id": 15,
            "antecedents": {"etc": "very_low", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]},
            "consequent": "very_low",
            "desc": "Negligible ETc and no deficit indicate zero water demand",
        },
        {
            "id": 16,
            "antecedents": {"etc": "very_low", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]},
            "consequent": "low",
            "desc": "Negligible ETc with slight deficit",
        },
        {
            "id": 17,
            "antecedents": {"etc": "very_low", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]},
            "consequent": "moderate",
            "desc": "Low ETc with moderate deficit",
        },
        {
            "id": 18,
            "antecedents": {"etc": "very_low", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]},
            "consequent": "high",
            "desc": "Low ETc with high deficit",
        },
        {
            "id": 19,
            "antecedents": {"etc": "very_low", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]},
            "consequent": "very_high",
            "desc": "Severe deficit dominates even with low ETc",
        },

        # ETc: Low
        {
            "id": 20,
            "antecedents": {"etc": "low", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]},
            "consequent": "very_low",
            "desc": "Low ETc and zero deficit",
        },
        {
            "id": 21,
            "antecedents": {"etc": "low", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]},
            "consequent": "low",
            "desc": "Low ETc with low deficit",
        },
        {
            "id": 22,
            "antecedents": {"etc": "low", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]},
            "consequent": "moderate",
            "desc": "Low ETc with moderate deficit",
        },
        {
            "id": 23,
            "antecedents": {"etc": "low", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]},
            "consequent": "high",
            "desc": "Low ETc with high deficit",
        },
        {
            "id": 24,
            "antecedents": {"etc": "low", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]},
            "consequent": "very_high",
            "desc": "Low ETc with severe deficit",
        },

        # ETc: Moderate
        {
            "id": 25,
            "antecedents": {"etc": "moderate", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]},
            "consequent": "low",
            "desc": "Moderate ETc with zero deficit",
        },
        {
            "id": 26,
            "antecedents": {"etc": "moderate", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]},
            "consequent": "moderate",
            "desc": "Moderate ETc with low deficit",
        },
        {
            "id": 27,
            "antecedents": {"etc": "moderate", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]},
            "consequent": "moderate",
            "desc": "Moderate ETc with moderate deficit",
        },
        {
            "id": 28,
            "antecedents": {"etc": "moderate", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]},
            "consequent": "high",
            "desc": "Moderate ETc with high deficit",
        },
        {
            "id": 29,
            "antecedents": {"etc": "moderate", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]},
            "consequent": "very_high",
            "desc": "Moderate ETc with severe deficit",
        },

        # ETc: High
        {
            "id": 30,
            "antecedents": {"etc": "high", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]},
            "consequent": "moderate",
            "desc": "High ETc with zero deficit maintains moderate demand",
        },
        {
            "id": 31,
            "antecedents": {"etc": "high", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]},
            "consequent": "moderate",
            "desc": "High ETc with low deficit",
        },
        {
            "id": 32,
            "antecedents": {"etc": "high", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]},
            "consequent": "high",
            "desc": "High ETc with moderate deficit",
        },
        {
            "id": 33,
            "antecedents": {"etc": "high", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]},
            "consequent": "high",
            "desc": "High ETc with high deficit produces high demand",
        },
        {
            "id": 34,
            "antecedents": {"etc": "high", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]},
            "consequent": "very_high",
            "desc": "High ETc with severe deficit",
        },

        # ETc: Very High
        {
            "id": 35,
            "antecedents": {"etc": "very_high", "crop_water_deficit": "none", "effective_rainfall": ["none", "low"]},
            "consequent": "moderate",
            "desc": "Very high ETc with zero deficit maintains moderate demand",
        },
        {
            "id": 36,
            "antecedents": {"etc": "very_high", "crop_water_deficit": "low", "effective_rainfall": ["none", "low"]},
            "consequent": "high",
            "desc": "Very high ETc with low deficit drives high demand",
        },
        {
            "id": 37,
            "antecedents": {"etc": "very_high", "crop_water_deficit": "moderate", "effective_rainfall": ["none", "low"]},
            "consequent": "high",
            "desc": "Very high ETc with moderate deficit",
        },
        {
            "id": 38,
            "antecedents": {"etc": "very_high", "crop_water_deficit": "high", "effective_rainfall": ["none", "low"]},
            "consequent": "very_high",
            "desc": "Very high ETc with high deficit drives very high demand",
        },
        {
            "id": 39,
            "antecedents": {"etc": "very_high", "crop_water_deficit": "very_high", "effective_rainfall": ["none", "low"]},
            "consequent": "very_high",
            "desc": "Very high ETc with extreme deficit creates maximum demand",
        },
    ]

    def __init__(self, resolution: int = 501) -> None:
        # Bind variables from the centralized global registry
        self.etc_var: FuzzyVariable = get_fuzzy_variable("etc")
        self.deficit_var: FuzzyVariable = get_fuzzy_variable("crop_water_deficit")
        self.rainfall_var: FuzzyVariable = get_fuzzy_variable("effective_rainfall")
        self.demand_var: FuzzyVariable = get_fuzzy_variable("water_demand")

        self.resolution = resolution
        # Output evaluation grid for centroid integration [0.0, 100.0]%
        self.z_grid = np.linspace(
            self.demand_var.universe.min_val,
            self.demand_var.universe.max_val,
            self.resolution,
        )

        # Pre-evaluate the output membership functions over z_grid
        self._output_mf_matrix: Dict[str, np.ndarray] = {
            name: mf_set.evaluate(self.z_grid)
            for name, mf_set in self.demand_var.sets.items()
        }

    def _validate_and_clamp_inputs(
        self,
        etc: float,
        crop_water_deficit: float,
        effective_rainfall: float,
    ) -> Tuple[float, float, float]:
        """
        Validate inputs rejecting NaN / Inf, clamping physical values to universe bounds.
        """
        if np.isnan(etc) or np.isinf(etc):
            raise ValueError(f"ETc input cannot be NaN or infinite. Got: {etc}")
        if np.isnan(crop_water_deficit) or np.isinf(crop_water_deficit):
            raise ValueError(f"Crop water deficit input cannot be NaN or infinite. Got: {crop_water_deficit}")
        if np.isnan(effective_rainfall) or np.isinf(effective_rainfall):
            raise ValueError(f"Effective rainfall input cannot be NaN or infinite. Got: {effective_rainfall}")

        c_etc = float(self.etc_var.clamp(etc))
        c_def = float(self.deficit_var.clamp(crop_water_deficit))
        c_rain = float(self.rainfall_var.clamp(effective_rainfall))
        return c_etc, c_def, c_rain

    def _fuzzify_inputs(
        self,
        c_etc: float,
        c_def: float,
        c_rain: float,
    ) -> Dict[str, Dict[str, float]]:
        """Compute membership degrees for all 3 water demand input variables."""
        return {
            "etc": self.etc_var.evaluate(c_etc, clamp=False),
            "crop_water_deficit": self.deficit_var.evaluate(c_def, clamp=False),
            "effective_rainfall": self.rainfall_var.evaluate(c_rain, clamp=False),
        }

    def evaluate(
        self,
        etc: float,
        crop_water_deficit: float,
        effective_rainfall: float,
        **kwargs: Any,
    ) -> float:
        """
        Compute crisp Water Demand output [0.0, 100.0]% using Mamdani inference.

        Supports alternative keyword arguments:
            etc_mm_day, water_deficit, effective_rainfall_mm.

        Parameters
        ----------
        etc : float
            Crop evapotranspiration rate in mm/day [0.0, 15.0].
        crop_water_deficit : float
            Atmospheric/crop water deficit in mm/day [0.0, 15.0].
        effective_rainfall : float
            Effective precipitation depth in mm [0.0, 50.0].

        Returns
        -------
        float
            Crisp water demand index [0.0, 100.0]%.
        """
        v_etc = kwargs.get("etc_mm_day", etc)
        v_def = kwargs.get("water_deficit", crop_water_deficit)
        v_rain = kwargs.get("effective_rainfall_mm", effective_rainfall)

        c_etc, c_def, c_rain = self._validate_and_clamp_inputs(v_etc, v_def, v_rain)
        memberships = self._fuzzify_inputs(c_etc, c_def, c_rain)

        consequent_activations = {name: 0.0 for name in self.demand_var.set_names}

        for rule in self.RULES:
            weights = []
            for var_name, term_or_terms in rule["antecedents"].items():
                var_mu = memberships[var_name]
                if isinstance(term_or_terms, list):
                    w = max(var_mu[t] for t in term_or_terms)
                else:
                    w = var_mu[term_or_terms]
                weights.append(w)

            firing_strength = min(weights) if weights else 0.0
            target_term = rule["consequent"]
            if firing_strength > consequent_activations[target_term]:
                consequent_activations[target_term] = float(firing_strength)

        # Implication & Aggregation across output grid
        # mu_agg(z) = max_i ( min(beta_i, mu_Ci(z)) )
        agg_mu = np.zeros_like(self.z_grid)
        for term_name, beta in consequent_activations.items():
            if beta > 0.0:
                clipped_mf = np.minimum(beta, self._output_mf_matrix[term_name])
                agg_mu = np.maximum(agg_mu, clipped_mf)

        # Centroid Defuzzification
        total_area = np.sum(agg_mu)
        if total_area < 1e-9:
            # Fallback for empty fuzzy set (edge safety)
            return 0.0

        centroid = float(np.sum(self.z_grid * agg_mu) / total_area)
        return float(np.clip(centroid, 0.0, 100.0))

    def evaluate_detailed(
        self,
        etc: float,
        crop_water_deficit: float,
        effective_rainfall: float,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute full inference and return comprehensive telemetry.

        Returns
        -------
        dict
            Dictionary containing inputs, fuzzified memberships, active rules,
            consequent activations, and defuzzified crisp output.
        """
        v_etc = kwargs.get("etc_mm_day", etc)
        v_def = kwargs.get("water_deficit", crop_water_deficit)
        v_rain = kwargs.get("effective_rainfall_mm", effective_rainfall)

        c_etc, c_def, c_rain = self._validate_and_clamp_inputs(v_etc, v_def, v_rain)
        memberships = self._fuzzify_inputs(c_etc, c_def, c_rain)

        active_rules = []
        consequent_activations = {name: 0.0 for name in self.demand_var.set_names}

        for rule in self.RULES:
            weights = []
            for var_name, term_or_terms in rule["antecedents"].items():
                var_mu = memberships[var_name]
                if isinstance(term_or_terms, list):
                    w = max(var_mu[t] for t in term_or_terms)
                else:
                    w = var_mu[term_or_terms]
                weights.append(w)

            firing_strength = min(weights) if weights else 0.0
            target_term = rule["consequent"]

            if firing_strength > 0.0:
                active_rules.append({
                    "rule_id": rule["id"],
                    "antecedents": rule["antecedents"],
                    "consequent": target_term,
                    "weight": float(firing_strength),
                    "description": rule["desc"],
                })

            if firing_strength > consequent_activations[target_term]:
                consequent_activations[target_term] = float(firing_strength)

        # Implication & Aggregation
        agg_mu = np.zeros_like(self.z_grid)
        for term_name, beta in consequent_activations.items():
            if beta > 0.0:
                clipped_mf = np.minimum(beta, self._output_mf_matrix[term_name])
                agg_mu = np.maximum(agg_mu, clipped_mf)

        total_area = float(np.sum(agg_mu))
        if total_area < 1e-9:
            centroid = 0.0
        else:
            centroid = float(np.sum(self.z_grid * agg_mu) / total_area)
        crisp_demand = float(np.clip(centroid, 0.0, 100.0))

        return {
            "etc": v_etc,
            "etc_clamped": c_etc,
            "crop_water_deficit": v_def,
            "crop_water_deficit_clamped": c_def,
            "effective_rainfall": v_rain,
            "effective_rainfall_clamped": c_rain,
            "water_demand": crisp_demand,
            "etc_membership": {k: float(v) for k, v in memberships["etc"].items()},
            "deficit_membership": {k: float(v) for k, v in memberships["crop_water_deficit"].items()},
            "effective_rainfall_membership": {k: float(v) for k, v in memberships["effective_rainfall"].items()},
            "consequent_activations": consequent_activations,
            "active_rules": active_rules,
            "total_fuzzy_area": total_area,
        }

    def evaluate_array(
        self,
        etc_arr: np.ndarray,
        deficit_arr: np.ndarray,
        rainfall_arr: np.ndarray,
    ) -> np.ndarray:
        """
        Vectorized batch evaluation for simulation timeseries arrays.

        Parameters
        ----------
        etc_arr : np.ndarray
            Array of crop evapotranspiration values (mm/day).
        deficit_arr : np.ndarray
            Array of crop water deficit values (mm/day).
        rainfall_arr : np.ndarray
            Array of effective rainfall values (mm).

        Returns
        -------
        np.ndarray
            Array of crisp water demand values [0.0, 100.0]%.
        """
        e_flat = np.asarray(etc_arr, dtype=float).flatten()
        d_flat = np.asarray(deficit_arr, dtype=float).flatten()
        r_flat = np.asarray(rainfall_arr, dtype=float).flatten()

        n = len(e_flat)
        if not (len(d_flat) == n and len(r_flat) == n):
            raise ValueError("All input arrays to evaluate_array must have identical dimensions.")

        results = np.zeros(n, dtype=float)
        for i in range(n):
            results[i] = self.evaluate(e_flat[i], d_flat[i], r_flat[i])

        return results.reshape(etc_arr.shape)

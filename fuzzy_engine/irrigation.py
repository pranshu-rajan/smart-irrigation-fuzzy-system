"""
FIS 4: Main Irrigation Fuzzy Inference System (MainIrrigationFIS).

Core Supervisory Control FIS of the hierarchical fuzzy irrigation architecture.
Synthesizes 4 heterogeneous physical and diagnostic indicators:
1. Soil Stress: [0.0, 100.0] %
   - Linguistic terms: Low, Moderate, High, Very High
2. Weather Stress: [0.0, 100.0] %
   - Linguistic terms: Low, Moderate, High, Very High
3. Water Demand: [0.0, 100.0] %
   - Linguistic terms: Very Low, Low, Moderate, High, Very High
4. Moisture Error e(t) = target_moisture - current_moisture: [-30.0, 30.0] %
   - Linguistic terms: Large Negative, Negative, Zero, Positive, Large Positive

Output:
1. Irrigation Command: [0.0, 100.0] %
   - Linguistic terms: Off, Low, Moderate, High, Maximum

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


class MainIrrigationFIS:
    """
    Mamdani Fuzzy Inference System for Supervisory Irrigation Command Generation.

    Parameters
    ----------
    resolution : int, optional
        Number of discrete points across the output universe [0, 100]% for centroid
        defuzzification. Default is 501 points (0.2% resolution).
    """

    # Comprehensive Hierarchical Engineering Rule Base (32 Rules):
    #
    # LAYER 1: Moisture Error Safety & Oversaturation Suppression (Rules 1-4)
    # When current soil moisture is above target (error < 0), irrigation is strongly
    # suppressed to prevent waterlogging, hypoxia, and runoff.
    #
    # LAYER 2: Balanced / At-Target Moisture Regulation (Rules 5-15)
    # When soil moisture is at target (error = 0), baseline maintenance pulses match
    # active crop water demand and emerging soil stress.
    #
    # LAYER 3: Moisture Deficit Replacement Kernel (Rules 16-25)
    # When soil moisture is below target (error > 0), irrigation command scales
    # directly with soil stress severity and active water demand.
    #
    # LAYER 4: Severe Moisture Depletion Override (Rules 26-28)
    # Large moisture deficits (error in large_positive) trigger high to maximum
    # replenishment commands to avert crop wilting.
    #
    # LAYER 5: Climatic Forcing & Environmental Modulation (Rules 29-32)
    # Extreme weather stress (heatwaves/desiccating winds) amplifies irrigation delivery
    # during deficits, while cool humid conditions eliminate unnecessary water use.
    RULES: List[Dict[str, Any]] = [
        # =========================================================================
        # LAYER 1: MOISTURE ERROR SAFETY & OVERSATURATION SUPPRESSION (4 Rules)
        # =========================================================================
        {
            "id": 1,
            "antecedents": {"moisture_error": "large_negative"},
            "consequent": "off",
            "desc": "Deeply oversaturated soil strictly shuts off irrigation",
        },
        {
            "id": 2,
            "antecedents": {
                "moisture_error": "negative",
                "soil_stress": ["low", "moderate"],
            },
            "consequent": "off",
            "desc": "Negative error with mild soil stress requires no irrigation",
        },
        {
            "id": 3,
            "antecedents": {
                "moisture_error": "negative",
                "soil_stress": ["high", "very_high"],
                "water_demand": ["very_low", "low", "moderate"],
            },
            "consequent": "off",
            "desc": "Negative error with low/moderate demand overrides higher stress",
        },
        {
            "id": 4,
            "antecedents": {
                "moisture_error": "negative",
                "soil_stress": ["high", "very_high"],
                "water_demand": ["high", "very_high"],
            },
            "consequent": "low",
            "desc": "Elevated stress and demand with mild negative error permits minimal maintenance pulse",
        },

        # =========================================================================
        # LAYER 2: BALANCED / AT-TARGET MOISTURE REGULATION (11 Rules)
        # Active when moisture error is near zero (e(t) in zero).
        # =========================================================================
        {
            "id": 5,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "low",
                "water_demand": "very_low",
            },
            "consequent": "off",
            "desc": "At target moisture with low soil stress and very low demand",
        },
        {
            "id": 6,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "low",
                "water_demand": ["low", "moderate"],
            },
            "consequent": "low",
            "desc": "At target with low/moderate demand maintains low replacement",
        },
        {
            "id": 7,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "low",
                "water_demand": ["high", "very_high"],
            },
            "consequent": "moderate",
            "desc": "At target with high transpirational demand requires moderate replacement",
        },
        {
            "id": 8,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "moderate",
                "water_demand": ["very_low", "low"],
            },
            "consequent": "low",
            "desc": "At target with moderate soil stress and low demand",
        },
        {
            "id": 9,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "moderate",
                "water_demand": "moderate",
            },
            "consequent": "moderate",
            "desc": "At target with moderate stress and moderate demand",
        },
        {
            "id": 10,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "moderate",
                "water_demand": ["high", "very_high"],
            },
            "consequent": "high",
            "desc": "At target with moderate stress and high demand",
        },
        {
            "id": 11,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "high",
                "water_demand": ["very_low", "low"],
            },
            "consequent": "moderate",
            "desc": "At target with high soil stress requires moderate intervention",
        },
        {
            "id": 12,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "high",
                "water_demand": ["moderate", "high"],
            },
            "consequent": "high",
            "desc": "At target with high stress and high demand",
        },
        {
            "id": 13,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "high",
                "water_demand": "very_high",
            },
            "consequent": "maximum",
            "desc": "At target with high stress and very high demand",
        },
        {
            "id": 14,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "very_high",
                "water_demand": ["very_low", "low"],
            },
            "consequent": "high",
            "desc": "At target with very high stress requires strong replenishment",
        },
        {
            "id": 15,
            "antecedents": {
                "moisture_error": "zero",
                "soil_stress": "very_high",
                "water_demand": ["moderate", "high", "very_high"],
            },
            "consequent": "maximum",
            "desc": "At target with severe stress and active demand",
        },

        # =========================================================================
        # LAYER 3: POSITIVE ERROR DEFICIT REPLACEMENT KERNEL (10 Rules)
        # Active when soil moisture is depleted below target (e(t) in positive).
        # =========================================================================
        {
            "id": 16,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "low",
                "water_demand": ["very_low", "low"],
            },
            "consequent": "low",
            "desc": "Mild depletion with low stress requires low irrigation",
        },
        {
            "id": 17,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "low",
                "water_demand": "moderate",
            },
            "consequent": "moderate",
            "desc": "Mild depletion with moderate demand",
        },
        {
            "id": 18,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "low",
                "water_demand": ["high", "very_high"],
            },
            "consequent": "high",
            "desc": "Mild depletion with high demand",
        },
        {
            "id": 19,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "moderate",
                "water_demand": ["very_low", "low"],
            },
            "consequent": "moderate",
            "desc": "Positive error with moderate stress",
        },
        {
            "id": 20,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "moderate",
                "water_demand": "moderate",
            },
            "consequent": "moderate",
            "desc": "Balanced deficit with moderate demand",
        },
        {
            "id": 21,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "moderate",
                "water_demand": ["high", "very_high"],
            },
            "consequent": "high",
            "desc": "Balanced deficit with high demand",
        },
        {
            "id": 22,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "high",
                "water_demand": ["very_low", "low"],
            },
            "consequent": "high",
            "desc": "High soil stress with positive error",
        },
        {
            "id": 23,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "high",
                "water_demand": ["moderate", "high"],
            },
            "consequent": "high",
            "desc": "High stress and positive error with active demand",
        },
        {
            "id": 24,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "high",
                "water_demand": "very_high",
            },
            "consequent": "maximum",
            "desc": "High stress and high demand with positive error",
        },
        {
            "id": 25,
            "antecedents": {
                "moisture_error": "positive",
                "soil_stress": "very_high",
            },
            "consequent": "maximum",
            "desc": "Severe stress with positive error requires maximum irrigation",
        },

        # =========================================================================
        # LAYER 4: LARGE POSITIVE ERROR SEVERE DEPLETION OVERRIDE (3 Rules)
        # =========================================================================
        {
            "id": 26,
            "antecedents": {
                "moisture_error": "large_positive",
                "soil_stress": "low",
            },
            "consequent": "moderate",
            "desc": "Large deficit even if sensor stress is low",
        },
        {
            "id": 27,
            "antecedents": {
                "moisture_error": "large_positive",
                "soil_stress": "moderate",
            },
            "consequent": "high",
            "desc": "Large deficit with moderate stress",
        },
        {
            "id": 28,
            "antecedents": {
                "moisture_error": "large_positive",
                "soil_stress": ["high", "very_high"],
            },
            "consequent": "maximum",
            "desc": "Severe depletion with high/very high stress commands maximum irrigation",
        },

        # =========================================================================
        # LAYER 5: CLIMATIC FORCING & ENVIRONMENTAL MODULATION (4 Rules)
        # =========================================================================
        {
            "id": 29,
            "antecedents": {
                "weather_stress": "very_high",
                "moisture_error": ["positive", "large_positive"],
                "soil_stress": ["moderate", "high", "very_high"],
            },
            "consequent": "maximum",
            "desc": "Heatwave forcing during soil deficit drives maximum irrigation",
        },
        {
            "id": 30,
            "antecedents": {
                "weather_stress": "very_high",
                "moisture_error": "zero",
                "soil_stress": ["high", "very_high"],
            },
            "consequent": "maximum",
            "desc": "Extreme climate stress with elevated root stress at target moisture",
        },
        {
            "id": 31,
            "antecedents": {
                "weather_stress": "high",
                "moisture_error": ["positive", "large_positive"],
                "water_demand": ["high", "very_high"],
            },
            "consequent": "high",
            "desc": "High atmospheric stress amplifies irrigation during moisture deficit",
        },
        {
            "id": 32,
            "antecedents": {
                "weather_stress": "low",
                "soil_stress": "low",
                "water_demand": "very_low",
            },
            "consequent": "off",
            "desc": "Cool calm overcast conditions with hydrated soil eliminates irrigation",
        },
    ]

    def __init__(
        self,
        resolution: int = 501,
        soil_stress_var: Optional[FuzzyVariable] = None,
        weather_stress_var: Optional[FuzzyVariable] = None,
        water_demand_var: Optional[FuzzyVariable] = None,
        moisture_error_var: Optional[FuzzyVariable] = None,
        command_var: Optional[FuzzyVariable] = None,
    ) -> None:
        # Bind variables from arguments or centralized global registry
        self.soil_stress_var: FuzzyVariable = (
            soil_stress_var if soil_stress_var is not None else get_fuzzy_variable("soil_stress")
        )
        self.weather_stress_var: FuzzyVariable = (
            weather_stress_var if weather_stress_var is not None else get_fuzzy_variable("weather_stress")
        )
        self.water_demand_var: FuzzyVariable = (
            water_demand_var if water_demand_var is not None else get_fuzzy_variable("water_demand")
        )
        self.moisture_error_var: FuzzyVariable = (
            moisture_error_var if moisture_error_var is not None else get_fuzzy_variable("moisture_error")
        )
        self.command_var: FuzzyVariable = (
            command_var if command_var is not None else get_fuzzy_variable("irrigation_command")
        )

        self.resolution = resolution
        # Output evaluation grid for centroid integration [0.0, 100.0]%
        self.z_grid = np.linspace(
            self.command_var.universe.min_val,
            self.command_var.universe.max_val,
            self.resolution,
        )

        # Pre-evaluate the output membership functions over z_grid
        self._output_mf_matrix: Dict[str, np.ndarray] = {
            name: mf_set.evaluate(self.z_grid)
            for name, mf_set in self.command_var.sets.items()
        }

    def _validate_and_clamp_inputs(
        self,
        soil_stress: float,
        weather_stress: float,
        water_demand: float,
        moisture_error: float,
    ) -> Tuple[float, float, float, float]:
        """
        Validate inputs rejecting NaN / Inf, clamping physical values to universe bounds.
        """
        if np.isnan(soil_stress) or np.isinf(soil_stress):
            raise ValueError(f"Soil stress input cannot be NaN or infinite. Got: {soil_stress}")
        if np.isnan(weather_stress) or np.isinf(weather_stress):
            raise ValueError(f"Weather stress input cannot be NaN or infinite. Got: {weather_stress}")
        if np.isnan(water_demand) or np.isinf(water_demand):
            raise ValueError(f"Water demand input cannot be NaN or infinite. Got: {water_demand}")
        if np.isnan(moisture_error) or np.isinf(moisture_error):
            raise ValueError(f"Moisture error input cannot be NaN or infinite. Got: {moisture_error}")

        c_ss = float(self.soil_stress_var.clamp(soil_stress))
        c_ws = float(self.weather_stress_var.clamp(weather_stress))
        c_wd = float(self.water_demand_var.clamp(water_demand))
        c_me = float(self.moisture_error_var.clamp(moisture_error))
        return c_ss, c_ws, c_wd, c_me

    def _fuzzify_inputs(
        self,
        c_ss: float,
        c_ws: float,
        c_wd: float,
        c_me: float,
    ) -> Dict[str, Dict[str, float]]:
        """Compute membership degrees for all 4 input variables."""
        return {
            "soil_stress": self.soil_stress_var.evaluate(c_ss, clamp=False),
            "weather_stress": self.weather_stress_var.evaluate(c_ws, clamp=False),
            "water_demand": self.water_demand_var.evaluate(c_wd, clamp=False),
            "moisture_error": self.moisture_error_var.evaluate(c_me, clamp=False),
        }

    def evaluate(
        self,
        soil_stress: float,
        weather_stress: float,
        water_demand: float,
        moisture_error: float,
        **kwargs: Any,
    ) -> float:
        """
        Compute normalized Irrigation Command output [0.0, 100.0]% using Mamdani inference.

        Parameters
        ----------
        soil_stress : float
            Soil moisture stress in range [0.0, 100.0]%.
        weather_stress : float
            Atmospheric weather stress in range [0.0, 100.0]%.
        water_demand : float
            Crop water demand in range [0.0, 100.0]%.
        moisture_error : float
            Soil moisture tracking error e(t) in range [-30.0, 30.0]%.

        Returns
        -------
        float
            Normalized irrigation command [0.0, 100.0]%.
        """
        c_ss, c_ws, c_wd, c_me = self._validate_and_clamp_inputs(
            soil_stress, weather_stress, water_demand, moisture_error
        )
        memberships = self._fuzzify_inputs(c_ss, c_ws, c_wd, c_me)

        consequent_activations = {name: 0.0 for name in self.command_var.set_names}

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
        soil_stress: float,
        weather_stress: float,
        water_demand: float,
        moisture_error: float,
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
        c_ss, c_ws, c_wd, c_me = self._validate_and_clamp_inputs(
            soil_stress, weather_stress, water_demand, moisture_error
        )
        memberships = self._fuzzify_inputs(c_ss, c_ws, c_wd, c_me)

        active_rules = []
        consequent_activations = {name: 0.0 for name in self.command_var.set_names}

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
        crisp_command = float(np.clip(centroid, 0.0, 100.0))

        return {
            "soil_stress": soil_stress,
            "soil_stress_clamped": c_ss,
            "weather_stress": weather_stress,
            "weather_stress_clamped": c_ws,
            "water_demand": water_demand,
            "water_demand_clamped": c_wd,
            "moisture_error": moisture_error,
            "moisture_error_clamped": c_me,
            "irrigation_command": crisp_command,
            "soil_stress_membership": {k: float(v) for k, v in memberships["soil_stress"].items()},
            "weather_stress_membership": {k: float(v) for k, v in memberships["weather_stress"].items()},
            "water_demand_membership": {k: float(v) for k, v in memberships["water_demand"].items()},
            "moisture_error_membership": {k: float(v) for k, v in memberships["moisture_error"].items()},
            "consequent_activations": consequent_activations,
            "active_rules": active_rules,
            "total_fuzzy_area": total_area,
        }

    def evaluate_array(
        self,
        soil_stress_arr: np.ndarray,
        weather_stress_arr: np.ndarray,
        water_demand_arr: np.ndarray,
        moisture_error_arr: np.ndarray,
    ) -> np.ndarray:
        """
        Vectorized batch evaluation for simulation timeseries arrays.

        Parameters
        ----------
        soil_stress_arr : np.ndarray
            Array of soil stress values (%).
        weather_stress_arr : np.ndarray
            Array of weather stress values (%).
        water_demand_arr : np.ndarray
            Array of water demand values (%).
        moisture_error_arr : np.ndarray
            Array of moisture error values (%).

        Returns
        -------
        np.ndarray
            Array of crisp normalized irrigation command values [0.0, 100.0]%.
        """
        ss_flat = np.asarray(soil_stress_arr, dtype=float).flatten()
        ws_flat = np.asarray(weather_stress_arr, dtype=float).flatten()
        wd_flat = np.asarray(water_demand_arr, dtype=float).flatten()
        me_flat = np.asarray(moisture_error_arr, dtype=float).flatten()

        n = len(ss_flat)
        if not (len(ws_flat) == n and len(wd_flat) == n and len(me_flat) == n):
            raise ValueError("All input arrays to evaluate_array must have identical dimensions.")

        results = np.zeros(n, dtype=float)
        for i in range(n):
            results[i] = self.evaluate(ss_flat[i], ws_flat[i], wd_flat[i], me_flat[i])

        return results.reshape(soil_stress_arr.shape)

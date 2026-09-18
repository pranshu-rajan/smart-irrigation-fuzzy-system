"""
FIS 5: Water Allocation Fuzzy Inference System (WaterAllocationFIS).

Allocates constrained shared water resources among competing agricultural zones.
Synthesizes 4 heterogeneous inputs:
1. available_water: [0.0, 100.0] %
   - Supply variable representing the fraction of nominal shared water supply available.
   - Linguistic terms: Very Low, Low, Moderate, High, Very High
2. zone_demand: [0.0, 100.0] %
   - Upstream irrigation request from MainIrrigationFIS (or equivalent control command).
   - Linguistic terms: Very Low, Low, Moderate, High, Very High
3. zone_stress: [0.0, 100.0] %
   - Zone crop physiological / soil root-zone moisture stress.
   - Linguistic terms: Low, Moderate, High, Very High
4. zone_priority: [0.0, 100.0] %
   - Explicit agronomic / economic weighting assigned to the zone.
   - Linguistic terms: Low, Medium, High, Critical

Output:
1. zone_allocation: [0.0, 100.0] %
   - Allocation factor representing the percentage of requested water granted.
   - Linguistic terms: None, Low, Moderate, High, Maximum

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


class WaterAllocationFIS:
    """
    Mamdani Fuzzy Inference System for Shared Water Allocation across Agricultural Zones.

    Parameters
    ----------
    resolution : int, optional
        Number of discrete points across the output universe [0, 100]% for centroid
        defuzzification. Default is 501 points (0.2% resolution).
    """

    # Comprehensive Hierarchical Engineering Rule Base (32 Rules):
    #
    # LAYER 1: Severe Scarcity & Zero-Demand Safety (Rules 1-5)
    # When available water is near zero or zone request is negligible, allocation is
    # suppressed to prevent water wastage and enforce physical scarcity boundaries.
    #
    # LAYER 2: Abundant Supply Satisfaction (Rules 6-11)
    # When available water is high or very high, zone demand is fulfilled proportionally,
    # with high-stress crops receiving priority maximum delivery.
    #
    # LAYER 3: Moderate Supply Balancing (Rules 12-18)
    # Under moderate water supply, priority and crop stress determine whether requests
    # are satisfied in full or throttled to conserve reservoir storage.
    #
    # LAYER 4: Low Supply & Drought Rationing (Rules 19-26)
    # Under low water supply, non-stressed or low-priority crops are strictly restricted,
    # reserving remaining reserves for high-priority and critically stressed crops.
    #
    # LAYER 5: Priority & Stress Cross-Modulation (Rules 27-32)
    # Specific high-consequence edge cases where critical priority and severe stress
    # override standard thresholds or low priority prevents allocation expansion.
    RULES: List[Dict[str, Any]] = [
        # =========================================================================
        # LAYER 1: SEVERE SCARCITY & ZERO-DEMAND SAFETY (5 Rules)
        # =========================================================================
        {
            "id": 1,
            "antecedents": {"zone_demand": "very_low"},
            "consequent": "none",
            "desc": "Negligible zone demand strictly requires no allocation",
        },
        {
            "id": 2,
            "antecedents": {
                "available_water": "very_low",
                "zone_priority": ["low", "medium"],
            },
            "consequent": "none",
            "desc": "Severe water scarcity suppresses low and medium priority zones",
        },
        {
            "id": 3,
            "antecedents": {
                "available_water": "very_low",
                "zone_stress": ["low", "moderate"],
            },
            "consequent": "none",
            "desc": "Severe water scarcity suppresses non-stressed crops",
        },
        {
            "id": 4,
            "antecedents": {
                "available_water": "very_low",
                "zone_stress": ["high", "very_high"],
                "zone_priority": ["high", "critical"],
            },
            "consequent": "low",
            "desc": "Severe scarcity permits only emergency low allocation for critical high-stress zones",
        },
        {
            "id": 5,
            "antecedents": {
                "available_water": "very_low",
                "zone_demand": ["high", "very_high"],
                "zone_priority": "low",
            },
            "consequent": "none",
            "desc": "High demand by low priority zone denied under severe scarcity",
        },

        # =========================================================================
        # LAYER 2: ABUNDANT SUPPLY SATISFACTION (6 Rules)
        # When available water is high or very high, full requested amounts are granted.
        # =========================================================================
        {
            "id": 6,
            "antecedents": {
                "available_water": ["high", "very_high"],
                "zone_demand": "low",
            },
            "consequent": "maximum",
            "desc": "Abundant water satisfies low demand in full",
        },
        {
            "id": 7,
            "antecedents": {
                "available_water": ["high", "very_high"],
                "zone_demand": "moderate",
            },
            "consequent": "maximum",
            "desc": "Abundant water satisfies moderate demand in full",
        },
        {
            "id": 8,
            "antecedents": {
                "available_water": ["high", "very_high"],
                "zone_demand": "high",
            },
            "consequent": "maximum",
            "desc": "Abundant water satisfies high demand in full",
        },
        {
            "id": 9,
            "antecedents": {
                "available_water": ["high", "very_high"],
                "zone_demand": "very_high",
            },
            "consequent": "maximum",
            "desc": "Abundant water satisfies very high demand in full",
        },
        {
            "id": 10,
            "antecedents": {
                "available_water": "very_high",
                "zone_priority": ["high", "critical"],
            },
            "consequent": "maximum",
            "desc": "Abundant water with high/critical priority commands maximum allocation",
        },
        {
            "id": 11,
            "antecedents": {
                "available_water": "high",
                "zone_demand": ["moderate", "high", "very_high"],
                "zone_stress": ["high", "very_high"],
            },
            "consequent": "maximum",
            "desc": "High supply with active stress commands maximum allocation factor",
        },

        # =========================================================================
        # LAYER 3: MODERATE SUPPLY BALANCING (7 Rules)
        # =========================================================================
        {
            "id": 12,
            "antecedents": {
                "available_water": "moderate",
                "zone_demand": "low",
            },
            "consequent": "low",
            "desc": "Moderate supply grants low demand",
        },
        {
            "id": 13,
            "antecedents": {
                "available_water": "moderate",
                "zone_demand": "moderate",
                "zone_stress": ["low", "moderate"],
            },
            "consequent": "moderate",
            "desc": "Moderate supply satisfies moderate demand for unstressed crops",
        },
        {
            "id": 14,
            "antecedents": {
                "available_water": "moderate",
                "zone_demand": "moderate",
                "zone_stress": ["high", "very_high"],
            },
            "consequent": "high",
            "desc": "Moderate supply boosts allocation for stressed crops with moderate demand",
        },
        {
            "id": 15,
            "antecedents": {
                "available_water": "moderate",
                "zone_demand": ["high", "very_high"],
                "zone_priority": ["high", "critical"],
            },
            "consequent": "high",
            "desc": "Moderate supply grants high allocation to high/critical priority zones",
        },
        {
            "id": 16,
            "antecedents": {
                "available_water": "moderate",
                "zone_demand": ["high", "very_high"],
                "zone_priority": "low",
            },
            "consequent": "moderate",
            "desc": "Moderate supply throttles high demand of low-priority zones to moderate",
        },
        {
            "id": 17,
            "antecedents": {
                "available_water": "moderate",
                "zone_demand": ["high", "very_high"],
                "zone_stress": "very_high",
                "zone_priority": ["high", "critical"],
            },
            "consequent": "maximum",
            "desc": "Severe stress and high priority achieve maximum allocation under moderate supply",
        },
        {
            "id": 18,
            "antecedents": {
                "available_water": "moderate",
                "zone_demand": "high",
                "zone_stress": ["low", "moderate"],
                "zone_priority": ["low", "medium"],
            },
            "consequent": "low",
            "desc": "Low stress and low priority throttled to low allocation under moderate supply",
        },

        # =========================================================================
        # LAYER 4: LOW SUPPLY & DROUGHT RATIONING (8 Rules)
        # =========================================================================
        {
            "id": 19,
            "antecedents": {
                "available_water": "low",
                "zone_demand": ["low", "moderate"],
                "zone_priority": "low",
            },
            "consequent": "none",
            "desc": "Low priority cut completely under supply scarcity",
        },
        {
            "id": 20,
            "antecedents": {
                "available_water": "low",
                "zone_demand": ["low", "moderate"],
                "zone_priority": ["medium", "high"],
            },
            "consequent": "low",
            "desc": "Medium and high priority receive low allocation under supply scarcity",
        },
        {
            "id": 21,
            "antecedents": {
                "available_water": "low",
                "zone_demand": ["high", "very_high"],
                "zone_priority": "low",
            },
            "consequent": "none",
            "desc": "High demand by low priority denied under supply scarcity",
        },
        {
            "id": 22,
            "antecedents": {
                "available_water": "low",
                "zone_demand": ["high", "very_high"],
                "zone_priority": "medium",
            },
            "consequent": "low",
            "desc": "Medium priority high demand throttled to low allocation under scarcity",
        },
        {
            "id": 23,
            "antecedents": {
                "available_water": "low",
                "zone_demand": ["high", "very_high"],
                "zone_priority": ["high", "critical"],
                "zone_stress": ["low", "moderate"],
            },
            "consequent": "moderate",
            "desc": "High priority crop with moderate stress receives moderate allocation under scarcity",
        },
        {
            "id": 24,
            "antecedents": {
                "available_water": "low",
                "zone_demand": ["high", "very_high"],
                "zone_priority": ["high", "critical"],
                "zone_stress": ["high", "very_high"],
            },
            "consequent": "high",
            "desc": "Critical high-stress zone protected with high allocation under scarcity",
        },
        {
            "id": 25,
            "antecedents": {
                "available_water": "low",
                "zone_stress": "low",
            },
            "consequent": "none",
            "desc": "Unstressed crops receive zero allocation under supply scarcity",
        },
        {
            "id": 26,
            "antecedents": {
                "available_water": "low",
                "zone_stress": "very_high",
                "zone_priority": "critical",
            },
            "consequent": "high",
            "desc": "Emergency rescue allocation for critical crop under drought",
        },

        # =========================================================================
        # LAYER 5: PRIORITY & STRESS CROSS-MODULATION (6 Rules)
        # =========================================================================
        {
            "id": 27,
            "antecedents": {
                "zone_priority": "critical",
                "zone_stress": ["high", "very_high"],
                "available_water": ["moderate", "high", "very_high"],
            },
            "consequent": "maximum",
            "desc": "Critical priority and high stress command maximum allocation when water is available",
        },
        {
            "id": 28,
            "antecedents": {
                "zone_priority": "low",
                "available_water": ["very_low", "low"],
            },
            "consequent": "none",
            "desc": "Strict cutoff for low-priority crops under scarce water",
        },
        {
            "id": 29,
            "antecedents": {
                "zone_demand": "very_high",
                "zone_stress": "low",
                "available_water": ["low", "moderate"],
            },
            "consequent": "low",
            "desc": "Excessive demand without corresponding stress is restrained",
        },
        {
            "id": 30,
            "antecedents": {
                "zone_demand": ["moderate", "high"],
                "zone_stress": ["high", "very_high"],
                "available_water": ["high", "very_high"],
            },
            "consequent": "maximum",
            "desc": "Elevated demand and high stress with abundant water triggers maximum allocation",
        },
        {
            "id": 31,
            "antecedents": {
                "available_water": "very_high",
                "zone_priority": ["high", "critical"],
                "zone_demand": ["moderate", "high", "very_high"],
            },
            "consequent": "maximum",
            "desc": "Abundant water and high priority guarantees maximum allocation factor",
        },
        {
            "id": 32,
            "antecedents": {
                "zone_stress": "very_high",
                "zone_demand": ["high", "very_high"],
                "zone_priority": ["high", "critical"],
                "available_water": ["low", "moderate"],
            },
            "consequent": "high",
            "desc": "Critical stressed crop preserved with high allocation under restricted supply",
        },
    ]

    def __init__(self, resolution: int = 501) -> None:
        # Bind variables from the centralized global registry
        self.available_water_var: FuzzyVariable = get_fuzzy_variable("available_water")
        self.zone_demand_var: FuzzyVariable = get_fuzzy_variable("zone_demand")
        self.zone_stress_var: FuzzyVariable = get_fuzzy_variable("zone_stress")
        self.zone_priority_var: FuzzyVariable = get_fuzzy_variable("zone_priority")
        self.allocation_var: FuzzyVariable = get_fuzzy_variable("zone_allocation")

        self.resolution = resolution
        # Output evaluation grid for centroid integration [0.0, 100.0]%
        self.z_grid = np.linspace(
            self.allocation_var.universe.min_val,
            self.allocation_var.universe.max_val,
            self.resolution,
        )

        # Pre-evaluate the output membership functions over z_grid
        self._output_mf_matrix: Dict[str, np.ndarray] = {
            name: mf_set.evaluate(self.z_grid)
            for name, mf_set in self.allocation_var.sets.items()
        }

    def _validate_and_clamp_inputs(
        self,
        available_water: float,
        zone_demand: float,
        zone_stress: float,
        zone_priority: float,
    ) -> Tuple[float, float, float, float]:
        """
        Validate inputs rejecting NaN / Inf, clamping physical values to universe bounds.
        """
        if np.isnan(available_water) or np.isinf(available_water):
            raise ValueError(f"Available water input cannot be NaN or infinite. Got: {available_water}")
        if np.isnan(zone_demand) or np.isinf(zone_demand):
            raise ValueError(f"Zone demand input cannot be NaN or infinite. Got: {zone_demand}")
        if np.isnan(zone_stress) or np.isinf(zone_stress):
            raise ValueError(f"Zone stress input cannot be NaN or infinite. Got: {zone_stress}")
        if np.isnan(zone_priority) or np.isinf(zone_priority):
            raise ValueError(f"Zone priority input cannot be NaN or infinite. Got: {zone_priority}")

        c_aw = float(self.available_water_var.clamp(available_water))
        c_zd = float(self.zone_demand_var.clamp(zone_demand))
        c_zs = float(self.zone_stress_var.clamp(zone_stress))
        c_zp = float(self.zone_priority_var.clamp(zone_priority))
        return c_aw, c_zd, c_zs, c_zp

    def _fuzzify_inputs(
        self,
        c_aw: float,
        c_zd: float,
        c_zs: float,
        c_zp: float,
    ) -> Dict[str, Dict[str, float]]:
        """Compute membership degrees for all 4 input variables."""
        return {
            "available_water": self.available_water_var.evaluate(c_aw, clamp=False),
            "zone_demand": self.zone_demand_var.evaluate(c_zd, clamp=False),
            "zone_stress": self.zone_stress_var.evaluate(c_zs, clamp=False),
            "zone_priority": self.zone_priority_var.evaluate(c_zp, clamp=False),
        }

    def evaluate(
        self,
        available_water: float,
        zone_demand: float,
        zone_stress: float,
        zone_priority: float,
        **kwargs: Any,
    ) -> float:
        """
        Compute normalized Allocation Factor output [0.0, 100.0]% using Mamdani inference.

        Parameters
        ----------
        available_water : float
            Available water supply fraction in range [0.0, 100.0]%.
        zone_demand : float
            Zone irrigation demand / command in range [0.0, 100.0]%.
        zone_stress : float
            Crop physiological / soil moisture stress in range [0.0, 100.0]%.
        zone_priority : float
            Zone agronomic allocation priority in range [0.0, 100.0]%.

        Returns
        -------
        float
            Normalized allocation factor [0.0, 100.0]%.
        """
        c_aw, c_zd, c_zs, c_zp = self._validate_and_clamp_inputs(
            available_water, zone_demand, zone_stress, zone_priority
        )

        # Zero demand safety check: if zone demands no water, allocation is strictly 0%
        if c_zd <= 1e-4:
            return 0.0

        # Zero supply safety check: if no water is available, allocation is strictly 0%
        if c_aw <= 1e-4:
            return 0.0

        memberships = self._fuzzify_inputs(c_aw, c_zd, c_zs, c_zp)

        consequent_activations = {name: 0.0 for name in self.allocation_var.set_names}

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
        available_water: float,
        zone_demand: float,
        zone_stress: float,
        zone_priority: float,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute full inference and return comprehensive telemetry.

        Returns
        -------
        dict
            Dictionary containing inputs, fuzzified memberships, active rules,
            consequent activations, aggregated fuzzy set, and defuzzified crisp output.
        """
        c_aw, c_zd, c_zs, c_zp = self._validate_and_clamp_inputs(
            available_water, zone_demand, zone_stress, zone_priority
        )

        memberships = self._fuzzify_inputs(c_aw, c_zd, c_zs, c_zp)

        active_rules = []
        consequent_activations = {name: 0.0 for name in self.allocation_var.set_names}

        # Handle hard boundary conditions for telemetry
        if c_zd <= 1e-4 or c_aw <= 1e-4:
            return {
                "inputs": {
                    "available_water": available_water,
                    "zone_demand": zone_demand,
                    "zone_stress": zone_stress,
                    "zone_priority": zone_priority,
                },
                "clamped_inputs": {
                    "available_water": c_aw,
                    "zone_demand": c_zd,
                    "zone_stress": c_zs,
                    "zone_priority": c_zp,
                },
                "memberships": memberships,
                "active_rules": [],
                "consequent_activations": consequent_activations,
                "defuzzified_output": 0.0,
                "zero_safety_override": True,
            }

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
                    "firing_strength": float(firing_strength),
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

        total_area = np.sum(agg_mu)
        if total_area < 1e-9:
            centroid = 0.0
        else:
            centroid = float(np.sum(self.z_grid * agg_mu) / total_area)

        crisp_output = float(np.clip(centroid, 0.0, 100.0))

        return {
            "inputs": {
                "available_water": available_water,
                "zone_demand": zone_demand,
                "zone_stress": zone_stress,
                "zone_priority": zone_priority,
            },
            "clamped_inputs": {
                "available_water": c_aw,
                "zone_demand": c_zd,
                "zone_stress": c_zs,
                "zone_priority": c_zp,
            },
            "memberships": memberships,
            "active_rules": sorted(active_rules, key=lambda r: r["firing_strength"], reverse=True),
            "consequent_activations": consequent_activations,
            "defuzzified_output": crisp_output,
            "zero_safety_override": False,
        }

    def evaluate_array(
        self,
        available_water_arr: np.ndarray,
        zone_demand_arr: np.ndarray,
        zone_stress_arr: np.ndarray,
        zone_priority_arr: np.ndarray,
    ) -> np.ndarray:
        """
        Vectorized/batch evaluation over synchronized 1D numpy arrays.

        Parameters
        ----------
        available_water_arr : np.ndarray
        zone_demand_arr : np.ndarray
        zone_stress_arr : np.ndarray
        zone_priority_arr : np.ndarray

        Returns
        -------
        np.ndarray
            Array of defuzzified allocation factors [0.0, 100.0]%.
        """
        aw = np.asarray(available_water_arr, dtype=np.float64)
        zd = np.asarray(zone_demand_arr, dtype=np.float64)
        zs = np.asarray(zone_stress_arr, dtype=np.float64)
        zp = np.asarray(zone_priority_arr, dtype=np.float64)

        if not (aw.shape == zd.shape == zs.shape == zp.shape):
            raise ValueError(
                f"Array shapes must match: aw={aw.shape}, zd={zd.shape}, zs={zs.shape}, zp={zp.shape}"
            )

        n = aw.size
        flat_aw = aw.ravel()
        flat_zd = zd.ravel()
        flat_zs = zs.ravel()
        flat_zp = zp.ravel()

        results = np.zeros(n, dtype=np.float64)
        for i in range(n):
            results[i] = self.evaluate(flat_aw[i], flat_zd[i], flat_zs[i], flat_zp[i])

        return results.reshape(aw.shape)

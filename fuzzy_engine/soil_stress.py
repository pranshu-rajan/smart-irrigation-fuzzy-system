"""
FIS 1: Soil Stress Fuzzy Inference System.

Evaluates crop root-zone water stress based on Relative Soil Moisture (RSM)
and Moisture Tracking Error e(t) = target_moisture - current_moisture.

Inputs:
    1. Relative Soil Moisture (RSM): [0.0, 1.0]
       - Linguistic terms: Very Dry, Dry, Adequate, Wet, Very Wet
    2. Moisture Error e(t): [-30.0, 30.0] %
       - Linguistic terms: Large Negative, Negative, Zero, Positive, Large Positive

Output:
    1. Soil Stress: [0.0, 100.0] %
       - Linguistic terms: Low, Moderate, High, Very High

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


class SoilStressFIS:
    """
    Mamdani Fuzzy Inference System for Crop Root-Zone Soil Moisture Stress.

    Parameters
    ----------
    resolution : int, optional
        Number of discrete points across the output universe [0, 100]% for centroid
        defuzzification. Default is 501 points (0.2% resolution).
    """

    # 25-Rule Base: (RSM term, Error term) -> Output Stress term
    # Engineering Rationale:
    # - Decreasing RSM (drier soil) drives higher stress.
    # - Positive error (moisture deficit below target) amplifies stress.
    # - High RSM and negative error (excess water) eliminate soil stress.
    RULES: List[Tuple[str, str, str]] = [
        # Very Dry soil rules (RSM near Wilting Point)
        ("very_dry", "large_positive", "very_high"),  # Rule 1
        ("very_dry", "positive", "very_high"),        # Rule 2
        ("very_dry", "zero", "high"),                # Rule 3
        ("very_dry", "negative", "high"),            # Rule 4
        ("very_dry", "large_negative", "moderate"),  # Rule 5
        # Dry soil rules
        ("dry", "large_positive", "very_high"),      # Rule 6
        ("dry", "positive", "high"),                 # Rule 7
        ("dry", "zero", "moderate"),                 # Rule 8
        ("dry", "negative", "low"),                  # Rule 9
        ("dry", "large_negative", "low"),            # Rule 10
        # Adequate soil rules (optimal root zone)
        ("adequate", "large_positive", "high"),      # Rule 11
        ("adequate", "positive", "moderate"),        # Rule 12
        ("adequate", "zero", "low"),                 # Rule 13
        ("adequate", "negative", "low"),             # Rule 14
        ("adequate", "large_negative", "low"),       # Rule 15
        # Wet soil rules (approaching Field Capacity)
        ("wet", "large_positive", "moderate"),       # Rule 16
        ("wet", "positive", "low"),                  # Rule 17
        ("wet", "zero", "low"),                      # Rule 18
        ("wet", "negative", "low"),                  # Rule 19
        ("wet", "large_negative", "low"),            # Rule 20
        # Very Wet soil rules (at or above Field Capacity)
        ("very_wet", "large_positive", "low"),       # Rule 21
        ("very_wet", "positive", "low"),             # Rule 22
        ("very_wet", "zero", "low"),                 # Rule 23
        ("very_wet", "negative", "low"),             # Rule 24
        ("very_wet", "large_negative", "low"),       # Rule 25
    ]

    def __init__(self, resolution: int = 501) -> None:
        # Bind variables from the central registry
        self.rsm_var: FuzzyVariable = get_fuzzy_variable("rsm")
        self.error_var: FuzzyVariable = get_fuzzy_variable("moisture_error")
        self.stress_var: FuzzyVariable = get_fuzzy_variable("soil_stress")

        self.resolution = resolution
        # Output evaluation grid for centroid integration
        self.z_grid = np.linspace(
            self.stress_var.universe.min_val,
            self.stress_var.universe.max_val,
            self.resolution,
        )

        # Pre-evaluate the output membership functions over z_grid
        self._output_mf_matrix: Dict[str, np.ndarray] = {
            name: mf_set.evaluate(self.z_grid)
            for name, mf_set in self.stress_var.sets.items()
        }

    def _validate_inputs(self, rsm: float, moisture_error: float) -> Tuple[float, float]:
        """
        Validate input values, rejecting NaN and infinite numbers.
        Returns clamped physical values.
        """
        if np.isnan(rsm) or np.isinf(rsm):
            raise ValueError(f"RSM input cannot be NaN or infinite. Got: {rsm}")
        if np.isnan(moisture_error) or np.isinf(moisture_error):
            raise ValueError(f"Moisture error input cannot be NaN or infinite. Got: {moisture_error}")

        # Clamping to universe limits
        clamped_rsm = float(self.rsm_var.clamp(rsm))
        clamped_error = float(self.error_var.clamp(moisture_error))
        return clamped_rsm, clamped_error

    def evaluate(self, rsm: float, moisture_error: float) -> float:
        """
        Compute crisp Soil Stress output [0.0, 100.0]% using Mamdani inference and centroid defuzzification.

        Parameters
        ----------
        rsm : float
            Relative Soil Moisture in range [0.0, 1.0].
        moisture_error : float
            Moisture tracking error in range [-30.0, 30.0]%.

        Returns
        -------
        float
            Crisp soil stress index [0.0, 100.0]%.
        """
        clamped_rsm, clamped_error = self._validate_inputs(rsm, moisture_error)

        # 1. Fuzzification
        rsm_mu = self.rsm_var.evaluate(clamped_rsm, clamp=False)
        error_mu = self.error_var.evaluate(clamped_error, clamp=False)

        # 2. Rule evaluation and consequent aggregation
        # We accumulate the maximum activation for each consequent term (Low, Moderate, High, Very High)
        consequent_activations = {name: 0.0 for name in self.stress_var.set_names}

        for rsm_term, err_term, stress_term in self.RULES:
            # T-Norm: Minimum for AND
            firing_weight = min(rsm_mu[rsm_term], error_mu[err_term])
            if firing_weight > consequent_activations[stress_term]:
                consequent_activations[stress_term] = firing_weight

        # 3. Implication and Aggregation across output grid
        # mu_agg(z) = max_L ( min(beta_L, mu_L(z)) )
        agg_mu = np.zeros_like(self.z_grid)
        for stress_term, beta in consequent_activations.items():
            if beta > 0.0:
                clipped_mf = np.minimum(beta, self._output_mf_matrix[stress_term])
                agg_mu = np.maximum(agg_mu, clipped_mf)

        # 4. Centroid Defuzzification
        # z* = sum(z * mu(z)) / sum(mu(z))
        total_area = np.sum(agg_mu)
        if total_area < 1e-9:
            # Fallback for empty fuzzy set (edge safety)
            return 0.0

        centroid = float(np.sum(self.z_grid * agg_mu) / total_area)
        # Ensure result strictly within [0.0, 100.0]
        return float(np.clip(centroid, 0.0, 100.0))

    def evaluate_detailed(self, rsm: float, moisture_error: float) -> Dict[str, Any]:
        """
        Execute full inference and return comprehensive telemetry.

        Returns
        -------
        dict
            Dictionary containing inputs, fuzzified memberships, active rules,
            consequent activations, and defuzzified crisp output.
        """
        clamped_rsm, clamped_error = self._validate_inputs(rsm, moisture_error)

        # 1. Fuzzification
        rsm_mu = self.rsm_var.evaluate(clamped_rsm, clamp=False)
        error_mu = self.error_var.evaluate(clamped_error, clamp=False)

        # 2. Rule evaluation
        active_rules = []
        consequent_activations = {name: 0.0 for name in self.stress_var.set_names}

        for idx, (rsm_term, err_term, stress_term) in enumerate(self.RULES, 1):
            firing_weight = min(rsm_mu[rsm_term], error_mu[err_term])
            if firing_weight > 0.0:
                active_rules.append({
                    "rule_id": idx,
                    "rsm_term": rsm_term,
                    "error_term": err_term,
                    "consequent": stress_term,
                    "weight": float(firing_weight),
                })
            if firing_weight > consequent_activations[stress_term]:
                consequent_activations[stress_term] = float(firing_weight)

        # 3. Implication and Aggregation
        agg_mu = np.zeros_like(self.z_grid)
        for stress_term, beta in consequent_activations.items():
            if beta > 0.0:
                clipped_mf = np.minimum(beta, self._output_mf_matrix[stress_term])
                agg_mu = np.maximum(agg_mu, clipped_mf)

        # 4. Defuzzification
        total_area = float(np.sum(agg_mu))
        if total_area < 1e-9:
            centroid = 0.0
        else:
            centroid = float(np.sum(self.z_grid * agg_mu) / total_area)
        crisp_stress = float(np.clip(centroid, 0.0, 100.0))

        return {
            "rsm_input": rsm,
            "rsm_clamped": clamped_rsm,
            "moisture_error_input": moisture_error,
            "moisture_error_clamped": clamped_error,
            "soil_stress": crisp_stress,
            "rsm_membership": {k: float(v) for k, v in rsm_mu.items()},
            "error_membership": {k: float(v) for k, v in error_mu.items()},
            "consequent_activations": consequent_activations,
            "active_rules": active_rules,
            "total_fuzzy_area": total_area,
        }

    def evaluate_array(self, rsm_arr: np.ndarray, error_arr: np.ndarray) -> np.ndarray:
        """
        Vectorized batch evaluation for simulation timeseries arrays.
        """
        rsm_flat = np.asarray(rsm_arr, dtype=float).flatten()
        err_flat = np.asarray(error_arr, dtype=float).flatten()
        if len(rsm_flat) != len(err_flat):
            raise ValueError(f"Array length mismatch: {len(rsm_flat)} != {len(err_flat)}")

        results = np.zeros(len(rsm_flat), dtype=float)
        for i in range(len(rsm_flat)):
            results[i] = self.evaluate(rsm_flat[i], err_flat[i])

        return results.reshape(rsm_arr.shape)

"""
FIS 2: Weather Stress Fuzzy Inference System.

Evaluates atmospheric evaporative demand and environmental climatic stress
based on Temperature, Relative Humidity, Solar Radiation, Wind Speed, and Rainfall.

Inputs:
    1. Temperature: [10.0, 50.0] °C
       - Linguistic terms: Low, Moderate, High, Very High
    2. Relative Humidity: [0.0, 100.0] %
       - Linguistic terms: Very Low, Low, Moderate, High, Very High
    3. Solar Radiation: [0.0, 1200.0] W/m²
       - Linguistic terms: Low, Moderate, High, Very High
    4. Wind Speed: [0.0, 15.0] m/s
       - Linguistic terms: Calm, Low, Moderate, High, Very High
    5. Rainfall: [0.0, 50.0] mm/timestep
       - Linguistic terms: None, Light, Moderate, Heavy, Very Heavy

Output:
    1. Weather Stress: [0.0, 100.0] %
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


class WeatherStressFIS:
    """
    Mamdani Fuzzy Inference System for Atmospheric Weather and Environmental Stress.

    Parameters
    ----------
    resolution : int, optional
        Number of discrete points across output universe [0, 100]% for centroid
        defuzzification. Default is 501 points (0.2% resolution).
    """

    # Comprehensive Hierarchical Engineering Rule Base:
    # 1. Direct Rainfall Suppression Layer: Active during precipitation events.
    # 2. Thermal-Humidity (VPD) Core Matrix: 20 baseline rules active under dry/non-rain conditions.
    # 3. Radiative and Advective Modulation Rules: Elevate stress under high solar/wind forcing.
    # 4. Nocturnal / Calm Baselines: Suppress stress under cool overcast conditions.
    RULES: List[Dict[str, Any]] = [
        # =========================================================================
        # LAYER 1: DIRECT PRECIPITATION SUPPRESSION (Rainfall Relief)
        # =========================================================================
        {
            "id": 1,
            "antecedents": {"rainfall": ["heavy", "very_heavy"]},
            "consequent": "low",
            "desc": "Heavy to torrential rainfall unconditionally suppresses atmospheric stress",
        },
        {
            "id": 2,
            "antecedents": {
                "rainfall": "moderate",
                "humidity": ["moderate", "high", "very_high"],
            },
            "consequent": "low",
            "desc": "Moderate rain in moist air halts evaporative tension",
        },
        {
            "id": 3,
            "antecedents": {
                "rainfall": "moderate",
                "humidity": ["very_low", "low"],
            },
            "consequent": "moderate",
            "desc": "Moderate rain during hot dry spell provides partial relief",
        },
        {
            "id": 4,
            "antecedents": {
                "rainfall": "light",
                "humidity": ["high", "very_high"],
            },
            "consequent": "low",
            "desc": "Light rain under humid skies maintains low stress",
        },
        {
            "id": 5,
            "antecedents": {
                "rainfall": "light",
                "temperature": "moderate",
                "humidity": "moderate",
            },
            "consequent": "moderate",
            "desc": "Light shower during temperate weather maintains moderate stress",
        },
        {
            "id": 6,
            "antecedents": {
                "rainfall": "light",
                "temperature": ["high", "very_high"],
                "humidity": ["very_low", "low"],
            },
            "consequent": "high",
            "desc": "Light sprinkle during heatwave cannot eliminate high stress",
        },

        # =========================================================================
        # LAYER 2: THERMAL-HUMIDITY (VPD) BASELINE KERNEL (20 Rules)
        # Active when rainfall is absent or negligible (none / light).
        # =========================================================================
        # Very High Temperature (Heatwave regime)
        {"id": 7,  "antecedents": {"temperature": "very_high", "humidity": "very_low", "rainfall": ["none", "light"]}, "consequent": "very_high", "desc": "Extreme temperature with arid parched air"},
        {"id": 8,  "antecedents": {"temperature": "very_high", "humidity": "low", "rainfall": ["none", "light"]},      "consequent": "very_high", "desc": "Extreme heat with low humidity"},
        {"id": 9,  "antecedents": {"temperature": "very_high", "humidity": "moderate", "rainfall": ["none", "light"]}, "consequent": "high",      "desc": "Extreme heat with moderate humidity"},
        {"id": 10, "antecedents": {"temperature": "very_high", "humidity": "high", "rainfall": ["none", "light"]},     "consequent": "moderate",  "desc": "Extreme heat mitigated by high humidity"},
        {"id": 11, "antecedents": {"temperature": "very_high", "humidity": "very_high", "rainfall": ["none", "light"]},"consequent": "low",       "desc": "Near-saturated tropical air limits evaporative pull"},

        # High Temperature (Hot summer regime)
        {"id": 12, "antecedents": {"temperature": "high", "humidity": "very_low", "rainfall": ["none", "light"]}, "consequent": "very_high", "desc": "Hot dry desert air creates severe evaporative demand"},
        {"id": 13, "antecedents": {"temperature": "high", "humidity": "low", "rainfall": ["none", "light"]},      "consequent": "high",      "desc": "Hot dry summer midday conditions"},
        {"id": 14, "antecedents": {"temperature": "high", "humidity": "moderate", "rainfall": ["none", "light"]}, "consequent": "moderate",  "desc": "Warm temperate conditions with moderate humidity"},
        {"id": 15, "antecedents": {"temperature": "high", "humidity": "high", "rainfall": ["none", "light"]},     "consequent": "low",       "desc": "Warm humid conditions suppress transpirational deficit"},
        {"id": 16, "antecedents": {"temperature": "high", "humidity": "very_high", "rainfall": ["none", "light"]},"consequent": "low",       "desc": "Near-saturated air prevents water loss"},

        # Moderate Temperature (Temperate nominal regime)
        {"id": 17, "antecedents": {"temperature": "moderate", "humidity": "very_low", "rainfall": ["none", "light"]}, "consequent": "high",      "desc": "Temperate temperature with arid air causes high demand"},
        {"id": 18, "antecedents": {"temperature": "moderate", "humidity": "low", "rainfall": ["none", "light"]},      "consequent": "moderate",  "desc": "Temperate dry day"},
        {"id": 19, "antecedents": {"temperature": "moderate", "humidity": "moderate", "rainfall": ["none", "light"]}, "consequent": "moderate",  "desc": "Nominal balanced agricultural baseline"},
        {"id": 20, "antecedents": {"temperature": "moderate", "humidity": "high", "rainfall": ["none", "light"]},     "consequent": "low",       "desc": "Temperate humid conditions"},
        {"id": 21, "antecedents": {"temperature": "moderate", "humidity": "very_high", "rainfall": ["none", "light"]},"consequent": "low",       "desc": "Moist temperate air suppresses stress"},

        # Low Temperature (Cool / Mild regime)
        {"id": 22, "antecedents": {"temperature": "low", "humidity": "very_low", "rainfall": ["none", "light"]}, "consequent": "moderate",  "desc": "Cool dry air produces moderate demand"},
        {"id": 23, "antecedents": {"temperature": "low", "humidity": "low", "rainfall": ["none", "light"]},      "consequent": "low",       "desc": "Cool conditions limit saturated vapor pressure"},
        {"id": 24, "antecedents": {"temperature": "low", "humidity": "moderate", "rainfall": ["none", "light"]}, "consequent": "low",       "desc": "Cool temperate baseline"},
        {"id": 25, "antecedents": {"temperature": "low", "humidity": "high", "rainfall": ["none", "light"]},     "consequent": "low",       "desc": "Cool humid weather"},
        {"id": 26, "antecedents": {"temperature": "low", "humidity": "very_high", "rainfall": ["none", "light"]},"consequent": "low",       "desc": "Cold saturated morning air"},

        # =========================================================================
        # LAYER 3: RADIATIVE & SOLAR FORCING MODULATION
        # High solar radiation boosts evaporative demand on cloudless days.
        # =========================================================================
        {
            "id": 27,
            "antecedents": {
                "solar_radiation": "very_high",
                "humidity": ["very_low", "low"],
                "rainfall": "none",
            },
            "consequent": "high",
            "desc": "Intense solar irradiance through cloudless dry air elevates stress",
        },
        {
            "id": 28,
            "antecedents": {
                "solar_radiation": "very_high",
                "temperature": ["high", "very_high"],
                "humidity": ["very_low", "low", "moderate"],
                "rainfall": "none",
            },
            "consequent": "very_high",
            "desc": "Intense solar radiative forcing during hot weather drives extreme stress",
        },
        {
            "id": 29,
            "antecedents": {
                "solar_radiation": "high",
                "temperature": ["high", "very_high"],
                "humidity": ["very_low", "low"],
                "rainfall": "none",
            },
            "consequent": "high",
            "desc": "High midday solar load drives elevated transpiration",
        },

        # =========================================================================
        # LAYER 4: ADVECTIVE WIND MODULATION
        # High wind speed thins boundary layer resistance and exacerbates dry air.
        # =========================================================================
        {
            "id": 30,
            "antecedents": {
                "wind_speed": "very_high",
                "humidity": ["very_low", "low"],
                "temperature": ["high", "very_high"],
                "rainfall": "none",
            },
            "consequent": "very_high",
            "desc": "Gale-force desiccating winds strip boundary layer resistance",
        },
        {
            "id": 31,
            "antecedents": {
                "wind_speed": ["high", "very_high"],
                "humidity": ["very_low", "low"],
                "rainfall": "none",
            },
            "consequent": "high",
            "desc": "Strong dry wind accelerates atmospheric evaporative loss",
        },
        {
            "id": 32,
            "antecedents": {
                "wind_speed": "high",
                "temperature": ["high", "very_high"],
                "solar_radiation": ["high", "very_high"],
                "rainfall": "none",
            },
            "consequent": "very_high",
            "desc": "Hot sunny windy day maximizes Penman-Monteith aerodynamics",
        },

        # =========================================================================
        # LAYER 5: NOCTURNAL / CALM MITIGATION RULES
        # Calm winds or absence of solar radiation lower transpirational tension.
        # =========================================================================
        {
            "id": 33,
            "antecedents": {
                "solar_radiation": "low",
                "wind_speed": ["calm", "low"],
                "temperature": ["low", "moderate"],
            },
            "consequent": "low",
            "desc": "Calm overcast or nocturnal conditions with minimal solar forcing",
        },
        {
            "id": 34,
            "antecedents": {
                "humidity": "very_high",
            },
            "consequent": "low",
            "desc": "Near-saturated air unconditionally halts transpiration",
        },
    ]

    def __init__(self, resolution: int = 501) -> None:
        # Bind variables from central registry
        self.temp_var: FuzzyVariable = get_fuzzy_variable("temperature")
        self.hum_var: FuzzyVariable = get_fuzzy_variable("humidity")
        self.solar_var: FuzzyVariable = get_fuzzy_variable("solar_radiation")
        self.wind_var: FuzzyVariable = get_fuzzy_variable("wind_speed")
        self.rain_var: FuzzyVariable = get_fuzzy_variable("rainfall")
        self.stress_var: FuzzyVariable = get_fuzzy_variable("weather_stress")

        self.resolution = resolution
        self.z_grid = np.linspace(
            self.stress_var.universe.min_val,
            self.stress_var.universe.max_val,
            self.resolution,
        )

        # Pre-evaluate output membership functions over z_grid
        self._output_mf_matrix: Dict[str, np.ndarray] = {
            name: mf_set.evaluate(self.z_grid)
            for name, mf_set in self.stress_var.sets.items()
        }

    def _validate_and_clamp_inputs(
        self,
        temperature: float,
        humidity: float,
        solar_radiation: float,
        wind_speed: float,
        rainfall: float,
    ) -> Tuple[float, float, float, float, float]:
        """Validate inputs against NaN/Inf and clamp to physical universes."""
        vals = [temperature, humidity, solar_radiation, wind_speed, rainfall]
        names = ["Temperature", "Humidity", "Solar Radiation", "Wind Speed", "Rainfall"]
        for val, name in zip(vals, names):
            if np.isnan(val) or np.isinf(val):
                raise ValueError(f"{name} input cannot be NaN or infinite. Got: {val}")

        c_temp = float(self.temp_var.clamp(temperature))
        c_hum = float(self.hum_var.clamp(humidity))
        c_sol = float(self.solar_var.clamp(solar_radiation))
        c_wind = float(self.wind_var.clamp(wind_speed))
        c_rain = float(self.rain_var.clamp(rainfall))
        return c_temp, c_hum, c_sol, c_wind, c_rain

    def _fuzzify_inputs(
        self,
        c_temp: float,
        c_hum: float,
        c_sol: float,
        c_wind: float,
        c_rain: float,
    ) -> Dict[str, Dict[str, float]]:
        """Compute membership degrees for all 5 weather input variables."""
        return {
            "temperature": self.temp_var.evaluate(c_temp, clamp=False),
            "humidity": self.hum_var.evaluate(c_hum, clamp=False),
            "solar_radiation": self.solar_var.evaluate(c_sol, clamp=False),
            "wind_speed": self.wind_var.evaluate(c_wind, clamp=False),
            "rainfall": self.rain_var.evaluate(c_rain, clamp=False),
        }

    def evaluate(
        self,
        temperature: float,
        humidity: float,
        solar_radiation: float,
        wind_speed: float,
        rainfall: float,
        **kwargs: Any,
    ) -> float:
        """
        Compute crisp Weather Stress output [0.0, 100.0]% using Mamdani inference.

        Supports alternative keyword arguments:
            temperature_c, humidity_percent, solar_radiation_wm2, wind_speed_ms, rainfall_mm.
        """
        temp = kwargs.get("temperature_c", temperature)
        hum = kwargs.get("humidity_percent", humidity)
        sol = kwargs.get("solar_radiation_wm2", solar_radiation)
        wind = kwargs.get("wind_speed_ms", wind_speed)
        rain = kwargs.get("rainfall_mm", rainfall)

        c_temp, c_hum, c_sol, c_wind, c_rain = self._validate_and_clamp_inputs(
            temp, hum, sol, wind, rain
        )
        memberships = self._fuzzify_inputs(c_temp, c_hum, c_sol, c_wind, c_rain)

        consequent_activations = {name: 0.0 for name in self.stress_var.set_names}

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

        # Implication & Aggregation
        agg_mu = np.zeros_like(self.z_grid)
        for term_name, beta in consequent_activations.items():
            if beta > 0.0:
                clipped_mf = np.minimum(beta, self._output_mf_matrix[term_name])
                agg_mu = np.maximum(agg_mu, clipped_mf)

        # Centroid defuzzification
        total_area = np.sum(agg_mu)
        if total_area < 1e-9:
            return 0.0

        centroid = float(np.sum(self.z_grid * agg_mu) / total_area)
        return float(np.clip(centroid, 0.0, 100.0))

    def evaluate_detailed(
        self,
        temperature: float,
        humidity: float,
        solar_radiation: float,
        wind_speed: float,
        rainfall: float,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute full inference and return comprehensive diagnostic telemetry.
        """
        temp = kwargs.get("temperature_c", temperature)
        hum = kwargs.get("humidity_percent", humidity)
        sol = kwargs.get("solar_radiation_wm2", solar_radiation)
        wind = kwargs.get("wind_speed_ms", wind_speed)
        rain = kwargs.get("rainfall_mm", rainfall)

        c_temp, c_hum, c_sol, c_wind, c_rain = self._validate_and_clamp_inputs(
            temp, hum, sol, wind, rain
        )
        memberships = self._fuzzify_inputs(c_temp, c_hum, c_sol, c_wind, c_rain)

        active_rules = []
        consequent_activations = {name: 0.0 for name in self.stress_var.set_names}

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
            if firing_strength > 0.0:
                active_rules.append({
                    "rule_id": rule["id"],
                    "description": rule["desc"],
                    "consequent": rule["consequent"],
                    "weight": float(firing_strength),
                })
            target_term = rule["consequent"]
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
        crisp_stress = float(np.clip(centroid, 0.0, 100.0))

        return {
            "temperature": temp,
            "temperature_clamped": c_temp,
            "humidity": hum,
            "humidity_clamped": c_hum,
            "solar_radiation": sol,
            "solar_radiation_clamped": c_sol,
            "wind_speed": wind,
            "wind_speed_clamped": c_wind,
            "rainfall": rain,
            "rainfall_clamped": c_rain,
            "weather_stress": crisp_stress,
            "temperature_membership": {k: float(v) for k, v in memberships["temperature"].items()},
            "humidity_membership": {k: float(v) for k, v in memberships["humidity"].items()},
            "solar_radiation_membership": {k: float(v) for k, v in memberships["solar_radiation"].items()},
            "wind_speed_membership": {k: float(v) for k, v in memberships["wind_speed"].items()},
            "rainfall_membership": {k: float(v) for k, v in memberships["rainfall"].items()},
            "consequent_activations": consequent_activations,
            "active_rules": active_rules,
            "total_fuzzy_area": total_area,
        }

    def evaluate_array(
        self,
        temperature_arr: np.ndarray,
        humidity_arr: np.ndarray,
        solar_arr: np.ndarray,
        wind_arr: np.ndarray,
        rainfall_arr: np.ndarray,
    ) -> np.ndarray:
        """
        Batch evaluation for simulation timeseries arrays.
        """
        t_flat = np.asarray(temperature_arr, dtype=float).flatten()
        h_flat = np.asarray(humidity_arr, dtype=float).flatten()
        s_flat = np.asarray(solar_arr, dtype=float).flatten()
        w_flat = np.asarray(wind_arr, dtype=float).flatten()
        r_flat = np.asarray(rainfall_arr, dtype=float).flatten()

        n = len(t_flat)
        if not (len(h_flat) == n and len(s_flat) == n and len(w_flat) == n and len(r_flat) == n):
            raise ValueError("All input arrays to evaluate_array must have identical dimensions.")

        results = np.zeros(n, dtype=float)
        for i in range(n):
            results[i] = self.evaluate(t_flat[i], h_flat[i], s_flat[i], w_flat[i], r_flat[i])

        return results.reshape(temperature_arr.shape)

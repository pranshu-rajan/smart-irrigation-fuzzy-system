"""
Parameter Space Definition, Bounds, Normalization, and Repair for Phase 14 PSO.

Defines the 18-dimensional optimization vector targeting the Main Irrigation FIS:
- Moisture Error membership functions (5 parameters)
- Soil Stress membership functions (4 parameters)
- Water Demand membership functions (5 parameters)
- Irrigation Command output membership functions (4 parameters)

Provides:
- Bidirectional mapping between normalized [0, 1]^D and physical bounds.
- Deterministic repair mechanism ensuring valid membership function ordering:
  a <= b <= c for triangular MFs and a <= b <= c <= d for trapezoidal MFs.
- Builder method to construct a valid custom MainIrrigationFIS instance.
"""

from typing import Dict, List, Tuple, Any, Optional
import copy
import numpy as np
from pydantic import BaseModel, Field

from fuzzy_engine.variables import FuzzyUniverse, MembershipSet, FuzzyVariable
from fuzzy_engine.irrigation import MainIrrigationFIS
from fuzzy_engine.universes import get_fuzzy_variable


class ParameterSpec(BaseModel):
    """Specification of a single optimizable parameter."""
    name: str
    variable_name: str
    set_name: str
    param_index: int
    min_val: float
    max_val: float
    baseline_val: float
    description: str


# 18 Tunable Parameters for MainIrrigationFIS
PARAM_SPECS: List[ParameterSpec] = [
    # --- 1. Moisture Error (5 parameters) ---
    ParameterSpec(
        name="error_large_neg_d",
        variable_name="moisture_error",
        set_name="large_negative",
        param_index=3,
        min_val=-25.0,
        max_val=-5.0,
        baseline_val=-10.0,
        description="Right shoulder cutoff of Large Negative moisture error trapmf",
    ),
    ParameterSpec(
        name="error_neg_center",
        variable_name="moisture_error",
        set_name="negative",
        param_index=1,
        min_val=-14.0,
        max_val=-2.0,
        baseline_val=-7.5,
        description="Peak center of Negative moisture error trimf",
    ),
    ParameterSpec(
        name="error_zero_halfwidth",
        variable_name="moisture_error",
        set_name="zero",
        param_index=2,
        min_val=2.0,
        max_val=8.0,
        baseline_val=5.0,
        description="Half-width of Zero moisture error trimf [-w, 0, w]",
    ),
    ParameterSpec(
        name="error_pos_center",
        variable_name="moisture_error",
        set_name="positive",
        param_index=1,
        min_val=2.0,
        max_val=14.0,
        baseline_val=7.5,
        description="Peak center of Positive moisture error trimf",
    ),
    ParameterSpec(
        name="error_large_pos_a",
        variable_name="moisture_error",
        set_name="large_positive",
        param_index=0,
        min_val=5.0,
        max_val=25.0,
        baseline_val=10.0,
        description="Left shoulder onset of Large Positive moisture error trapmf",
    ),

    # --- 2. Soil Stress (4 parameters) ---
    ParameterSpec(
        name="soil_stress_low_d",
        variable_name="soil_stress",
        set_name="low",
        param_index=3,
        min_val=20.0,
        max_val=45.0,
        baseline_val=35.0,
        description="Right shoulder cutoff of Low soil stress trapmf",
    ),
    ParameterSpec(
        name="soil_stress_mod_center",
        variable_name="soil_stress",
        set_name="moderate",
        param_index=1,
        min_val=35.0,
        max_val=55.0,
        baseline_val=45.0,
        description="Peak center of Moderate soil stress trimf",
    ),
    ParameterSpec(
        name="soil_stress_high_center",
        variable_name="soil_stress",
        set_name="high",
        param_index=1,
        min_val=65.0,
        max_val=85.0,
        baseline_val=75.0,
        description="Peak center of High soil stress trimf",
    ),
    ParameterSpec(
        name="soil_stress_vhigh_a",
        variable_name="soil_stress",
        set_name="very_high",
        param_index=0,
        min_val=65.0,
        max_val=85.0,
        baseline_val=75.0,
        description="Left shoulder onset of Very High soil stress trapmf",
    ),

    # --- 3. Water Demand (5 parameters) ---
    ParameterSpec(
        name="demand_vlow_d",
        variable_name="water_demand",
        set_name="very_low",
        param_index=3,
        min_val=15.0,
        max_val=35.0,
        baseline_val=25.0,
        description="Right shoulder cutoff of Very Low water demand trapmf",
    ),
    ParameterSpec(
        name="demand_low_center",
        variable_name="water_demand",
        set_name="low",
        param_index=1,
        min_val=20.0,
        max_val=40.0,
        baseline_val=30.0,
        description="Peak center of Low water demand trimf",
    ),
    ParameterSpec(
        name="demand_mod_center",
        variable_name="water_demand",
        set_name="moderate",
        param_index=1,
        min_val=40.0,
        max_val=60.0,
        baseline_val=50.0,
        description="Peak center of Moderate water demand trimf",
    ),
    ParameterSpec(
        name="demand_high_center",
        variable_name="water_demand",
        set_name="high",
        param_index=1,
        min_val=60.0,
        max_val=80.0,
        baseline_val=70.0,
        description="Peak center of High water demand trimf",
    ),
    ParameterSpec(
        name="demand_vhigh_a",
        variable_name="water_demand",
        set_name="very_high",
        param_index=0,
        min_val=65.0,
        max_val=85.0,
        baseline_val=75.0,
        description="Left shoulder onset of Very High water demand trapmf",
    ),

    # --- 4. Irrigation Command Output (4 parameters) ---
    ParameterSpec(
        name="cmd_off_d",
        variable_name="irrigation_command",
        set_name="off",
        param_index=3,
        min_val=8.0,
        max_val=22.0,
        baseline_val=15.0,
        description="Right shoulder cutoff of Off command trapmf",
    ),
    ParameterSpec(
        name="cmd_low_center",
        variable_name="irrigation_command",
        set_name="low",
        param_index=1,
        min_val=18.0,
        max_val=35.0,
        baseline_val=25.0,
        description="Peak center of Low command trimf",
    ),
    ParameterSpec(
        name="cmd_mod_center",
        variable_name="irrigation_command",
        set_name="moderate",
        param_index=1,
        min_val=40.0,
        max_val=60.0,
        baseline_val=50.0,
        description="Peak center of Moderate command trimf",
    ),
    ParameterSpec(
        name="cmd_high_center",
        variable_name="irrigation_command",
        set_name="high",
        param_index=1,
        min_val=65.0,
        max_val=85.0,
        baseline_val=75.0,
        description="Peak center of High command trimf",
    ),
]


class FuzzyParameterSpace:
    """
    Manages the 18-dimensional parameter space, normalization, clamping,
    monotonic repair, and conversion into executable MainIrrigationFIS instances.
    """

    def __init__(self, specs: Optional[List[ParameterSpec]] = None) -> None:
        self.specs = specs or PARAM_SPECS
        self.dim = len(self.specs)
        self.names = [s.name for s in self.specs]
        self.lower_bounds = np.array([s.min_val for s in self.specs], dtype=float)
        self.upper_bounds = np.array([s.max_val for s in self.specs], dtype=float)
        self.baseline_values = np.array([s.baseline_val for s in self.specs], dtype=float)

    def normalize(self, theta: np.ndarray) -> np.ndarray:
        """Map physical parameters to normalized [0, 1]^D coordinates."""
        theta_clamped = np.clip(theta, self.lower_bounds, self.upper_bounds)
        return (theta_clamped - self.lower_bounds) / (self.upper_bounds - self.lower_bounds)

    def denormalize(self, x: np.ndarray) -> np.ndarray:
        """Map normalized [0, 1]^D coordinates to physical parameters."""
        x_clamped = np.clip(x, 0.0, 1.0)
        return self.lower_bounds + x_clamped * (self.upper_bounds - self.lower_bounds)

    def get_baseline_normalized(self) -> np.ndarray:
        """Get baseline configuration in normalized [0, 1]^D vector."""
        return self.normalize(self.baseline_values)

    def repair_and_validate(self, theta: np.ndarray) -> np.ndarray:
        """
        Repair parameter vector to strictly guarantee:
        1. Bounds clamping: lower_bounds <= theta <= upper_bounds.
        2. Monotonicity of MF coordinates: a <= b <= c (trimf) and a <= b <= c <= d (trapmf).
        3. Prevention of degenerate zero-width sets or inverted fuzzy partitions.
        """
        repaired = np.clip(theta, self.lower_bounds, self.upper_bounds).copy()

        # Group by variable and enforce internal consistency
        # Moisture error Zero halfwidth
        w = max(2.0, min(8.0, repaired[2]))
        repaired[2] = w

        # Moisture error negative center must be < 0
        repaired[1] = min(-w * 0.5, repaired[1])

        # Moisture error positive center must be > 0
        repaired[3] = max(w * 0.5, repaired[3])

        # Moisture error large negative shoulder d <= neg_center
        repaired[0] = min(repaired[1] - 1.0, repaired[0])

        # Moisture error large positive shoulder a >= pos_center
        repaired[4] = max(repaired[3] + 1.0, repaired[4])

        # Soil stress ordering: low_d < mod_center < high_center < vhigh_a
        # low_d: [20, 45], mod_c: [35, 55], high_c: [65, 85], vhigh_a: [65, 85]
        if repaired[5] >= repaired[6]:
            repaired[5] = repaired[6] - 2.0
        if repaired[6] >= repaired[7]:
            repaired[6] = repaired[7] - 2.0

        # Water demand ordering
        # vlow_d < low_c < mod_c < high_c
        if repaired[9] >= repaired[10]:
            repaired[9] = repaired[10] - 2.0
        if repaired[10] >= repaired[11]:
            repaired[10] = repaired[11] - 2.0
        if repaired[11] >= repaired[12]:
            repaired[11] = repaired[12] - 2.0

        # Command output ordering
        # off_d < low_c < mod_c < high_c
        if repaired[14] >= repaired[15]:
            repaired[14] = repaired[15] - 2.0
        if repaired[15] >= repaired[16]:
            repaired[15] = repaired[16] - 2.0
        if repaired[16] >= repaired[17]:
            repaired[16] = repaired[17] - 2.0

        # Final bounds safety
        repaired = np.clip(repaired, self.lower_bounds, self.upper_bounds)
        return repaired

    def build_fis(self, theta: np.ndarray, resolution: int = 501) -> MainIrrigationFIS:
        """
        Construct a fully configured MainIrrigationFIS instance with membership functions
        parameterized by the given physical parameter vector theta.
        """
        repaired = self.repair_and_validate(theta)

        # 1. Build Moisture Error Variable
        # Baseline: Large Negative [-30, -30, -20, -10], Negative [-15, -7.5, 0], Zero [-5, 0, 5], Positive [0, 7.5, 15], Large Positive [10, 20, 30, 30]
        w_err = float(repaired[2])
        neg_c = float(repaired[1])
        pos_c = float(repaired[3])
        ln_d = float(repaired[0])
        lp_a = float(repaired[4])

        u_err = FuzzyUniverse(min_val=-30.0, max_val=30.0, resolution=0.2)
        err_sets = {
            "large_negative": MembershipSet(
                name="large_negative", display_name="Large Negative",
                mf_type="trapezoidal", params=[-30.0, -30.0, min(-20.0, ln_d - 2.0), ln_d]
            ),
            "negative": MembershipSet(
                name="negative", display_name="Negative",
                mf_type="triangular", params=[min(-15.0, neg_c - 5.0), neg_c, 0.0]
            ),
            "zero": MembershipSet(
                name="zero", display_name="Zero",
                mf_type="triangular", params=[-w_err, 0.0, w_err]
            ),
            "positive": MembershipSet(
                name="positive", display_name="Positive",
                mf_type="triangular", params=[0.0, pos_c, max(15.0, pos_c + 5.0)]
            ),
            "large_positive": MembershipSet(
                name="large_positive", display_name="Large Positive",
                mf_type="trapezoidal", params=[lp_a, max(20.0, lp_a + 2.0), 30.0, 30.0]
            ),
        }
        var_err = FuzzyVariable(name="moisture_error", display_name="Moisture Tracking Error", unit="%", universe=u_err, sets=err_sets)

        # 2. Build Soil Stress Variable
        # Baseline: Low [0, 0, 15, 35], Moderate [25, 45, 65], High [55, 75, 85], Very High [75, 85, 100, 100]
        ss_low_d = float(repaired[5])
        ss_mod_c = float(repaired[6])
        ss_high_c = float(repaired[7])
        ss_vh_a = float(repaired[8])

        u_ss = FuzzyUniverse(min_val=0.0, max_val=100.0, resolution=0.5)
        ss_sets = {
            "low": MembershipSet(name="low", display_name="Low", mf_type="trapezoidal", params=[0.0, 0.0, 15.0, ss_low_d]),
            "moderate": MembershipSet(name="moderate", display_name="Moderate", mf_type="triangular", params=[max(0.0, ss_mod_c - 20.0), ss_mod_c, min(100.0, ss_mod_c + 20.0)]),
            "high": MembershipSet(name="high", display_name="High", mf_type="triangular", params=[max(0.0, ss_high_c - 20.0), ss_high_c, min(100.0, ss_high_c + 10.0)]),
            "very_high": MembershipSet(name="very_high", display_name="Very High", mf_type="trapezoidal", params=[ss_vh_a, max(ss_vh_a + 5.0, 85.0), 100.0, 100.0]),
        }
        var_ss = FuzzyVariable(name="soil_stress", display_name="Soil Moisture Stress", unit="%", universe=u_ss, sets=ss_sets)

        # 3. Build Water Demand Variable
        # Baseline: Very Low [0, 0, 10, 25], Low [15, 30, 45], Moderate [35, 50, 65], High [55, 70, 85], Very High [75, 90, 100, 100]
        wd_vl_d = float(repaired[9])
        wd_l_c = float(repaired[10])
        wd_m_c = float(repaired[11])
        wd_h_c = float(repaired[12])
        wd_vh_a = float(repaired[13])

        u_wd = FuzzyUniverse(min_val=0.0, max_val=100.0, resolution=0.5)
        wd_sets = {
            "very_low": MembershipSet(name="very_low", display_name="Very Low", mf_type="trapezoidal", params=[0.0, 0.0, 10.0, wd_vl_d]),
            "low": MembershipSet(name="low", display_name="Low", mf_type="triangular", params=[max(0.0, wd_l_c - 15.0), wd_l_c, min(100.0, wd_l_c + 15.0)]),
            "moderate": MembershipSet(name="moderate", display_name="Moderate", mf_type="triangular", params=[max(0.0, wd_m_c - 15.0), wd_m_c, min(100.0, wd_m_c + 15.0)]),
            "high": MembershipSet(name="high", display_name="High", mf_type="triangular", params=[max(0.0, wd_h_c - 15.0), wd_h_c, min(100.0, wd_h_c + 15.0)]),
            "very_high": MembershipSet(name="very_high", display_name="Very High", mf_type="trapezoidal", params=[wd_vh_a, max(wd_vh_a + 5.0, 90.0), 100.0, 100.0]),
        }
        var_wd = FuzzyVariable(name="water_demand", display_name="Crop Water Demand", unit="%", universe=u_wd, sets=wd_sets)

        # 4. Build Command Output Variable
        # Baseline: Off [0, 0, 5, 15], Low [10, 25, 40], Moderate [30, 50, 70], High [60, 75, 90], Maximum [80, 90, 100, 100]
        cmd_off_d = float(repaired[14])
        cmd_l_c = float(repaired[15])
        cmd_m_c = float(repaired[16])
        cmd_h_c = float(repaired[17])

        u_cmd = FuzzyUniverse(min_val=0.0, max_val=100.0, resolution=0.2)
        cmd_sets = {
            "off": MembershipSet(name="off", display_name="Off", mf_type="trapezoidal", params=[0.0, 0.0, 5.0, cmd_off_d]),
            "low": MembershipSet(name="low", display_name="Low", mf_type="triangular", params=[max(0.0, cmd_l_c - 15.0), cmd_l_c, min(100.0, cmd_l_c + 15.0)]),
            "moderate": MembershipSet(name="moderate", display_name="Moderate", mf_type="triangular", params=[max(0.0, cmd_m_c - 20.0), cmd_m_c, min(100.0, cmd_m_c + 20.0)]),
            "high": MembershipSet(name="high", display_name="High", mf_type="triangular", params=[max(0.0, cmd_h_c - 15.0), cmd_h_c, min(100.0, cmd_h_c + 15.0)]),
            "maximum": MembershipSet(name="maximum", display_name="Maximum", mf_type="trapezoidal", params=[max(cmd_h_c + 5.0, 80.0), 90.0, 100.0, 100.0]),
        }
        var_cmd = FuzzyVariable(name="irrigation_command", display_name="Irrigation Command Output", unit="%", universe=u_cmd, sets=cmd_sets, role="output")

        # Weather stress variable remains baseline (expert meteorological model)
        var_ws = get_fuzzy_variable("weather_stress")

        return MainIrrigationFIS(
            resolution=resolution,
            soil_stress_var=var_ss,
            weather_stress_var=var_ws,
            water_demand_var=var_wd,
            moisture_error_var=var_err,
            command_var=var_cmd,
        )

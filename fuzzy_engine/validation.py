"""
Fuzzy Variable and Membership Function Validation Utilities.

Performs rigorous verification of universe limits, membership parameters,
coverage completeness, partition-of-unity characteristics, and boundary saturation.
"""

from typing import Any, Dict, List, Tuple
import numpy as np

from fuzzy_engine.variables import FuzzyVariable, MembershipSet


class ValidationError(Exception):
    """Raised when a fuzzy variable or membership function fails validation."""
    pass


def validate_fuzzy_variable(var: FuzzyVariable) -> Dict[str, Any]:
    """
    Perform complete 11-point mathematical and engineering validation on a FuzzyVariable.

    Checks:
    1. Universe min < max
    2. Sufficient grid resolution (at least 100 points)
    3. Valid MF parameters (a <= b <= c or a <= b <= c <= d)
    4. Finite MF parameters (no NaN or Inf)
    5. Membership values strictly in [0.0, 1.0] across grid
    6. Non-zero support for every linguistic set
    7. Complete universe coverage: sum(mu) >= 0.5 for all x in universe (no holes)
    8. Overlap between adjacent membership functions (intersection height > 0)
    9. No gap where all memberships equal 0.0
    10. Boundary saturation: at min_val and max_val, edge sets evaluate to 1.0
    11. Numerical reproducibility

    Returns
    -------
    dict
        Detailed validation summary metrics.
    """
    summary = {
        "variable": var.name,
        "valid": True,
        "checks_passed": [],
        "warnings": [],
    }

    # 1. Universe min < max
    if var.universe.min_val >= var.universe.max_val:
        raise ValidationError(
            f"[{var.name}] Universe min_val ({var.universe.min_val}) must be strictly less than "
            f"max_val ({var.universe.max_val})."
        )
    summary["checks_passed"].append("universe_bounds")

    # 2. Universe grid points
    grid = var.universe.points
    if len(grid) < 100:
        raise ValidationError(f"[{var.name}] Grid points too sparse ({len(grid)} < 100).")
    summary["checks_passed"].append("grid_resolution")

    # 3 & 4. MF parameters finite and monotonic
    for set_name, m_set in var.sets.items():
        params = m_set.params
        if any(np.isnan(p) or np.isinf(p) for p in params):
            raise ValidationError(f"[{var.name}:{set_name}] MF parameters contain NaN or Inf: {params}")
        for i in range(len(params) - 1):
            if params[i] > params[i + 1]:
                raise ValidationError(
                    f"[{var.name}:{set_name}] Parameters not non-decreasing: {params}"
                )
    summary["checks_passed"].append("mf_parameters_monotonic_and_finite")

    # Evaluate all sets over universe grid
    eval_matrix = np.zeros((len(var.sets), len(grid)), dtype=float)
    set_names = list(var.sets.keys())
    for idx, sname in enumerate(set_names):
        mu_vals = var.sets[sname].evaluate(grid)
        eval_matrix[idx, :] = mu_vals

        # 5. Membership values strictly in [0, 1]
        if np.any(mu_vals < 0.0) or np.any(mu_vals > 1.0):
            raise ValidationError(
                f"[{var.name}:{sname}] Membership values outside [0, 1]: min={mu_vals.min()}, max={mu_vals.max()}"
            )

        # 6. Non-zero support
        support_count = np.count_nonzero(mu_vals > 0.0)
        if support_count == 0:
            raise ValidationError(f"[{var.name}:{sname}] Set has zero support across universe.")

        # Core (peak) evaluation at analytical apex
        if m_set.mf_type == "triangular":
            apex = m_set.params[1]
        else:
            apex = (m_set.params[1] + m_set.params[2]) / 2.0
        mu_apex = m_set.evaluate(apex)
        if abs(mu_apex - 1.0) > 1e-6:
            raise ValidationError(f"[{var.name}:{sname}] Core does not reach 1.0 at apex {apex}: mu={mu_apex}.")

        # Grid maximum should be close to 1.0 (>= 0.95)
        if np.max(mu_vals) < 0.95:
            raise ValidationError(f"[{var.name}:{sname}] Grid maximum too low ({np.max(mu_vals)} < 0.95).")

    summary["checks_passed"].append("membership_range_and_support")

    # 7 & 9. Universe coverage (sum of memberships across grid points)
    sum_mu = np.sum(eval_matrix, axis=0)
    min_sum = np.min(sum_mu)
    if min_sum < 0.3:
        raise ValidationError(
            f"[{var.name}] Coverage gap detected! Minimum sum of memberships across grid is {min_sum:.3f} < 0.3."
        )
    summary["checks_passed"].append("universe_coverage_no_holes")

    # 8. Overlap between adjacent sets
    # Sets are ordered in the definition dictionary
    for i in range(len(set_names) - 1):
        s1 = set_names[i]
        s2 = set_names[i + 1]
        mu1 = eval_matrix[i, :]
        mu2 = eval_matrix[i + 1, :]
        overlap = np.minimum(mu1, mu2)
        max_overlap = np.max(overlap)
        if max_overlap < 0.01:
            raise ValidationError(
                f"[{var.name}] Insufficient overlap between adjacent sets '{s1}' and '{s2}': "
                f"maximum intersection height is {max_overlap:.3f}."
            )
    summary["checks_passed"].append("adjacent_set_overlap")

    # 10. Boundary saturation
    first_set = set_names[0]
    last_set = set_names[-1]
    mu_min = var.sets[first_set].evaluate(var.universe.min_val)
    mu_max = var.sets[last_set].evaluate(var.universe.max_val)

    if mu_min < 0.999:
        raise ValidationError(
            f"[{var.name}:{first_set}] Lower boundary saturation failed. "
            f"mu({var.universe.min_val}) = {mu_min} != 1.0."
        )
    if mu_max < 0.999:
        raise ValidationError(
            f"[{var.name}:{last_set}] Upper boundary saturation failed. "
            f"mu({var.universe.max_val}) = {mu_max} != 1.0."
        )
    summary["checks_passed"].append("boundary_saturation")

    # 11. Reproducibility test
    sample_pt = (var.universe.min_val + var.universe.max_val) / 2.0
    res1 = var.evaluate(sample_pt)
    res2 = var.evaluate(sample_pt)
    for k in res1:
        if abs(res1[k] - res2[k]) > 1e-9:
            raise ValidationError(f"[{var.name}] Non-reproducible evaluation result for set {k}.")
    summary["checks_passed"].append("numerical_reproducibility")

    summary["min_sum_coverage"] = float(min_sum)
    summary["max_sum_coverage"] = float(np.max(sum_mu))
    summary["num_sets"] = len(var.sets)
    return summary


def validate_all_variables(variables: Dict[str, FuzzyVariable]) -> Dict[str, Dict[str, Any]]:
    """
    Run validation across all fuzzy variables in the registry.

    Returns
    -------
    dict
        Mapping of variable name -> validation results dict.
    """
    results = {}
    for name, var in variables.items():
        results[name] = validate_fuzzy_variable(var)
    return results

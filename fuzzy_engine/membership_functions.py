"""
Linguistic variables, universes of discourse, and membership function definitions.

Uses triangular and trapezoidal membership functions for interpretable Mamdani inference.
Re-exports mathematical functions from fuzzy_engine.membership for backward compatibility.
"""

from fuzzy_engine.membership import triangular_mf, trapezoidal_mf

__all__ = ["triangular_mf", "trapezoidal_mf"]

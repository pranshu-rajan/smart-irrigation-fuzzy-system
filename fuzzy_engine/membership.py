"""
Mathematical Membership Function Definitions.

Implements pure NumPy vectorized and scalar triangular and trapezoidal
membership functions according to standard fuzzy set theory.
Compatible with Python 3.11 and scikit-fuzzy standards.
"""

from typing import Union
import numpy as np


def triangular_mf(
    x: Union[float, int, np.ndarray],
    a: float,
    b: float,
    c: float,
) -> Union[float, np.ndarray]:
    """
    Evaluate a triangular fuzzy membership function.

    Formula:
        f(x; a, b, c) = 0,                        x <= a
                      = (x - a) / (b - a),        a < x < b
                      = 1,                        x == b
                      = (c - x) / (c - b),        b < x < c
                      = 0,                        x >= c

    Parameters
    ----------
    x : float or np.ndarray
        Point(s) at which to evaluate membership.
    a : float
        Left foot (support start, mu=0).
    b : float
        Peak / apex (core, mu=1).
    c : float
        Right foot (support end, mu=0).

    Returns
    -------
    float or np.ndarray
        Membership degree(s) in [0.0, 1.0].
    """
    if not (a <= b <= c):
        raise ValueError(f"Triangular MF parameters must satisfy a <= b <= c. Got a={a}, b={b}, c={c}")

    is_scalar = np.isscalar(x)
    x_arr = np.asarray(x, dtype=float)

    # Check for NaN / Inf in input
    if np.any(np.isnan(x_arr)) or np.any(np.isinf(x_arr)):
        raise ValueError("Membership function input x cannot contain NaN or Inf values.")

    # Initialize output array of zeros
    y = np.zeros_like(x_arr, dtype=float)

    # Left slope: a < x < b
    if a != b:
        left_mask = (a < x_arr) & (x_arr < b)
        y[left_mask] = (x_arr[left_mask] - a) / (b - a)

    # Apex: x == b
    peak_mask = (x_arr == b)
    y[peak_mask] = 1.0

    # Right slope: b < x < c
    if b != c:
        right_mask = (b < x_arr) & (x_arr < c)
        y[right_mask] = (c - x_arr[right_mask]) / (c - b)

    # Clip to [0, 1] for numerical safety
    y = np.clip(y, 0.0, 1.0)

    return float(y.item()) if is_scalar else y


def trapezoidal_mf(
    x: Union[float, int, np.ndarray],
    a: float,
    b: float,
    c: float,
    d: float,
) -> Union[float, np.ndarray]:
    """
    Evaluate a trapezoidal fuzzy membership function.

    Formula:
        f(x; a, b, c, d) = 0,                        x <= a
                         = (x - a) / (b - a),        a < x < b
                         = 1,                        b <= x <= c
                         = (d - x) / (d - c),        c < x < d
                         = 0,                        x >= d

    Parameters
    ----------
    x : float or np.ndarray
        Point(s) at which to evaluate membership.
    a : float
        Left foot (support start, mu=0).
    b : float
        Left plateau start (core start, mu=1).
    c : float
        Right plateau end (core end, mu=1).
    d : float
        Right foot (support end, mu=0).

    Returns
    -------
    float or np.ndarray
        Membership degree(s) in [0.0, 1.0].
    """
    if not (a <= b <= c <= d):
        raise ValueError(f"Trapezoidal MF parameters must satisfy a <= b <= c <= d. Got a={a}, b={b}, c={c}, d={d}")

    is_scalar = np.isscalar(x)
    x_arr = np.asarray(x, dtype=float)

    # Check for NaN / Inf in input
    if np.any(np.isnan(x_arr)) or np.any(np.isinf(x_arr)):
        raise ValueError("Membership function input x cannot contain NaN or Inf values.")

    # Initialize output array of zeros
    y = np.zeros_like(x_arr, dtype=float)

    # Left slope: a < x < b
    if a != b:
        left_mask = (a < x_arr) & (x_arr < b)
        y[left_mask] = (x_arr[left_mask] - a) / (b - a)

    # Plateau (core): b <= x <= c
    plateau_mask = (b <= x_arr) & (x_arr <= c)
    y[plateau_mask] = 1.0

    # Right slope: c < x < d
    if c != d:
        right_mask = (c < x_arr) & (x_arr < d)
        y[right_mask] = (d - x_arr[right_mask]) / (d - c)

    # Clip to [0, 1] for numerical safety
    y = np.clip(y, 0.0, 1.0)

    return float(y.item()) if is_scalar else y

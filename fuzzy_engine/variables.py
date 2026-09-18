"""
Fuzzy Variable, Universe of Discourse, and Membership Set Definitions.

Provides object-oriented abstractions for fuzzy variables, universes of discourse,
and linguistic membership sets according to Mamdani fuzzy logic principles.
"""

from typing import Dict, List, Optional, Union
import numpy as np

from fuzzy_engine.membership import triangular_mf, trapezoidal_mf


class FuzzyUniverse:
    """
    Continuous Universe of Discourse for a fuzzy variable with discrete evaluation support.

    Parameters
    ----------
    min_val : float
        Lower bound of the physical universe.
    max_val : float
        Upper bound of the physical universe.
    resolution : float, optional
        Step size between discrete evaluation points. Default is None.
    num_points : int, optional
        Total number of evaluation points across [min_val, max_val]. Default is 501.
    """

    def __init__(
        self,
        min_val: float,
        max_val: float,
        resolution: Optional[float] = None,
        num_points: int = 501,
    ) -> None:
        if min_val >= max_val:
            raise ValueError(f"Universe min_val must be strictly less than max_val. Got {min_val} >= {max_val}")
        if num_points < 2:
            raise ValueError(f"Universe num_points must be at least 2. Got {num_points}")

        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.resolution = float(resolution) if resolution is not None else None
        self._num_points = int(num_points)

    @property
    def range_span(self) -> float:
        """Physical range span (max_val - min_val)."""
        return self.max_val - self.min_val

    @property
    def points(self) -> np.ndarray:
        """Discrete evaluation grid points spanning [min_val, max_val]."""
        if self.resolution is not None and self.resolution > 0:
            # Calculate points matching exact resolution steps with endpoint inclusive
            steps = int(np.round((self.max_val - self.min_val) / self.resolution))
            return np.linspace(self.min_val, self.max_val, steps + 1)
        return np.linspace(self.min_val, self.max_val, self._num_points)

    def clamp(self, x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Safely clamp input value(s) to universe bounds [min_val, max_val].
        Rejects NaN and infinite values with a clear ValueError.
        """
        is_scalar = np.isscalar(x)
        x_arr = np.asarray(x, dtype=float)

        if np.any(np.isnan(x_arr)) or np.any(np.isinf(x_arr)):
            raise ValueError(f"Cannot clamp invalid numerical values (NaN or Inf): {x}")

        clamped = np.clip(x_arr, self.min_val, self.max_val)
        return float(clamped.item()) if is_scalar else clamped

    def normalize(self, x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Normalize physical value(s) linearly to [0.0, 1.0].
        Automatically clamps inputs to universe boundaries.
        """
        clamped = self.clamp(x)
        is_scalar = np.isscalar(clamped)
        norm_val = (np.asarray(clamped, dtype=float) - self.min_val) / self.range_span
        norm_val = np.clip(norm_val, 0.0, 1.0)
        return float(norm_val.item()) if is_scalar else norm_val

    def denormalize(self, y: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Denormalize value(s) from [0.0, 1.0] back to physical universe [min_val, max_val].
        Rejects NaN and infinite values.
        """
        is_scalar = np.isscalar(y)
        y_arr = np.asarray(y, dtype=float)

        if np.any(np.isnan(y_arr)) or np.any(np.isinf(y_arr)):
            raise ValueError(f"Cannot denormalize invalid values (NaN or Inf): {y}")

        y_clamped = np.clip(y_arr, 0.0, 1.0)
        phys_val = self.min_val + y_clamped * self.range_span
        return float(phys_val.item()) if is_scalar else phys_val

    def __repr__(self) -> str:
        return f"FuzzyUniverse(min={self.min_val}, max={self.max_val}, resolution={self.resolution})"


class MembershipSet:
    """
    A single linguistic term / membership set defined on a universe of discourse.

    Parameters
    ----------
    name : str
        Machine identifier (e.g. 'very_dry', 'adequate').
    display_name : str
        Human-readable title (e.g. 'Very Dry', 'Adequate').
    mf_type : str
        Type of membership function: 'triangular' or 'trapezoidal'.
    params : list of float
        Parameters [a, b, c] or [a, b, c, d].
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        mf_type: str,
        params: List[float],
    ) -> None:
        mf_type_clean = mf_type.lower().strip()
        if mf_type_clean not in ("triangular", "trapezoidal"):
            raise ValueError(f"Unsupported mf_type: '{mf_type}'. Must be 'triangular' or 'trapezoidal'.")

        if mf_type_clean == "triangular" and len(params) != 3:
            raise ValueError(f"Triangular MF requires exactly 3 parameters [a, b, c]. Got {params}")
        if mf_type_clean == "trapezoidal" and len(params) != 4:
            raise ValueError(f"Trapezoidal MF requires exactly 4 parameters [a, b, c, d]. Got {params}")

        self.name = name
        self.display_name = display_name
        self.mf_type = mf_type_clean
        self.params = [float(p) for p in params]

        # Verify parameter monotonicity
        for i in range(len(self.params) - 1):
            if self.params[i] > self.params[i + 1]:
                raise ValueError(f"Parameters must be non-decreasing for set '{name}': {self.params}")

    def evaluate(self, x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Evaluate degree of membership mu(x) in [0.0, 1.0].
        """
        if self.mf_type == "triangular":
            return triangular_mf(x, self.params[0], self.params[1], self.params[2])
        elif self.mf_type == "trapezoidal":
            return trapezoidal_mf(x, self.params[0], self.params[1], self.params[2], self.params[3])
        else:
            raise ValueError(f"Unknown mf_type: {self.mf_type}")

    def __repr__(self) -> str:
        return f"MembershipSet(name='{self.name}', type='{self.mf_type}', params={self.params})"


class FuzzyVariable:
    """
    Complete Fuzzy Variable definition with universe and linguistic sets.

    Parameters
    ----------
    name : str
        Variable identifier (e.g. 'rsm', 'moisture_error').
    display_name : str
        Human-readable title (e.g. 'Relative Soil Moisture').
    unit : str
        Physical engineering unit (e.g. 'dimensionless (0-1)', '°C', '%').
    universe : FuzzyUniverse
        The associated universe of discourse.
    sets : dict of {str: MembershipSet}
        Dictionary mapping linguistic set names to MembershipSet instances.
    role : str, optional
        Operational role: 'input' or 'output'. Default is 'input'.
    fis_groups : list of str, optional
        The FIS architectures utilizing this variable.
    description : str, optional
        Engineering rationale and context.
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        unit: str,
        universe: FuzzyUniverse,
        sets: Dict[str, MembershipSet],
        role: str = "input",
        fis_groups: Optional[List[str]] = None,
        description: str = "",
    ) -> None:
        if not sets:
            raise ValueError(f"FuzzyVariable '{name}' must have at least one membership set.")

        self.name = name
        self.display_name = display_name
        self.unit = unit
        self.universe = universe
        self.sets = sets
        self.role = role.lower().strip()
        self.fis_groups = fis_groups or []
        self.description = description

    def evaluate(self, x: Union[float, int, np.ndarray], clamp: bool = True) -> Dict[str, Union[float, np.ndarray]]:
        """
        Evaluate membership degrees for all linguistic terms of this variable.

        Parameters
        ----------
        x : float, int, or np.ndarray
            Input value(s) in physical units.
        clamp : bool, optional
            Whether to clamp inputs to universe boundaries prior to evaluation.
            Default is True.

        Returns
        -------
        dict of {str: float or np.ndarray}
            Mapping of linguistic set name -> membership degree(s).
        """
        eval_x = self.universe.clamp(x) if clamp else x
        return {term_name: mf_set.evaluate(eval_x) for term_name, mf_set in self.sets.items()}

    def normalize(self, x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
        """Normalize physical value to [0.0, 1.0]."""
        return self.universe.normalize(x)

    def denormalize(self, y: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
        """Denormalize [0.0, 1.0] back to physical universe."""
        return self.universe.denormalize(y)

    def clamp(self, x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
        """Clamp value to universe bounds."""
        return self.universe.clamp(x)

    @property
    def set_names(self) -> List[str]:
        """List of linguistic term names."""
        return list(self.sets.keys())

    def __repr__(self) -> str:
        return (
            f"FuzzyVariable(name='{self.name}', unit='{self.unit}', "
            f"range=[{self.universe.min_val}, {self.universe.max_val}], "
            f"sets={list(self.sets.keys())})"
        )

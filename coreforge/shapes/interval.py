from math import isclose
from typing import Tuple

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL


class Interval:
    """One-dimensional closed interval.

    Parameters
    ----------
    lower : float
        Lower bound of the interval.
    upper : float
        Upper bound of the interval.
    """

    def __init__(self, lower: float, upper: float) -> None:
        assert lower < upper or isclose(lower, upper, rel_tol=TOL), "Interval lower bound must not exceed upper bound."
        self._lower = lower
        self._upper = upper
        self._length = self.upper - self.lower
        self._center = 0.5 * (self.lower + self.upper)

    @property
    def lower(self) -> float:
        return self._lower

    @property
    def upper(self) -> float:
        return self._upper

    @property
    def bounds(self) -> Tuple[float, float]:
        return (self.lower, self.upper)

    @property
    def length(self) -> float:
        return self._length

    @property
    def center(self) -> float:
        return self._center

    def intersects(self,
                   other: "Interval",
                   tolerance: float = TOL) -> bool:
        """Check whether this interval intersects another interval.

        Parameters
        ----------
        other : Interval
            Other interval.
        tolerance : float
            Relative tolerance used when comparing interval endpoints.

        Returns
        -------
        bool
            True if the intervals overlap or touch.
        """
        if self.upper < other.lower and not isclose(self.upper, other.lower, rel_tol=tolerance):
            return False
        if other.upper < self.lower and not isclose(other.upper, self.lower, rel_tol=tolerance):
            return False
        return True

    def contains(self,
                 other: "Interval",
                 tolerance: float = TOL) -> bool:
        """Check whether this interval contains another interval.

        Parameters
        ----------
        other : Interval
            Other interval.
        tolerance : float
            Relative tolerance used when comparing interval endpoints.

        Returns
        -------
        bool
            True if the other interval lies inside this interval.
        """
        lower_ok = other.lower > self.lower or isclose(other.lower, self.lower, rel_tol=tolerance)
        upper_ok = other.upper < self.upper or isclose(other.upper, self.upper, rel_tol=tolerance)
        return lower_ok and upper_ok

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, Interval) and
            isclose(self.lower, other.lower, rel_tol=TOL) and
            isclose(self.upper, other.upper, rel_tol=TOL)
        )

    def __hash__(self) -> int:
        return hash((relative_round(self.lower, TOL), relative_round(self.upper, TOL)))

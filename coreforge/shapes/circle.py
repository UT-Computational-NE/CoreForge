from math import pi, isclose
from typing import Any, Tuple

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.shape import Shape_2D

class Circle(Shape_2D):
    """ A concrete circle channel shape class

    Parameters
    ----------
    r : float
        The radius of the circle (cm)

    Attributes
    ----------
    r : float
        The radius of the circle (cm)
    """

    @property
    def r(self) -> float:
        return self._inner_radius

    def __init__(self, r: float):
        assert r >= 0.
        super().__init__(inner_radius = r,
                         outer_radius = r,
                         area         = pi*r*r)

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Circle)  and
                isclose(self.r, other.r, rel_tol=TOL))

    def __hash__(self) -> int:
        return hash(relative_round(self.r, TOL))

    def make_region(self) -> openmc.Region:
        return -openmc.ZCylinder(r=self.r)

    def contains_point(self,
                       point: Tuple[float, float],
                       center: Tuple[float, float] = (0.0, 0.0),
                       rotation: float = 0.0) -> bool:
        """Check whether a point lies inside the circle.

        Parameters
        ----------
        point : Tuple[float, float]
            The (x, y) point to test.
        center : Tuple[float, float]
            The (x, y) center of the circle.
        rotation : float
            Rotation angle in degrees about the shape center (unused).

        Returns
        -------
        bool
            True if the point lies inside or on the boundary.
        """
        _ = rotation
        dx = point[0] - center[0]
        dy = point[1] - center[1]
        dist_sq = dx * dx + dy * dy
        radius_sq = self.r * self.r
        return dist_sq < radius_sq or isclose(dist_sq, radius_sq, rel_tol=TOL)

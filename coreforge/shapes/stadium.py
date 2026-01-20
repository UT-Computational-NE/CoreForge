from math import pi, isclose
from typing import Any, Tuple

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.shape import Shape_2D
from coreforge.shapes.utils import to_local

class Stadium(Shape_2D):
    """ A concrete stadium channel shape class

    Parameters
    ----------
    r : float
        The radius of the semicircles (cm)
    a : float
        The length of the stadium flat sides (cm)

    Attributes
    ----------
    r : float
        The radius of the semicircles (cm)
    a : float
        The length of the stadium flat sides (cm)
    """

    @property
    def r(self) -> float:
        return self._r

    @property
    def a(self) -> float:
        return self._a

    def __init__(self, r: float, a: float):
        assert r >= 0.
        assert a >= 0.
        self._r   = r
        self._a   = a
        super().__init__(inner_radius = r,
                         outer_radius = a*0.5 + r,
                         area         = pi*r*r + 2*r*a)

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Stadium)            and
                isclose(self.r, other.r, rel_tol=TOL) and
                isclose(self.a, other.a, rel_tol=TOL))

    def __hash__(self) -> int:
        return hash((relative_round(self.r, TOL),
                     relative_round(self.a, TOL)))

    def make_region(self) -> openmc.Region:
        left_circle  = openmc.ZCylinder(x0=-self.a/2., r=self.r)
        right_circle = openmc.ZCylinder(x0= self.a/2., r=self.r)
        rectangle    = openmc.model.RectangularPrism(width=self.a, height=self.r*2.)
        return -left_circle | -right_circle | -rectangle

    def contains_point(self,
                       point: Tuple[float, float],
                       center: Tuple[float, float] = (0.0, 0.0),
                       rotation: float = 0.0) -> bool:
        """Check whether a point lies inside the stadium.

        Parameters
        ----------
        point : Tuple[float, float]
            The (x, y) point to test.
        center : Tuple[float, float]
            The (x, y) center of the stadium.
        rotation : float
            Rotation angle in degrees about the shape center.

        Returns
        -------
        bool
            True if the point lies inside or on the boundary.
        """
        x_local, y_local = to_local(point, center, rotation)

        half_a = 0.5 * self.a
        if abs(x_local) <= half_a and (
            abs(y_local) < self.r or isclose(abs(y_local), self.r, rel_tol=TOL)
        ):
            return True

        for x_center in (-half_a, half_a):
            dx_c = x_local - x_center
            dist_sq = dx_c * dx_c + y_local * y_local
            radius_sq = self.r * self.r
            if dist_sq < radius_sq or isclose(dist_sq, radius_sq, rel_tol=TOL):
                return True

        return False

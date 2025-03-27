from math import pi, isclose
from typing import Any

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

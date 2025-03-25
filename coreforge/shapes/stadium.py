from math import pi, isclose
from typing import Any

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.shape import Shape_2D

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

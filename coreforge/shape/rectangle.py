from math import sqrt, isclose
from typing import Any

import openmc

from coreforge.shape.shape import Shape_2D
from coreforge.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

class Rectangle(Shape_2D):
    """ A concrete rectangle channel shape class

    Attributes
    ----------
    h : float
        The height of the rectangle (cm)
    w : float
        The width of the rectangle (cm)
    """

    @property
    def h(self) -> float:
        return self._h

    @property
    def w(self) -> float:
        return self._w

    def __init__(self, w: float, h: float = None):
        assert(w >= 0.)
        if h is None: h = w
        assert(h >= 0.)
        self._h = h
        self._w = w
        self._i_r = min(h/2., w/2.)
        self._o_r = sqrt(h*h + w*w)
        self._area = h*w

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Rectangle)          and
                isclose(self.h, other.h, rel_tol=TOL) and
                isclose(self.w, other.w, rel_tol=TOL))

    def __hash__(self) -> int:
        return hash((relative_round(self.h, TOL),
                     relative_round(self.w, TOL)))

    def make_region(self) -> openmc.Region:
        return -openmc.model.RectangularPrism(width=self.w, height=self.h)


class Square(Rectangle):
    """ A concrete square block shape class

    Attributes
    ----------
    s : float
        The side length of the square (cm)
    """

    @property
    def s(self) -> float:
        return self._w

    def __init__(self, s: float):
        assert(s >= 0.)
        super().__init__(s)
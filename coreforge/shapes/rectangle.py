from math import sqrt, isclose
from typing import Any

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.shape import Shape_2D

class Rectangle(Shape_2D):
    """ A concrete rectangle channel shape class

    Parameters
    ----------
    h : float
        The height of the rectangle (cm)
    w : float
        The width of the rectangle (cm)

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

    def __init__(self, w: float, h: float):
        assert w >= 0.
        assert h >= 0.
        self._h = h
        self._w = w
        super().__init__(inner_radius = min(h/2., w/2.),
                         outer_radius = 0.5*sqrt(h*h + w*w),
                         area         = h*w)

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

    Parameters
    ----------
    length : float
        The side length of the square (cm)

    Attributes
    ----------
    length : float
        The side length of the square (cm)
    """

    @property
    def length(self) -> float:
        return self._w

    def __init__(self, length: float):
        assert length >= 0.
        super().__init__(length, length)

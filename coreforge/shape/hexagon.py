from math import sqrt, isclose
from typing import Any

import openmc

from coreforge.shape.shape import Shape_2D
from coreforge.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL


class Hexagon(Shape_2D):
    """ A concrete hexagon block shape class

    Attributes
    ----------
    orientation: str
        The orientation of the hexagon, with 'x' meaning that two sides
        are parallel with the x-axis and 'y' meaning that two sides are
        parallel with the y-axis
    """

    @property
    def orientation(self) -> str:
        return self._orientation

    def __init__(self, r: float, orientation: str = 'y'):
        assert(r >= 0.)
        self._i_r  = r
        self._o_r  = r * 2 / sqrt(3.)
        self._area = 3 * self.o_r * self.i_r
        assert(orientation in ['x', 'y'])
        self._orientation = orientation

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Hexagon)                and
                isclose(self.i_r, other.i_r, rel_tol=TOL) and
                self.orientation == other.orientation)

    def __hash__(self) -> int:
        return hash((relative_round(self.i_r, TOL), self.orientation))

    def make_region(self) -> openmc.Region:
        return -openmc.model.HexagonalPrism(edge_length=self._o_r, orientation=self.orientation)


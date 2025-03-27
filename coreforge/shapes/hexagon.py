from math import sqrt, isclose
from typing import Any

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.shape import Shape_2D


class Hexagon(Shape_2D):
    """ A concrete hexagon block shape class

    Parameters
    ----------
    inner_radius : float
        The inner-radius of the hexagon (cm)
    orientation: str
        The orientation of the hexagon, with 'x' meaning that two sides
        are parallel with the x-axis and 'y' meaning that two sides are
        parallel with the y-axis

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

    def __init__(self, inner_radius: float, orientation: str = 'y'):
        assert inner_radius >= 0.
        i_r = inner_radius
        o_r = inner_radius * 2 / sqrt(3.)
        super().__init__(inner_radius = i_r,
                         outer_radius = o_r,
                         area         = 3 * o_r * i_r)

        assert orientation in ['x', 'y']
        self._orientation = orientation


    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Hexagon)                and
                isclose(self.inner_radius, other.inner_radius, rel_tol=TOL) and
                self.orientation == other.orientation)

    def __hash__(self) -> int:
        return hash((relative_round(self.inner_radius, TOL), self.orientation))

    def make_region(self) -> openmc.Region:
        return -openmc.model.HexagonalPrism(edge_length=self._outer_radius, orientation=self.orientation)

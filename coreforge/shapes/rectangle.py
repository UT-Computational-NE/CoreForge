from math import sqrt, isclose
from typing import Any, Tuple

from coreforge.shapes.circle import Circle
import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.shape import Shape_2D
from coreforge.shapes.utils import to_local

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

    def contains_point(self,
                       point: Tuple[float, float],
                       center: Tuple[float, float] = (0.0, 0.0),
                       rotation: float = 0.0) -> bool:
        """Check whether a point lies inside the rectangle.

        Parameters
        ----------
        point : Tuple[float, float]
            The (x, y) point to test.
        center : Tuple[float, float]
            The (x, y) center of the rectangle.
        rotation : float
            Rotation angle in degrees about the shape center.

        Returns
        -------
        bool
            True if the point lies inside or on the boundary.
        """
        x_local, y_local = to_local(point, center, rotation)

        half_w = 0.5 * self.w
        half_h = 0.5 * self.h
        inside_x = (abs(x_local) < half_w or isclose(abs(x_local), half_w, rel_tol=TOL))
        inside_y = (abs(y_local) < half_h or isclose(abs(y_local), half_h, rel_tol=TOL))
        return inside_x and inside_y

    def _intersects_with_circle(self,
                                circle: Circle,
                                rect_center: Tuple[float, float] = (0.0, 0.0),
                                circle_center: Tuple[float, float] = (0.0, 0.0)):
        """Check intersection between this rectangle and a circle.

        Parameters
        ----------
        circle : Circle
            The circle to test.
        rect_center : Tuple[float, float]
            (x, y) center of this rectangle.
        circle_center : Tuple[float, float]
            (x, y) center of the circle.

        Returns
        -------
        bool
            True if the shapes intersect, False otherwise.
        """
        half_w = 0.5 * self.w
        half_h = 0.5 * self.h
        dx = abs(circle_center[0] - rect_center[0]) - half_w
        dy = abs(circle_center[1] - rect_center[1]) - half_h

        dx = max(dx, 0.0)
        dy = max(dy, 0.0)

        dist_sq = dx * dx + dy * dy
        radius_sq = circle.r * circle.r
        return dist_sq < radius_sq or isclose(dist_sq, radius_sq, rel_tol=TOL)


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

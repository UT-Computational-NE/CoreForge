from math import cos, sin, radians, isclose
from typing import List, Tuple

from mpactpy.utils import ROUNDING_RELATIVE_TOLERANCE as TOL


def to_local(point: Tuple[float, float],
             center: Tuple[float, float] = (0.0, 0.0),
             rotation: float = 0.0) -> Tuple[float, float]:
    """Convert a global point to local coordinates for a rotated shape.

    Parameters
    ----------
    point : Tuple[float, float]
        The (x, y) point in global coordinates.
    center : Tuple[float, float]
        The (x, y) center of the shape.
    rotation : float
        Rotation angle in degrees about the shape center.

    Returns
    -------
    Tuple[float, float]
        The (x, y) point in the shape's local coordinates.
    """
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    if rotation:
        theta = radians(rotation)
        cos_t = cos(theta)
        sin_t = sin(theta)
        x_local = dx * cos_t + dy * sin_t
        y_local = -dx * sin_t + dy * cos_t
        return (x_local, y_local)
    return (dx, dy)


def is_convex(vertices: List[Tuple[float, float]]) -> bool:
    """Check whether a polygon defined by vertices is convex.

    Parameters
    ----------
    vertices : List[Tuple[float, float]]
        Ordered (x, y) vertices for the polygon.

    Returns
    -------
    bool
        True if the polygon is convex.
    """
    if len(vertices) < 3:
        return False

    sign = 0
    n = len(vertices)
    for i in range(n):
        v0 = vertices[i]
        v1 = vertices[(i + 1) % n]
        v2 = vertices[(i + 2) % n]
        cross = ((v1[0] - v0[0]) * (v2[1] - v1[1]) -
                 (v1[1] - v0[1]) * (v2[0] - v1[0]))
        if isclose(cross, 0.0, rel_tol=TOL):
            continue
        curr = 1 if cross > 0.0 else -1
        if sign == 0:
            sign = curr
        elif curr != sign:
            return False
    return True

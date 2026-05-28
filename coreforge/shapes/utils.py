from math import cos, sin, radians, isclose, sqrt
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


def equal_volume_ring_radii(outer_radius: float,
                            num_regions: int,
                            inner_radius: float = 0.0) -> List[float]:
    """Return ring outer radii that divide an annulus into equal areas.

    Parameters
    ----------
    outer_radius : float
        Outer radius of the full annulus.
    num_regions : int
        Number of equal-area radial regions.
    inner_radius : float, optional
        Inner radius of the full annulus. Defaults to 0.0.

    Returns
    -------
    List[float]
        Outer radii for each equal-area ring, ordered from inner to outer.
    """
    assert inner_radius >= 0.0, f"inner_radius = {inner_radius}"
    assert outer_radius > inner_radius, (
        f"outer_radius = {outer_radius}, inner_radius = {inner_radius}"
    )
    assert isinstance(num_regions, int), f"num_regions = {num_regions}"
    assert num_regions > 0, f"num_regions = {num_regions}"

    inner_radius_squared = inner_radius * inner_radius
    radial_area_increment = (
        (outer_radius * outer_radius - inner_radius_squared) / num_regions
    )

    return [sqrt(inner_radius_squared + i * radial_area_increment)
            for i in range(1, num_regions + 1)]


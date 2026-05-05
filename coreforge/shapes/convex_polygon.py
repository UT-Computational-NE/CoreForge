from abc import abstractmethod
from math import isclose
from typing import List, Tuple

from mpactpy.utils import ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.circle import Circle
from coreforge.shapes.shape import Shape_2D


class ConvexPolygon(Shape_2D):
    """Base class for convex polygon shapes.

    Subclasses provide ordered boundary vertices. The shared implementation
    uses those vertices for point containment and polygon-polygon intersection.
    """

    @abstractmethod
    def boundary_points(self,
                        center: Tuple[float, float] = (0.0, 0.0),
                        rotation: float = 0.0) -> List[Tuple[float, float]]:
        """Return ordered polygon vertices.

        Parameters
        ----------
        center : Tuple[float, float]
            The (x, y) center of the polygon.
        rotation : float
            Rotation angle in degrees about the polygon center.

        Returns
        -------
        List[Tuple[float, float]]
            Ordered polygon vertices in global coordinates.
        """

    def contains_point(self,
                       point: Tuple[float, float],
                       center: Tuple[float, float] = (0.0, 0.0),
                       rotation: float = 0.0) -> bool:
        """Check whether a point lies inside the polygon.

        Parameters
        ----------
        point : Tuple[float, float]
            The (x, y) point to test.
        center : Tuple[float, float]
            The (x, y) center of the polygon.
        rotation : float
            Rotation angle in degrees about the polygon center.

        Returns
        -------
        bool
            True if the point lies inside or on the boundary.
        """
        vertices = self.boundary_points(center, rotation)
        sign = 0
        for vertex, next_vertex in zip(vertices, vertices[1:] + vertices[:1]):
            cross = ((next_vertex[0] - vertex[0]) * (point[1] - vertex[1]) -
                     (next_vertex[1] - vertex[1]) * (point[0] - vertex[0]))
            if isclose(cross, 0.0, rel_tol=TOL):
                continue
            curr = 1 if cross > 0.0 else -1
            if sign == 0:
                sign = curr
            elif curr != sign:
                return False
        return True

    def _intersects_with_convex_polygon(self,
                                        polygon: "ConvexPolygon",
                                        self_center: Tuple[float, float] = (0.0, 0.0),
                                        other_center: Tuple[float, float] = (0.0, 0.0),
                                        self_rotation: float = 0.0,
                                        other_rotation: float = 0.0):
        """Check intersection between this polygon and another convex polygon.

        This uses the Separating Axis Theorem. Two convex polygons do not
        intersect if at least one axis exists where their projected intervals
        are disjoint. For convex polygons, it is sufficient to test the axes
        normal to the edges of both polygons.

        Parameters
        ----------
        polygon : ConvexPolygon
            The convex polygon to test.
        self_center : Tuple[float, float]
            (x, y) center of this polygon.
        other_center : Tuple[float, float]
            (x, y) center of the other polygon.
        self_rotation : float
            Rotation angle in degrees for this polygon.
        other_rotation : float
            Rotation angle in degrees for the other polygon.

        Returns
        -------
        bool
            True if the polygons intersect, False otherwise.
        """
        self_points = self.boundary_points(self_center, self_rotation)
        other_points = polygon.boundary_points(other_center, other_rotation)

        def axes(vertices: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
            normals = []
            for vertex, next_vertex in zip(vertices, vertices[1:] + vertices[:1]):
                edge_x = next_vertex[0] - vertex[0]
                edge_y = next_vertex[1] - vertex[1]
                normals.append((-edge_y, edge_x))
            return normals

        def projection(vertices: List[Tuple[float, float]],
                       axis: Tuple[float, float]) -> Tuple[float, float]:
            values = [vertex[0] * axis[0] + vertex[1] * axis[1] for vertex in vertices]
            return min(values), max(values)

        for axis in axes(self_points) + axes(other_points):
            min_1, max_1 = projection(self_points, axis)
            min_2, max_2 = projection(other_points, axis)
            if ((max_1 < min_2 and not isclose(max_1, min_2, rel_tol=TOL)) or
                    (max_2 < min_1 and not isclose(max_2, min_1, rel_tol=TOL))):
                return False
        return True

    def _intersects_with_circle(self,
                                circle: Circle,
                                self_center: Tuple[float, float] = (0.0, 0.0),
                                circle_center: Tuple[float, float] = (0.0, 0.0),
                                self_rotation: float = 0.0,
                                circle_rotation: float = 0.0):
        """Check intersection between this polygon and a circle.

        The polygon and circle intersect if the circle center is inside the
        polygon or if the circle is close enough to touch any polygon edge.

        Parameters
        ----------
        circle : Circle
            The circle to test.
        self_center : Tuple[float, float]
            (x, y) center of this polygon.
        circle_center : Tuple[float, float]
            (x, y) center of the circle.
        self_rotation : float
            Rotation angle in degrees for this polygon.
        circle_rotation : float
            Rotation angle in degrees for the circle (unused).

        Returns
        -------
        bool
            True if the polygon and circle intersect, False otherwise.
        """
        _ = circle_rotation
        if self.contains_point(circle_center, self_center, self_rotation):
            return True

        radius_sq = circle.r * circle.r
        vertices = self.boundary_points(self_center, self_rotation)
        for vertex, next_vertex in zip(vertices, vertices[1:] + vertices[:1]):
            edge_x = next_vertex[0] - vertex[0]
            edge_y = next_vertex[1] - vertex[1]
            length_sq = edge_x * edge_x + edge_y * edge_y
            dx = circle_center[0] - vertex[0]
            dy = circle_center[1] - vertex[1]
            t = (dx * edge_x + dy * edge_y) / length_sq
            t = min(1.0, max(0.0, t))
            closest_x = vertex[0] + t * edge_x
            closest_y = vertex[1] + t * edge_y
            dist_x = circle_center[0] - closest_x
            dist_y = circle_center[1] - closest_y
            dist_sq = dist_x * dist_x + dist_y * dist_y
            if dist_sq < radius_sq or isclose(dist_sq, radius_sq, rel_tol=TOL):
                return True
        return False

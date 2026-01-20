from abc import ABC, abstractmethod
from typing import Any, Callable, Tuple, TypeVar, cast

import openmc

T = TypeVar('T', bound='Shape')


def _call_intersection(method: Callable[..., bool], *args: Any) -> bool:
    return method(*args)

class Shape(ABC):
    """ An abstract class for channel shapes

    Attributes
    ----------
    inner_radius : float
        The inner-radius of the shape (cm)
    outer_radius : float
        The outer-radius of the shape (cm)
    """

    @property
    def inner_radius(self) -> float:
        return self._inner_radius

    @property
    def outer_radius(self) -> float:
        return self._outer_radius

    def __init__(self, inner_radius: float, outer_radius: float):
        assert inner_radius >= 0., f"inner_radius = {inner_radius}"
        assert outer_radius >= inner_radius, f"outer_radius = {outer_radius}"

        self._inner_radius = inner_radius
        self._outer_radius = outer_radius

    def intersects(self,
                   other: "Shape",
                   self_center: Tuple[float, float] = (0.0, 0.0),
                   other_center: Tuple[float, float] = (0.0, 0.0)):
        """Check whether two shapes intersect using double dispatch.

        Parameters
        ----------
        other : Shape
            The other shape to test for intersection.
        self_center : Tuple[float, float]
            The (x, y) center of this shape.
        other_center : Tuple[float, float]
            The (x, y) center of the other shape.

        Returns
        -------
        bool or NotImplemented
            True if an implemented routine reports an intersection.
            NotImplemented when no routine exists for the pair.
        """
        method_name = f"_intersects_with_{other.__class__.__name__.lower()}"
        method = getattr(self, method_name, None)
        if callable(method):
            return _call_intersection(cast(Callable[..., bool], method),
                                      other,
                                      self_center,
                                      other_center)

        reverse_name = f"_intersects_with_{self.__class__.__name__.lower()}"
        reverse_method = getattr(other, reverse_name, None)
        if callable(reverse_method):
            return _call_intersection(cast(Callable[..., bool], reverse_method),
                                      self,
                                      other_center,
                                      self_center)

        return NotImplemented

    @abstractmethod
    def __eq__(self: T, other: Any) -> bool:
        """ Equality method

        Parameters
        ----------
        other : Any
            Other shape to check equality against
        """

    @abstractmethod
    def __hash__(self: T) -> int:
        """ Hashing method

        Returns
        -------
        int
            hash for this shape
        """

    @abstractmethod
    def make_region(self) -> openmc.Region:
        """ A method for creating a new region based on the shape

        Returns
        -------
        openmc.Region
            A new region based on this shape
        """


class Shape_2D(Shape):
    """ An abstract class for Two-Dimensional Shapes

    Attributes
    ----------
    area : float
        The area of the shape (cm^2)
    """

    @property
    def area(self) -> float:
        return self._area

    def __init__(self, inner_radius: float, outer_radius: float, area: float):
        assert area > 0.0, f"area = {area}"
        self._area = area
        super().__init__(inner_radius, outer_radius)

    @abstractmethod
    def contains_point(self,
                       point: Tuple[float, float],
                       center: Tuple[float, float] = (0.0, 0.0),
                       rotation: float = 0.0) -> bool:
        """Check whether a point lies inside the shape.

        Parameters
        ----------
        point : Tuple[float, float]
            The (x, y) point to test.
        center : Tuple[float, float]
            The (x, y) center of the shape.
        rotation : float
            Rotation angle in degrees about the shape center.

        Returns
        -------
        bool
            True if the point lies inside or on the boundary.
        """


class Shape_3D(Shape):
    """ An abstract class for Three-Dimensional Shapes

    Attributes
    ----------
    volume : float
        The volume of the shape (cm^3)
    """

    @property
    def volume(self) -> float:
        return self._volume

    def __init__(self, inner_radius: float, outer_radius: float, volume: float):
        assert volume > 0.0, f"volume = {volume}"
        self._volume = volume
        super().__init__(inner_radius, outer_radius)

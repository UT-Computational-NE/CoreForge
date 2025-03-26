from abc import ABC, abstractmethod
from typing import Any, TypeVar

import openmc

T = TypeVar('T', bound='Shape')

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
        assert inner_radius > 0., f"inner_radius = {inner_radius}"
        assert outer_radius >= inner_radius, f"outer_radius = {outer_radius}"

        self._inner_radius = inner_radius
        self._outer_radius = outer_radius

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

from abc import ABC, abstractmethod
from typing import Any, TypeVar

import openmc

T = TypeVar('T', bound='Shape')

class Shape(ABC):
    """ An abstract class for channel shapes

    Attributes
    ----------
    i_r : float
        The inner-radius of the shape (cm)
    o_r : float
        The outer-radius of the shape (cm)
    """
    _i_r: float
    _o_r: float

    @property
    def i_r(self) -> float:
        return self._i_r

    @property
    def o_r(self) -> float:
        return self._o_r

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
    _area: float

    @property
    def area(self) -> float:
        return self._area


class Shape_3D(Shape):
    """ An abstract class for Three-Dimensional Shapes

    Attributes
    ----------
    volume : float
        The volume of the shape (cm^3)
    """
    _volume: float

    @property
    def volume(self) -> float:
        return self._volume

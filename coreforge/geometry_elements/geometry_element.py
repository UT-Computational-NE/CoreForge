from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TypeVar

import openmc
import mpactpy

T = TypeVar('T', bound='GeometryElement')

class GeometryElement(ABC):
    """ An abstract class for reactor geometry elements

    Attributes
    ----------
    name : str
        A name for the geometry element
    """

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    def __init__(self, name: str = ""):
        self.name = name

    @abstractmethod
    def __eq__(self: T, other: Any) -> bool:
        """ This equality check does not check to ensure names are identical
        """

    def __ne__(self: T, other: Any) -> bool:
        return not self.__eq__(other)

    @abstractmethod
    def __hash__(self) -> int:
        """ Method for creating a hash (required because we're defining __eq__)
        """

    @abstractmethod
    def make_openmc_universe(self) -> openmc.Universe:
        """ A method for creating an OpenMC universe based on this geometry

        Returns
        -------
        openmc.Universe
            A new universe based on this geometry
        """

    def make_mpact_core(self) -> mpactpy.Core:
        """ A method for creating an MPACTPy Core based on this geometry

        Returns
        -------
        mpactpy.Core
            A new mpact core based on this geometry
        """
        raise NotImplementedError(f"Cannot make an MPACT Core for {type(self).__name__} {self.name}.")

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TypeVar


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

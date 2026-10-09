from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Optional, TypeVar

from coreforge.materials import Material


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

    def overlay(self, other: Optional[GeometryElement]) -> GeometryElement:
        """Return new geometry with ``other`` overlaid onto this element.

        Parameters
        ----------
        other : GeometryElement, optional
            Higher-priority geometry element. ``None`` returns a deep copy
            of this element.

        Returns
        -------
        GeometryElement
            New geometry produced by the registered rule for the ordered
            operand types, using deep copies of the inputs.

        Raises
        ------
        NotImplementedError
            If no overlay rule supports the ordered pair of geometry types.
        """
        from coreforge.geometry_elements.overlay import overlay

        return overlay(self, other)

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
    def get_materials(self) -> List[Material]:
        """Return the unique materials used by this geometry element.

        Returns
        -------
        List[Material]
            Unique materials used by this geometry element.
        """

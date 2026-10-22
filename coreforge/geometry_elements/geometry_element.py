from __future__ import annotations
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Callable, List, Optional, TypeVar

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


_overlay_registry: dict[
    tuple[type[GeometryElement], type[GeometryElement]],
    Callable[..., GeometryElement],
] = {}


def register_overlay(lower_cls: type[GeometryElement],
                     upper_cls: type[GeometryElement]):
    """Register an overlay rule for an ordered pair of geometry types.

    Parameters
    ----------
    lower_cls : type[GeometryElement]
        Type of the lower-priority geometry element.
    upper_cls : type[GeometryElement]
        Type of the higher-priority geometry element.

    Returns
    -------
    Callable
        Decorator registering a function that accepts ``(lower, upper)`` and
        returns their overlaid geometry.
    """
    def decorator(function: Callable[..., GeometryElement]) -> Callable[..., GeometryElement]:
        _overlay_registry[(lower_cls, upper_cls)] = function
        return function
    return decorator


def overlay(lower: GeometryElement,
            upper: Optional[GeometryElement]) -> GeometryElement:
    """Overlay higher-priority geometry onto lower-priority geometry.

    Rules are searched in method-resolution order, first for the lower
    element's type and then for the upper element's type.

    Parameters
    ----------
    lower : GeometryElement
        Lower-priority geometry element.
    upper : GeometryElement, optional
        Higher-priority geometry element. ``None`` contributes no geometry
        and returns a deep copy of ``lower``.

    Returns
    -------
    GeometryElement
        Overlaid geometry constructed from deep copies of the inputs.

    Raises
    ------
    NotImplementedError
        If no rule is registered for the ordered operand types or their base
        classes.
    """
    if upper is None:
        return deepcopy(lower)

    for lower_cls in type(lower).__mro__:
        for upper_cls in type(upper).__mro__:
            rule = _overlay_registry.get((lower_cls, upper_cls))
            if rule is not None:
                return rule(*deepcopy((lower, upper)))

    raise NotImplementedError(
        f"No overlay rule registered for {type(lower).__name__} "
        f"below {type(upper).__name__}."
    )

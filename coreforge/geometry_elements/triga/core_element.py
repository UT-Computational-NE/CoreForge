from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping

from coreforge.geometry_elements.pincell_stack import PinCellStack
from coreforge.geometry_elements.geometry_element import GeometryElement


class CoreElement(GeometryElement):
    """Abstract base class for elements that may occupy a TRIGA core location.

    Attributes
    ----------
    pincell : Mapping[str, object]
        Named axial pin-cell cross sections.
    """

    @property
    @abstractmethod
    def pincell(self) -> Mapping[str, object]:
        """Return the element's named axial pin-cell cross sections."""

    @abstractmethod
    def as_stack(self) -> PinCellStack:
        """Return the element as a pin-cell stack at its default position.

        Returns
        -------
        PinCellStack
            Element represented as a pin-cell stack.
        """

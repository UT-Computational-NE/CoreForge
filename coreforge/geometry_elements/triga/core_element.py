from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping

from coreforge.geometry_elements.cylindrical_stack import CylindricalStack
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
    def as_stack(self) -> CylindricalStack:
        """Return the element as a cylindrical stack at its default position.

        Returns
        -------
        CylindricalStack
            Element represented as a cylindrical stack.
        """

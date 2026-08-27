from __future__ import annotations

from typing import Optional, Tuple

import mpactpy

from coreforge import geometry_elements
from coreforge.mpact_builder.builder import Bounds
from coreforge.mpact_builder.mpact_builder import register_builder
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.triga.core_element import CoreElement


@register_builder(geometry_elements.CylindricalStack)
class CylindricalStack(CoreElement[geometry_elements.CylindricalStack]):
    """MPACT builder for cylindrical stacks used as TRIGA core elements.

    Parameters
    ----------
    specs : Optional[Specs]
        Specifications for building the cylindrical stack. If omitted, default
        :class:`Stack.Specs` are used.

    Attributes
    ----------
    specs : Specs
        Specifications for building the cylindrical stack.
    """

    Specs = Stack.Specs

    def default_specs(self) -> Specs:
        return self.Specs()

    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs is not None else self.Specs()

    def build(
        self,
        element: geometry_elements.CylindricalStack,
        bounds: Optional[Bounds] = None,
    ) -> mpactpy.Core:
        """Build an MPACT core using the generic stack builder.

        Parameters
        ----------
        element : geometry_elements.CylindricalStack
            Cylindrical stack to build.
        bounds : Optional[Bounds]
            Spatial bounds for the geometry.

        Returns
        -------
        mpactpy.Core
            MPACT representation of the cylindrical stack.
        """
        return Stack(self.specs).build(element, bounds)

    def build_stack_and_specs(
        self,
        element: geometry_elements.CylindricalStack,
    ) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:
        """Return the cylindrical stack and its stack specifications.

        Parameters
        ----------
        element : geometry_elements.CylindricalStack
            Cylindrical stack to use as a TRIGA core element.

        Returns
        -------
        Tuple[geometry_elements.CylindricalStack, Stack.Specs]
            Cylindrical stack and its corresponding MPACT stack
            specifications.
        """
        return element, self.specs

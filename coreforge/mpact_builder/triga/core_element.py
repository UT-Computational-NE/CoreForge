from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple, TypeVar

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.mpact_builder import Builder, CylindricalPinCell, Stack
import coreforge.geometry_elements as geometry_elements

TCoreElement = TypeVar("TCoreElement", bound=GeometryElement)


class CoreElement(Builder[TCoreElement], ABC):
    """Base builder for TRIGA core elements."""

    @dataclass
    class SegmentSpecs(Stack.Segment.Specs):
        """Specs for core element stack segments.

        Attributes
        ----------
        builder_specs : Optional[CylindricalPinCell.Specs]
            Builder specifications for the segment element.
        """

        builder_specs: Optional[CylindricalPinCell.Specs] = None

        def __post_init__(self) -> None:
            super().__post_init__()
            if self.builder_specs is None:
                return
            assert isinstance(self.builder_specs, CylindricalPinCell.Specs), \
                "CoreElement.SegmentSpecs.builder_specs must be CylindricalPinCell.Specs."

    @abstractmethod
    def build_stack_and_specs(
        self,
        element: TCoreElement,
    ) -> Tuple[geometry_elements.Stack, Stack.Specs]:
        """Build the element stack and corresponding stack specs.

        Parameters
        ----------
        element : GeometryElement
            The geometry element to be built into a stack.

        Returns
        -------
        Tuple[geometry_elements.Stack, Stack.Specs]
            The stack representation of the element and corresponding stack specs.
        """
        raise NotImplementedError

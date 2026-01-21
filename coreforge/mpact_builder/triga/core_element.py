from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple, TypeVar

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.mpact_builder.builder import Builder
from coreforge.mpact_builder.builder_specs import MaterialSpecs
from coreforge.mpact_builder.cylindrical_pincell import CylindricalPinCell
from coreforge.mpact_builder.stack import Stack
from coreforge import geometry_elements

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

    @staticmethod
    def _apply_material_specs(
        segment_specs: dict[Stack.Segment, "CoreElement.SegmentSpecs"],
        material_specs: Optional[MaterialSpecs],
    ) -> None:
        """Merge element-level material specs into segment builder specs."""
        if not material_specs:
            return
        for specs in segment_specs.values():
            if specs.builder_specs is None:
                specs.builder_specs = CylindricalPinCell.Specs()
            specs.builder_specs.material_specs = (
                material_specs | specs.builder_specs.material_specs
            )

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

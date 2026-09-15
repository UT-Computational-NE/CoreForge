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

    def build_stack_and_specs(
        self,
        element: TCoreElement,
        x0: float = 0.0,
        y0: float = 0.0,
    ) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:
        """Build the element stack and corresponding stack specs.

        Parameters
        ----------
        element : GeometryElement
            The geometry element to be built into a stack.
        x0 : float
            Translation applied to the stack along the x-axis [cm].
        y0 : float
            Translation applied to the stack along the y-axis [cm].

        Returns
        -------
        Tuple[geometry_elements.CylindricalStack, Stack.Specs]
            The stack representation of the element and corresponding stack specs.
        """
        stack, stack_specs = self._build_stack_and_specs(element)

        if x0 == 0.0 and y0 == 0.0:
            return stack, stack_specs

        translated_stack = stack.translate(x0, y0)
        translated_segment_specs = {
            translated_segment: stack_specs.segment_specs.get(original_segment)
            for original_segment, translated_segment
            in zip(stack.segments, translated_stack.segments)
        }
        translated_specs = Stack.Specs(segment_specs=translated_segment_specs,
                                       num_procs=stack_specs.num_procs)
        return translated_stack, translated_specs

    @abstractmethod
    def _build_stack_and_specs(
        self,
        element: TCoreElement,
    ) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:
        """Build an untranslated element stack and its corresponding specs."""
        raise NotImplementedError

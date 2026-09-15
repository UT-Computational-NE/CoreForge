from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import mpactpy

from coreforge import geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl
from coreforge.mpact_builder.builder import AxisBounds, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs
from coreforge.mpact_builder.mpact_builder import build, register_builder
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.triga.core_element import CoreElement


@register_builder(geometry_elements_triga_netl.PNT)
class PNT(CoreElement[geometry_elements_triga_netl.PNT]):
    """MPACT geometry builder for a TRIGA NETL PNT.

    Parameters
    ----------
    specs : Optional[Specs]
        Specifications for building the MPACT representation of this element.
    """

    @dataclass
    class Specs(BuilderSpecs):
        """Building specifications for a PNT.

        Attributes
        ----------
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all PNT segments.
        terminus : CoreElement.SegmentSpecs
            Specifications shared by the terminus segments.
        wrapped_tube : CoreElement.SegmentSpecs
            Specifications for the wrapped transport-tube segment.
        tube : CoreElement.SegmentSpecs
            Specifications for the unwrapped transport-tube segment.
        """

        material_specs: Optional[MaterialSpecs] = None
        terminus: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        wrapped_tube: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        tube: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )

        def __post_init__(self) -> None:
            self.terminus = self.terminus or CoreElement.SegmentSpecs()
            self.wrapped_tube = self.wrapped_tube or CoreElement.SegmentSpecs()
            self.tube = self.tube or CoreElement.SegmentSpecs()

    def __init__(self, specs: Optional[Specs] = None):
        super().__init__(specs)

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
        element: geometry_elements_triga_netl.PNT,
        bounds: Optional[Bounds] = None,
    ) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a TRIGA NETL PNT

        Parameters
        ----------
        element: geometry_elements_triga_netl.SourceHolder
            The geometry element to be built
        bounds: Optional[Bounds]
            The spatial bounds for the geometry.
            X and Y bounds are passed to child segments.
            Z bounds, if provided, are applied to the final assembled stack to extract an axial slice.

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        stack, stack_specs = self.build_stack_and_specs(element)

        if bounds is None:
            outer_radius = max(
                zone.shape.outer_radius
                for segment in stack.segments
                for zone in segment.element.zones
            )
            bounds = Bounds(
                X=AxisBounds(min=-outer_radius, max=outer_radius),
                Y=AxisBounds(min=-outer_radius, max=outer_radius),
            )

        return build(stack, stack_specs, bounds)

    def _build_stack_and_specs(
        self,
        element: geometry_elements_triga_netl.PNT,
    ) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:
        """Return the PNT stack and its corresponding segment specifications."""

        stack = element.as_stack()
        terminus_count = len(element.terminus.segments)
        segment_specs = {
            segment: self.specs.terminus
            for segment in stack.segments[:terminus_count]
        }

        tube_index = terminus_count
        if element.wrapper is not None:
            segment_specs[stack.segments[tube_index]] = self.specs.wrapped_tube
            tube_index += 1

        if tube_index < len(stack.segments):
            segment_specs[stack.segments[tube_index]] = self.specs.tube

        self._apply_material_specs(segment_specs, self.specs.material_specs)

        return stack, Stack.Specs(segment_specs)

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


@register_builder(geometry_elements_triga_netl.ThreeElementIrradiator)
class ThreeElementIrradiator(CoreElement[geometry_elements_triga_netl.ThreeElementIrradiator]):
    """MPACT geometry builder for a conventional NETL three-element irradiator.

    Parameters
    ----------
    specs : Optional[Specs]
        Specifications for building the MPACT representation of this element.
    """

    @dataclass
    class Specs(BuilderSpecs):
        """Building specifications for a three-element irradiator.

        Attributes
        ----------
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all irradiator segments.
        solid_end : CoreElement.SegmentSpecs
            Specifications shared by the solid lower- and upper-end segments.
        liner_bottom : CoreElement.SegmentSpecs
            Specifications for the solid liner-bottom segment.
        inner_sleeve_bottom : CoreElement.SegmentSpecs
            Specifications for the solid inner-sleeve-bottom segment.
        lined : CoreElement.SegmentSpecs
            Specifications for the segment containing both sleeve and liner
            sidewalls.
        inner_sleeve : CoreElement.SegmentSpecs
            Specifications for the sleeve-only sidewall segment.
        outer_casing : CoreElement.SegmentSpecs
            Specifications for the casing-only annular segment.
        """

        material_specs: Optional[MaterialSpecs] = None
        solid_end: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        liner_bottom: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        inner_sleeve_bottom: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        lined: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        inner_sleeve: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        outer_casing: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )

        def __post_init__(self) -> None:
            self.solid_end = self.solid_end or CoreElement.SegmentSpecs()
            self.liner_bottom = self.liner_bottom or CoreElement.SegmentSpecs()
            self.inner_sleeve_bottom = self.inner_sleeve_bottom or CoreElement.SegmentSpecs()
            self.lined = self.lined or CoreElement.SegmentSpecs()
            self.inner_sleeve = self.inner_sleeve or CoreElement.SegmentSpecs()
            self.outer_casing = self.outer_casing or CoreElement.SegmentSpecs()

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
        element: geometry_elements_triga_netl.ThreeElementIrradiator,
        bounds: Optional[Bounds] = None,
    ) -> mpactpy.Core:
        """Build an MPACT representation of the three-element irradiator.

        Parameters
        ----------
        element : geometry_elements_triga_netl.ThreeElementIrradiator
            Irradiator geometry to build.
        bounds : Optional[Bounds]
            Spatial bounds for the geometry. X and Y bounds are passed to the
            child segments. Z bounds, when provided, clip the assembled stack.

        Returns
        -------
        mpactpy.Core
            MPACT representation of the irradiator.
        """

        if bounds is None:
            outer_radius = element.outer_casing.outer_radius
            bounds = Bounds(
                X=AxisBounds(min=-outer_radius, max=outer_radius),
                Y=AxisBounds(min=-outer_radius, max=outer_radius),
            )

        stack, stack_specs = self.build_stack_and_specs(element)
        return build(stack, stack_specs, bounds)

    def _build_stack_and_specs(
        self,
        element: geometry_elements_triga_netl.ThreeElementIrradiator,
    ) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:
        """Return the irradiator stack and its segment specifications."""

        stack = element.as_stack(bottom_pos=0.0)
        segment_specs = {
            stack.segments[0]: self.specs.solid_end,
            stack.segments[1]: self.specs.liner_bottom,
            stack.segments[2]: self.specs.inner_sleeve_bottom,
            stack.segments[3]: self.specs.lined,
            stack.segments[4]: self.specs.inner_sleeve,
            stack.segments[5]: self.specs.outer_casing,
            stack.segments[6]: self.specs.solid_end,
        }

        self._apply_material_specs(segment_specs, self.specs.material_specs)
        return stack, Stack.Specs(segment_specs)

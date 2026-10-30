from __future__ import annotations
from typing import Optional, Tuple
from dataclasses import dataclass

import mpactpy

from coreforge.mpact_builder.builder import AxisBounds, Bounds
from coreforge.mpact_builder.builder_specs import MaterialSpecs
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.mpact_builder import build, register_builder
from coreforge.mpact_builder.triga.core_element import CoreElement
from coreforge import geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


@register_builder(geometry_elements_triga_netl.SourceHolder)
class SourceHolder(CoreElement[geometry_elements_triga_netl.SourceHolder]):
    """ An MPACT geometry builder class for a TRIGA NETL Source Holder

    Parameters
    ----------
    specs: Optional[Specs]
        Specifications for building the MPACT representation of this element

    Attributes
    ----------
    specs: Optional[Specs]
        Specifications for building the MPACT representation of this element
    """

    @dataclass
    class Specs(CoreElement.Specs):
        """ Building specifications for SourceHolder

        Attributes
        ----------
        default_segment_specs : Optional[CoreElement.SegmentSpecs]
            Default settings for omitted features; explicit feature settings
            replace the entire default. Each default is copied independently.
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all pincell segments.
        solid : CoreElement.SegmentSpecs
            Specs for the solid cladding regions above/below the cavity.
        cavity : CoreElement.SegmentSpecs
            Specs for the cavity region.
        """

        material_specs: Optional[MaterialSpecs] = None
        solid: Optional[CoreElement.SegmentSpecs] = None
        cavity: Optional[CoreElement.SegmentSpecs] = None

        def __post_init__(self):
            self.solid = self.resolve_segment_specs(self.solid)
            self.cavity = self.resolve_segment_specs(self.cavity)


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


    def build(self,
              element: geometry_elements_triga_netl.SourceHolder,
              bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a TRIGA NETL Source Holder

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

        if bounds is None:
            outer_radius = element.cladding.outer_radius
            bounds = Bounds(X=AxisBounds(min=-outer_radius, max=outer_radius),
                            Y=AxisBounds(min=-outer_radius, max=outer_radius))

        stack, stack_specs = self.build_stack_and_specs(element)

        return build(stack, stack_specs, bounds)


    def _build_stack_and_specs(self,
                               element: geometry_elements_triga_netl.SourceHolder,
    ) -> Tuple[geometry_elements.PinCellStack, Stack.Specs]:

        stack = element.as_stack()

        specs_by_pincell = {id(p): getattr(self.specs, name) for name, p in element.pincell.items()}
        segment_specs = {segment: specs_by_pincell[id(segment.element)] for segment in stack.segments}

        self._apply_material_specs(segment_specs, self.specs.material_specs)

        stack_specs = Stack.Specs(segment_specs)

        return stack, stack_specs

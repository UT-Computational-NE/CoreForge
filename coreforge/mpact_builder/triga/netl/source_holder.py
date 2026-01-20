from __future__ import annotations
from typing import Optional, Tuple
from dataclasses import dataclass, field

import mpactpy

from coreforge.mpact_builder.builder import AxisBounds, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
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
    class Specs(BuilderSpecs):
        """ Building specifications for SourceHolder

        Attributes
        ----------
        solid : CoreElement.SegmentSpecs
            Specs for the solid cladding regions above/below the cavity.
        cavity : CoreElement.SegmentSpecs
            Specs for the cavity region.
        """

        solid: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        cavity: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )

        def __post_init__(self):
            self.solid = self.solid or CoreElement.SegmentSpecs()
            self.cavity = self.cavity or CoreElement.SegmentSpecs()


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


    def build_stack_and_specs(self,
                              element: geometry_elements_triga_netl.SourceHolder,
    ) -> Tuple[geometry_elements.Stack, Stack.Specs]:

        stack = element.as_stack()

        segment_specs = {stack.segments[0]: self.specs.solid,
                         stack.segments[1]: self.specs.cavity,
                         stack.segments[2]: self.specs.solid}

        stack_specs = Stack.Specs(segment_specs)

        return stack, stack_specs

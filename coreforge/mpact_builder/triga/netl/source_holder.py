from __future__ import annotations
from typing import Optional, Tuple
from dataclasses import dataclass, field
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build
from coreforge.mpact_builder.builder import AxisBounds, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.cylindrical_pincell import CylindricalPinCell
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.triga.core_element import CoreElement
import coreforge.geometry_elements as geometry_elements
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
    class RegionSpecs(BuilderSpecs):
        """ Building specifications for a SourceHolder region.

        Attributes
        ----------
        target_axial_thickness : float
            Target axial thickness for segment subdivision (cm).
        pincell_specs : CylindricalPinCell.Specs
            Specifications for building the region pincell.
        """

        target_axial_thickness: Optional[float] = None
        pincell_specs:          Optional[CylindricalPinCell.Specs] = None

        def __post_init__(self):
            if not self.target_axial_thickness:
                self.target_axial_thickness = inf

            assert self.target_axial_thickness > 0.0, \
                f"target_axial_thickness = {self.target_axial_thickness}"

            if not self.pincell_specs:
                self.pincell_specs = CylindricalPinCell.Specs()


    @dataclass
    class Specs(BuilderSpecs):
        """ Building specifications for SourceHolder

        Attributes
        ----------
        solid : RegionSpecs
            Specs for the solid cladding regions above/below the cavity.
        cavity : RegionSpecs
            Specs for the cavity region.
        """

        solid:  Optional[SourceHolder.RegionSpecs] = field(
            default_factory=lambda: SourceHolder.RegionSpecs()
        )
        cavity: Optional[SourceHolder.RegionSpecs] = field(
            default_factory=lambda: SourceHolder.RegionSpecs()
        )

        def __post_init__(self):
            self.solid  = self.solid  or SourceHolder.RegionSpecs()
            self.cavity = self.cavity or SourceHolder.RegionSpecs()


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

        segments = [(stack.segments[0], self.specs.solid),
                    (stack.segments[1], self.specs.cavity),
                    (stack.segments[2], self.specs.solid)]

        stack = geometry_elements.Stack(segments=[segment for segment, _ in segments],
                                        name=element.name)

        stack_specs = Stack.Specs({
            segment: Stack.Segment.Specs(region_specs.target_axial_thickness,
                                         region_specs.pincell_specs)
            for segment, region_specs in segments
        })

        return stack, stack_specs

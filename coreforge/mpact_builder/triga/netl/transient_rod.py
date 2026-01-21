from __future__ import annotations
from typing import Optional, Tuple
from dataclasses import dataclass, field

import mpactpy

from coreforge.mpact_builder.builder import AxisBounds, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.mpact_builder import build, register_builder
from coreforge.mpact_builder.triga.core_element import CoreElement
from coreforge import geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


@register_builder(geometry_elements_triga_netl.TransientRod)
class TransientRod(CoreElement[geometry_elements_triga_netl.TransientRod]):
    """ An MPACT geometry builder class for a TRIGA NETL Transient Rod

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
        """ Building specifications for TransientRod

        Attributes
        ----------
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all pincell segments.
        lower_element_plug : CoreElement.SegmentSpecs
            Specs for the lower element plug region.
        air_follower : CoreElement.SegmentSpecs
            Specs for the air follower region.
        lower_magneform_fitting : CoreElement.SegmentSpecs
            Specs for the lower magneform fitting region.
        absorber : CoreElement.SegmentSpecs
            Specs for the absorber region.
        upper_magneform_fitting : CoreElement.SegmentSpecs
            Specs for the upper magneform fitting region.
        upper_element_plug : CoreElement.SegmentSpecs
            Specs for the upper element plug region.
        """

        material_specs: Optional[MaterialSpecs] = None
        lower_element_plug: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        air_follower: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        lower_magneform_fitting: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        absorber: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        upper_magneform_fitting: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        upper_element_plug: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )

        def __post_init__(self):
            self.lower_element_plug = self.lower_element_plug or CoreElement.SegmentSpecs()
            self.air_follower = self.air_follower or CoreElement.SegmentSpecs()
            self.lower_magneform_fitting = self.lower_magneform_fitting or CoreElement.SegmentSpecs()
            self.absorber = self.absorber or CoreElement.SegmentSpecs()
            self.upper_magneform_fitting = self.upper_magneform_fitting or CoreElement.SegmentSpecs()
            self.upper_element_plug = self.upper_element_plug or CoreElement.SegmentSpecs()


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
              element: geometry_elements_triga_netl.TransientRod,
              bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a TRIGA NETL Transient Rod

        Parameters
        ----------
        element: geometry_elements_triga_netl.TransientRod
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
                              element: geometry_elements_triga_netl.TransientRod,
    ) -> Tuple[geometry_elements.Stack, Stack.Specs]:

        stack = element.as_stack().unionize_radial_mesh()
        segment_specs = {stack.segments[0]: self.specs.lower_element_plug,
                         stack.segments[1]: self.specs.air_follower,
                         stack.segments[2]: self.specs.lower_magneform_fitting,
                         stack.segments[3]: self.specs.absorber,
                         stack.segments[4]: self.specs.upper_magneform_fitting,
                         stack.segments[5]: self.specs.upper_element_plug}

        self._apply_material_specs(segment_specs, self.specs.material_specs)

        stack_specs = Stack.Specs(segment_specs)

        return stack, stack_specs

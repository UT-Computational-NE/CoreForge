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


@register_builder(geometry_elements_triga_netl.FuelFollowerControlRod)
class FuelFollowerControlRod(CoreElement[geometry_elements_triga_netl.FuelFollowerControlRod]):
    """ An MPACT geometry builder class for a TRIGA NETL Fuel Follower Control Rod

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
        """ Building specifications for FuelFollowerControlRod

        Attributes
        ----------
        lower_element_plug : CoreElement.SegmentSpecs
            Specs for the lower element plug region.
        lower_air_gap : CoreElement.SegmentSpecs
            Specs for the lower air gap region.
        lower_magneform_fitting : CoreElement.SegmentSpecs
            Specs for the lower magneform fitting region.
        fuel_follower : CoreElement.SegmentSpecs
            Specs for the fuel follower region.
        above_fuel_follower_air_gap : CoreElement.SegmentSpecs
            Specs for the air gap above the fuel follower.
        middle_magneform_fitting : CoreElement.SegmentSpecs
            Specs for the middle magneform fitting region.
        absorber : CoreElement.SegmentSpecs
            Specs for the absorber region.
        above_absorber_air_gap : CoreElement.SegmentSpecs
            Specs for the air gap above the absorber.
        upper_magneform_fitting : CoreElement.SegmentSpecs
            Specs for the upper magneform fitting region.
        upper_air_gap : CoreElement.SegmentSpecs
            Specs for the upper air gap region.
        upper_element_plug : CoreElement.SegmentSpecs
            Specs for the upper element plug region.
        """

        lower_element_plug: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        lower_air_gap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        lower_magneform_fitting: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        fuel_follower: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        above_fuel_follower_air_gap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        middle_magneform_fitting: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        absorber: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        above_absorber_air_gap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        upper_magneform_fitting: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        upper_air_gap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        upper_element_plug: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )

        def __post_init__(self):
            self.lower_element_plug = self.lower_element_plug or CoreElement.SegmentSpecs()
            self.lower_air_gap = self.lower_air_gap or CoreElement.SegmentSpecs()
            self.lower_magneform_fitting = self.lower_magneform_fitting or CoreElement.SegmentSpecs()
            self.fuel_follower = self.fuel_follower or CoreElement.SegmentSpecs()
            self.above_fuel_follower_air_gap = (
                self.above_fuel_follower_air_gap or CoreElement.SegmentSpecs()
            )
            self.middle_magneform_fitting = self.middle_magneform_fitting or CoreElement.SegmentSpecs()
            self.absorber = self.absorber or CoreElement.SegmentSpecs()
            self.above_absorber_air_gap = self.above_absorber_air_gap or CoreElement.SegmentSpecs()
            self.upper_magneform_fitting = self.upper_magneform_fitting or CoreElement.SegmentSpecs()
            self.upper_air_gap = self.upper_air_gap or CoreElement.SegmentSpecs()
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
              element: geometry_elements_triga_netl.FuelFollowerControlRod,
              bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a TRIGA NETL Fuel Follower Control Rod

        Parameters
        ----------
        element: geometry_elements_triga_netl.FuelFollowerControlRod
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
                              element: geometry_elements_triga_netl.FuelFollowerControlRod,
    ) -> Tuple[geometry_elements.Stack, Stack.Specs]:

        stack = element.as_stack().unionize_radial_mesh()
        segment_specs = {stack.segments[0]: self.specs.lower_element_plug,
                         stack.segments[1]: self.specs.lower_air_gap,
                         stack.segments[2]: self.specs.lower_magneform_fitting,
                         stack.segments[3]: self.specs.fuel_follower,
                         stack.segments[4]: self.specs.above_fuel_follower_air_gap,
                         stack.segments[5]: self.specs.middle_magneform_fitting,
                         stack.segments[6]: self.specs.absorber,
                         stack.segments[7]: self.specs.above_absorber_air_gap,
                         stack.segments[8]: self.specs.upper_magneform_fitting,
                         stack.segments[9]: self.specs.upper_air_gap,
                         stack.segments[10]: self.specs.upper_element_plug}

        stack_specs = Stack.Specs(segment_specs)

        return stack, stack_specs

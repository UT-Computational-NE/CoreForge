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
    class Specs(CoreElement.Specs):
        """ Building specifications for FuelFollowerControlRod

        Attributes
        ----------
        default_segment_specs : Optional[CoreElement.SegmentSpecs]
            Default settings for omitted features; explicit feature settings
            replace the entire default. Each default is copied independently.
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all pincell segments.
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

        material_specs: Optional[MaterialSpecs] = None
        lower_element_plug: Optional[CoreElement.SegmentSpecs] = None
        lower_air_gap: Optional[CoreElement.SegmentSpecs] = None
        lower_magneform_fitting: Optional[CoreElement.SegmentSpecs] = None
        fuel_follower: Optional[CoreElement.SegmentSpecs] = None
        above_fuel_follower_air_gap: Optional[CoreElement.SegmentSpecs] = None
        middle_magneform_fitting: Optional[CoreElement.SegmentSpecs] = None
        absorber: Optional[CoreElement.SegmentSpecs] = None
        above_absorber_air_gap: Optional[CoreElement.SegmentSpecs] = None
        upper_magneform_fitting: Optional[CoreElement.SegmentSpecs] = None
        upper_air_gap: Optional[CoreElement.SegmentSpecs] = None
        upper_element_plug: Optional[CoreElement.SegmentSpecs] = None

        def __post_init__(self):
            self.lower_element_plug = self.resolve_segment_specs(self.lower_element_plug)
            self.lower_air_gap = self.resolve_segment_specs(self.lower_air_gap)
            self.lower_magneform_fitting = self.resolve_segment_specs(self.lower_magneform_fitting)
            self.fuel_follower = self.resolve_segment_specs(self.fuel_follower)
            self.above_fuel_follower_air_gap = (
                self.resolve_segment_specs(self.above_fuel_follower_air_gap)
            )
            self.middle_magneform_fitting = self.resolve_segment_specs(self.middle_magneform_fitting)
            self.absorber = self.resolve_segment_specs(self.absorber)
            self.above_absorber_air_gap = self.resolve_segment_specs(self.above_absorber_air_gap)
            self.upper_magneform_fitting = self.resolve_segment_specs(self.upper_magneform_fitting)
            self.upper_air_gap = self.resolve_segment_specs(self.upper_air_gap)
            self.upper_element_plug = self.resolve_segment_specs(self.upper_element_plug)


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


    def _build_stack_and_specs(self,
                               element: geometry_elements_triga_netl.FuelFollowerControlRod,
    ) -> Tuple[geometry_elements.PinCellStack, Stack.Specs]:

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

        self._apply_material_specs(segment_specs, self.specs.material_specs)

        stack_specs = Stack.Specs(segment_specs)

        return stack, stack_specs

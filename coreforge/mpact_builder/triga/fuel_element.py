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
import coreforge.geometry_elements.triga as geometry_elements_triga


@register_builder(geometry_elements_triga.FuelElement)
class FuelElement(CoreElement[geometry_elements_triga.FuelElement]):
    """ An MPACT geometry builder class for a TRIGA Fuel Element

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
        """ Building specifications for FuelElement

        Attributes
        ----------
        default_segment_specs : Optional[CoreElement.SegmentSpecs]
            Default settings for omitted features; explicit feature settings
            replace the entire default. Each default is copied independently.
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all pincell segments.
        lower_end_fitting : CoreElement.SegmentSpecs
            Specs for the lower end fitting region.
        lower_reflector : CoreElement.SegmentSpecs
            Specs for the lower graphite reflector region.
        moly_disc : CoreElement.SegmentSpecs
            Specs for the molybdenum disc region.
        fuel : CoreElement.SegmentSpecs
            Specs for the fuel meat region.
        upper_reflector : CoreElement.SegmentSpecs
            Specs for the upper graphite reflector region.
        air_gap : CoreElement.SegmentSpecs
            Specs for the upper air gap region.
        upper_end_fitting : CoreElement.SegmentSpecs
            Specs for the upper end fitting region.
        """

        material_specs: Optional[MaterialSpecs] = None
        lower_end_fitting: Optional[CoreElement.SegmentSpecs] = None
        lower_reflector: Optional[CoreElement.SegmentSpecs] = None
        moly_disc: Optional[CoreElement.SegmentSpecs] = None
        fuel: Optional[CoreElement.SegmentSpecs] = None
        upper_reflector: Optional[CoreElement.SegmentSpecs] = None
        air_gap: Optional[CoreElement.SegmentSpecs] = None
        upper_end_fitting: Optional[CoreElement.SegmentSpecs] = None

        def __post_init__(self):
            self.lower_end_fitting = self.resolve_segment_specs(self.lower_end_fitting)
            self.lower_reflector = self.resolve_segment_specs(self.lower_reflector)
            self.moly_disc = self.resolve_segment_specs(self.moly_disc)
            self.fuel = self.resolve_segment_specs(self.fuel)
            self.upper_reflector = self.resolve_segment_specs(self.upper_reflector)
            self.air_gap = self.resolve_segment_specs(self.air_gap)
            self.upper_end_fitting = self.resolve_segment_specs(self.upper_end_fitting)


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
              element: geometry_elements_triga.FuelElement,
              bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a TRIGA Fuel Element

        Notes
        -----
        End fittings are represented by a volume-preserving stack of cylinders
        derived from the end fitting cone geometry elements.

        Parameters
        ----------
        element: geometry_elements_triga.FuelElement
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
                               element: geometry_elements_triga.FuelElement,
    ) -> Tuple[geometry_elements.PinCellStack, Stack.Specs]:

        stack = element.as_stack(
            lower_end_target_axial_thickness = self.specs.lower_end_fitting.target_axial_thickness,
            upper_end_target_axial_thickness = self.specs.upper_end_fitting.target_axial_thickness,
        )

        pincell = element.pincell
        segment_specs = {}
        lower_end_count = None
        for idx, segment in enumerate(stack.segments):
            if segment.element is pincell["lower_reflector"]:
                lower_end_count = idx
                break

        mid_specs = [self.specs.lower_reflector,
                     self.specs.moly_disc,
                     *([self.specs.fuel] * element.fuel_meat.num_axial_regions),
                     self.specs.upper_reflector,
                     self.specs.air_gap]

        mid_count = len(mid_specs)
        mid_start = lower_end_count
        mid_end   = mid_start + mid_count

        for segment in stack.segments[:lower_end_count]:
            segment_specs[segment] = self.specs.lower_end_fitting

        for segment, region_specs in zip(stack.segments[mid_start:mid_end], mid_specs):
            segment_specs[segment] = region_specs

        for segment in stack.segments[mid_end:]:
            segment_specs[segment] = self.specs.upper_end_fitting

        self._apply_material_specs(segment_specs, self.specs.material_specs)

        stack_specs = Stack.Specs(segment_specs)

        return stack, stack_specs

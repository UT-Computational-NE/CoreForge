from __future__ import annotations
from typing import Optional, Tuple
from dataclasses import dataclass, field
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build
from coreforge.mpact_builder.builder import AxisBounds, Bounds, Builder
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.cylindrical_pincell import CylindricalPinCell
from coreforge.mpact_builder.stack import Stack
import coreforge.geometry_elements as geometry_elements
import coreforge.geometry_elements.triga as geometry_elements_triga


@register_builder(geometry_elements_triga.FuelElement)
class FuelElement(Builder[geometry_elements_triga.FuelElement]):
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
    class RegionSpecs(BuilderSpecs):
        """ Building specifications for a FuelElement region.

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
        """ Building specifications for FuelElement

        Attributes
        ----------
        lower_end_fitting : RegionSpecs
            Specs for the lower end fitting region (not currently modeled).
        lower_reflector : RegionSpecs
            Specs for the lower graphite reflector region.
        moly_disc : RegionSpecs
            Specs for the molybdenum disc region.
        fuel : RegionSpecs
            Specs for the fuel meat region.
        upper_reflector : RegionSpecs
            Specs for the upper graphite reflector region.
        air_gap : RegionSpecs
            Specs for the upper air gap region.
        upper_end_fitting : RegionSpecs
            Specs for the upper end fitting region (not currently modeled).
        """

        lower_end_fitting: Optional[FuelElement.RegionSpecs] = field(default_factory=lambda: FuelElement.RegionSpecs())
        lower_reflector:   Optional[FuelElement.RegionSpecs] = field(default_factory=lambda: FuelElement.RegionSpecs())
        moly_disc:         Optional[FuelElement.RegionSpecs] = field(default_factory=lambda: FuelElement.RegionSpecs())
        fuel:              Optional[FuelElement.RegionSpecs] = field(default_factory=lambda: FuelElement.RegionSpecs())
        upper_reflector:   Optional[FuelElement.RegionSpecs] = field(default_factory=lambda: FuelElement.RegionSpecs())
        air_gap:           Optional[FuelElement.RegionSpecs] = field(default_factory=lambda: FuelElement.RegionSpecs())
        upper_end_fitting: Optional[FuelElement.RegionSpecs] = field(default_factory=lambda: FuelElement.RegionSpecs())

        def __post_init__(self):
            self.lower_end_fitting = self.lower_end_fitting or FuelElement.RegionSpecs()
            self.lower_reflector   = self.lower_reflector   or FuelElement.RegionSpecs()
            self.moly_disc         = self.moly_disc         or FuelElement.RegionSpecs()
            self.fuel              = self.fuel              or FuelElement.RegionSpecs()
            self.upper_reflector   = self.upper_reflector   or FuelElement.RegionSpecs()
            self.air_gap           = self.air_gap           or FuelElement.RegionSpecs()
            self.upper_end_fitting = self.upper_end_fitting or FuelElement.RegionSpecs()


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


    def build_stack_and_specs(self,
                              element: geometry_elements_triga.FuelElement,
    ) -> Tuple[geometry_elements.Stack, Stack.Specs]:
        """Build the element stack and corresponding stack specs."""
        cone = element.lower_end_fitting.cone(outer_material = element.outer_material,
                                              name           = element.name + "_lower_end_fitting_cone")
        lower_end_stack = cone.as_stack(target_axial_length = self.specs.lower_end_fitting.target_axial_thickness,
                                        direction           = element.lower_end_fitting.direction)

        cone = element.upper_end_fitting.cone(outer_material = element.outer_material,
                                              name           = element.name + "_upper_end_fitting_cone")
        upper_end_stack = cone.as_stack(target_axial_length = self.specs.upper_end_fitting.target_axial_thickness,
                                        direction           = element.upper_end_fitting.direction)

        mid_stack = geometry_elements.Stack(segments=[
            geometry_elements.Stack.Segment(element.lower_reflector_pincell,
                                            element.lower_graphite_reflector.thickness),
            geometry_elements.Stack.Segment(element.moly_disc_pincell,
                                            element.moly_disc.thickness),
            geometry_elements.Stack.Segment(element.fuel_pincell,
                                            element.fuel_meat.length),
            geometry_elements.Stack.Segment(element.upper_reflector_pincell,
                                            element.upper_graphite_reflector.thickness),
            geometry_elements.Stack.Segment(element.air_gap_pincell,
                                            element.upper_air_gap.thickness)])

        stack = lower_end_stack + mid_stack + upper_end_stack
        stack.name = element.name

        segments = []
        segments.extend((segment, self.specs.lower_end_fitting)
                        for segment in lower_end_stack.segments)
        segments.extend([(mid_stack.segments[0], self.specs.lower_reflector),
                         (mid_stack.segments[1], self.specs.moly_disc),
                         (mid_stack.segments[2], self.specs.fuel),
                         (mid_stack.segments[3], self.specs.upper_reflector),
                         (mid_stack.segments[4], self.specs.air_gap)])
        segments.extend((segment, self.specs.upper_end_fitting)
                        for segment in upper_end_stack.segments)

        stack_specs = Stack.Specs({
            segment: Stack.Segment.Specs(region_specs.target_axial_thickness,
                                         region_specs.pincell_specs)
            for segment, region_specs in segments})

        return stack, stack_specs

from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.cylindrical_pincell import CylindricalPinCell
from coreforge.mpact_builder.stack import Stack
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


@register_builder(geometry_elements_triga_netl.FuelFollowerControlRod)
class FuelFollowerControlRod:
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
    class RegionSpecs(BuilderSpecs):
        """ Building specifications for a FuelFollowerControlRod region.

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
        """ Building specifications for FuelFollowerControlRod

        Attributes
        ----------
        lower_element_plug : RegionSpecs
            Specs for the lower element plug region.
        lower_air_gap : RegionSpecs
            Specs for the lower air gap region.
        lower_magneform_fitting : RegionSpecs
            Specs for the lower magneform fitting region.
        fuel_follower : RegionSpecs
            Specs for the fuel follower region.
        above_fuel_follower_air_gap : RegionSpecs
            Specs for the air gap above the fuel follower.
        middle_magneform_fitting : RegionSpecs
            Specs for the middle magneform fitting region.
        absorber : RegionSpecs
            Specs for the absorber region.
        above_absorber_air_gap : RegionSpecs
            Specs for the air gap above the absorber.
        upper_magneform_fitting : RegionSpecs
            Specs for the upper magneform fitting region.
        upper_air_gap : RegionSpecs
            Specs for the upper air gap region.
        upper_element_plug : RegionSpecs
            Specs for the upper element plug region.
        """

        lower_element_plug:        Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        lower_air_gap:             Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        lower_magneform_fitting:   Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        fuel_follower:             Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        above_fuel_follower_air_gap: Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        middle_magneform_fitting:  Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        absorber:                  Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        above_absorber_air_gap:    Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        upper_magneform_fitting:   Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        upper_air_gap:             Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )
        upper_element_plug:        Optional[FuelFollowerControlRod.RegionSpecs] = field(
            default_factory=lambda: FuelFollowerControlRod.RegionSpecs()
        )

        def __post_init__(self):
            self.lower_element_plug        = self.lower_element_plug        or FuelFollowerControlRod.RegionSpecs()
            self.lower_air_gap             = self.lower_air_gap             or FuelFollowerControlRod.RegionSpecs()
            self.lower_magneform_fitting   = self.lower_magneform_fitting   or FuelFollowerControlRod.RegionSpecs()
            self.fuel_follower             = self.fuel_follower             or FuelFollowerControlRod.RegionSpecs()
            self.above_fuel_follower_air_gap = (
                self.above_fuel_follower_air_gap or FuelFollowerControlRod.RegionSpecs()
            )
            self.middle_magneform_fitting  = self.middle_magneform_fitting  or FuelFollowerControlRod.RegionSpecs()
            self.absorber                  = self.absorber                  or FuelFollowerControlRod.RegionSpecs()
            self.above_absorber_air_gap    = self.above_absorber_air_gap    or FuelFollowerControlRod.RegionSpecs()
            self.upper_magneform_fitting   = self.upper_magneform_fitting   or FuelFollowerControlRod.RegionSpecs()
            self.upper_air_gap             = self.upper_air_gap             or FuelFollowerControlRod.RegionSpecs()
            self.upper_element_plug        = self.upper_element_plug        or FuelFollowerControlRod.RegionSpecs()


    @property
    def specs(self) -> Optional[Specs]:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else FuelFollowerControlRod.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


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
            bounds = Bounds(X={"min": -outer_radius, "max": outer_radius},
                            Y={"min": -outer_radius, "max": outer_radius})

        stack = element.as_stack().unionize_radial_mesh()
        segments = [(stack.segments[0], self.specs.lower_element_plug),
                    (stack.segments[1], self.specs.lower_air_gap),
                    (stack.segments[2], self.specs.lower_magneform_fitting),
                    (stack.segments[3], self.specs.fuel_follower),
                    (stack.segments[4], self.specs.above_fuel_follower_air_gap),
                    (stack.segments[5], self.specs.middle_magneform_fitting),
                    (stack.segments[6], self.specs.absorber),
                    (stack.segments[7], self.specs.above_absorber_air_gap),
                    (stack.segments[8], self.specs.upper_magneform_fitting),
                    (stack.segments[9], self.specs.upper_air_gap),
                    (stack.segments[10], self.specs.upper_element_plug)]

        stack_specs = Stack.Specs({
            segment: Stack.Segment.Specs(region_specs.target_axial_thickness,
                                         region_specs.pincell_specs)
            for segment, region_specs in segments
        })

        return build(stack, stack_specs, bounds)

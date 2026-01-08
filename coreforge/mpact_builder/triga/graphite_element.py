from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.cylindrical_pincell import CylindricalPinCell
from coreforge.mpact_builder.stack import Stack
import coreforge.geometry_elements as geometry_elements
import coreforge.geometry_elements.triga as geometry_elements_triga


@register_builder(geometry_elements_triga.GraphiteElement)
class GraphiteElement:
    """ An MPACT geometry builder class for a TRIGA Graphite Element

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
        """ Building specifications for a GraphiteElement region.

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
        """ Building specifications for GraphiteElement

        Attributes
        ----------
        lower_end_fitting : RegionSpecs
            Specs for the lower end fitting region.
        graphite : RegionSpecs
            Specs for the graphite meat region.
        upper_end_fitting : RegionSpecs
            Specs for the upper end fitting region.
        """

        lower_end_fitting: Optional[GraphiteElement.RegionSpecs] = field(
            default_factory=lambda: GraphiteElement.RegionSpecs()
        )
        graphite: Optional[GraphiteElement.RegionSpecs] = field(
            default_factory=lambda: GraphiteElement.RegionSpecs()
        )
        upper_end_fitting: Optional[GraphiteElement.RegionSpecs] = field(
            default_factory=lambda: GraphiteElement.RegionSpecs()
        )

        def __post_init__(self):
            self.lower_end_fitting = self.lower_end_fitting or GraphiteElement.RegionSpecs()
            self.graphite          = self.graphite         or GraphiteElement.RegionSpecs()
            self.upper_end_fitting = self.upper_end_fitting or GraphiteElement.RegionSpecs()


    @property
    def specs(self) -> Optional[Specs]:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else GraphiteElement.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


    def build(self,
              element: geometry_elements_triga.GraphiteElement,
              bounds:  Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a TRIGA Graphite Element

        Parameters
        ----------
        element: geometry_elements_triga.GraphiteElement
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

        lower_end_stack = element.lower_end_fitting_cone.as_stack(
            target_axial_length = self.specs.lower_end_fitting.target_axial_thickness,
            direction           = element.lower_end_fitting.direction,
        ).unionize_radial_mesh()

        upper_end_stack = element.upper_end_fitting_cone.as_stack(
            target_axial_length = self.specs.upper_end_fitting.target_axial_thickness,
            direction           = element.upper_end_fitting.direction,
        ).unionize_radial_mesh()

        mid_stack = geometry_elements.Stack(
            segments=[geometry_elements.Stack.Segment(element.graphite_pincell,
                                                      element.graphite_meat.length)],
            name=element.name,
        )

        stack = lower_end_stack + mid_stack + upper_end_stack
        stack.name = element.name

        segments = []
        segments.extend((segment, self.specs.lower_end_fitting)
                        for segment in lower_end_stack.segments)
        segments.append((mid_stack.segments[0], self.specs.graphite))
        segments.extend((segment, self.specs.upper_end_fitting)
                        for segment in upper_end_stack.segments)

        stack_specs = Stack.Specs({
            segment: Stack.Segment.Specs(region_specs.target_axial_thickness,
                                         region_specs.pincell_specs)
            for segment, region_specs in segments
        })

        return build(stack, stack_specs, bounds)

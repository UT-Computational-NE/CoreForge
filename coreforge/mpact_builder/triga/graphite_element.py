from __future__ import annotations
from typing import Optional, Tuple
from dataclasses import dataclass, field

import mpactpy

from coreforge.mpact_builder.builder import AxisBounds, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.mpact_builder import build, register_builder
from coreforge.geometry_elements.cone import OneSidedCone
from coreforge.mpact_builder.triga.core_element import CoreElement
from coreforge import geometry_elements
import coreforge.geometry_elements.triga as geometry_elements_triga


@register_builder(geometry_elements_triga.GraphiteElement)
class GraphiteElement(CoreElement[geometry_elements_triga.GraphiteElement]):
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
    class Specs(BuilderSpecs):
        """ Building specifications for GraphiteElement

        Attributes
        ----------
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all pincell segments.
        lower_end_fitting : CoreElement.SegmentSpecs
            Specs for the lower end fitting region.
        graphite : CoreElement.SegmentSpecs
            Specs for the graphite meat region.
        upper_end_fitting : CoreElement.SegmentSpecs
            Specs for the upper end fitting region.
        """

        material_specs: Optional[MaterialSpecs] = None
        lower_end_fitting: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        graphite: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )
        upper_end_fitting: Optional[CoreElement.SegmentSpecs] = field(
            default_factory = CoreElement.SegmentSpecs
        )

        def __post_init__(self):
            self.lower_end_fitting = self.lower_end_fitting or CoreElement.SegmentSpecs()
            self.graphite = self.graphite or CoreElement.SegmentSpecs()
            self.upper_end_fitting = self.upper_end_fitting or CoreElement.SegmentSpecs()


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
            bounds = Bounds(X=AxisBounds(min=-outer_radius, max=outer_radius),
                            Y=AxisBounds(min=-outer_radius, max=outer_radius))

        stack, stack_specs = self.build_stack_and_specs(element)

        return build(stack, stack_specs, bounds)


    def build_stack_and_specs(self,
                              element: geometry_elements_triga.GraphiteElement,
    ) -> Tuple[geometry_elements.Stack, Stack.Specs]:

        lower_end_options = OneSidedCone.StackOptions(
            target_axial_length=self.specs.lower_end_fitting.target_axial_thickness
        )
        upper_end_options = OneSidedCone.StackOptions(
            target_axial_length=self.specs.upper_end_fitting.target_axial_thickness
        )
        stack = element.as_stack(lower_end_options=lower_end_options,
                                 upper_end_options=upper_end_options)

        segment_specs = {}
        lower_end_count = None
        for idx, segment in enumerate(stack.segments):
            if segment.element is element.graphite_pincell:
                lower_end_count = idx
                break


        mid_start = lower_end_count
        mid_end = mid_start + 1

        for segment in stack.segments[:lower_end_count]:
            segment_specs[segment] = self.specs.lower_end_fitting

        segment_specs[stack.segments[mid_start]] = self.specs.graphite

        for segment in stack.segments[mid_end:]:
            segment_specs[segment] = self.specs.upper_end_fitting

        self._apply_material_specs(segment_specs, self.specs.material_specs)

        stack_specs = Stack.Specs(segment_specs)

        return stack, stack_specs

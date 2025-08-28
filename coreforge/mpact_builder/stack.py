from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge import geometry_elements

@register_builder(geometry_elements.Stack)
class Stack:
    """ An MPACT geometry builder class for Stack

    Parameters
    ----------
    specs: Optional[Specs]
        Specifications for building the MPACT representation of this element

    Attributes
    ----------
    specs: Optional[Specs]
        Specifications for building the MPACT representation of this element
    """

    class Segment():
        """ An MPACT geometry builder class for Stack Segments

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
            """ Building specifications for CylindricalPinCells

            Attributes
            ----------
            target_axial_thickness : float
                The target thickness of the cells in terms of segment length (cm).
                Cells will be subdivided to limit cells to within this thickness.
            builder_specs : BuilderSpecs
                Specifications for how to build the segment elements
            """

            target_axial_thickness: Optional[float] = None
            builder_specs:          Optional[BuilderSpecs] = None

            def __post_init__(self):
                if not self.target_axial_thickness:
                    self.target_axial_thickness = inf

                assert self.target_axial_thickness > 0.0, \
                    f"target_axial_thickness = {self.target_axial_thickness}"

        @property
        def specs(self) -> Specs:
            return self._specs

        @specs.setter
        def specs(self, specs: Optional[Specs]) -> None:
            self._specs = specs if specs else Stack.Segment.Specs()


        def __init__(self, specs: Optional[Specs] = None):
            self.specs = specs


        def build(self, stack_name: str, i: int, segment: geometry_elements.Stack.Segment) -> List[mpactpy.Lattice]:
            """ Method for building the lattices of a Stack Segment

            Parameters
            ----------
            stack_name : str
                The stack name corresponding to this segment
            i : int
                The stack index corresponding to this segment
            segment : geometry_elements.Stack.Segment
                The stack segment to be built

            Returns
            -------
            List[mpactpy.Lattice]
                A new MPACT lattices corresponding to this stack segment
            """

            element        = segment.element
            build_specs    = self.specs.builder_specs if self.specs else None
            mpact_geometry = build(element, build_specs)
            assert mpact_geometry.nx == 1 and mpact_geometry.ny == 1, \
                f"Unsupported Geometry! Stack: {stack_name} Segment {i}: {element.name} has multiple MPACT assemblies"
            assert mpact_geometry.nz == 1, \
                f"Unsupported Geometry! Stack: {stack_name} Segment {i}: {element.name} is not a 2D radial geometry"

            length      = segment.length
            num_subd    = max(1, int(length // self.specs.target_axial_thickness))
            subd_length = length / num_subd
            subd_points = [i * subd_length for i in range(num_subd + 1)]

            lattice = mpact_geometry.lattices[0].with_height(length)

            return [lattice.get_axial_slice(start_pos, stop_pos)
                    for start_pos, stop_pos in zip(subd_points[:-1], subd_points[1:])]


    @dataclass
    class Specs(BuilderSpecs):
        """ Building specifications for Stack

        Attributes
        ----------
        segment_specs : Dict[geometry_elements.Stack.Segment, Segment.Specs]
            Specifications for how to build the segments
        """

        segment_specs: Optional[Dict[geometry_elements.Stack.Segment, Stack.Segment.Specs]] = None

        def __post_init__(self):
            self.segment_specs = self.segment_specs if self.segment_specs else {}


    @property
    def specs(self) -> Optional[Specs]:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


    def build(self, element: geometry_elements.Stack) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a Stack

        Parameters
        ----------
        element: geometry_elements.Stack
            The geometry element to be built

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        unique_segments    = {}
        target_thicknesses = {}

        # First pass: build unique geometries
        for i, segment in enumerate(element.segments):
            segment_specs = self.specs.segment_specs.get(segment) if self.specs else Stack.Segment.Specs(None)

            if segment not in unique_segments:
                mpact_geometry = build(segment.element, segment_specs.builder_specs)

                # Validate geometry using this segment for error reporting
                assert mpact_geometry.nx == 1 and mpact_geometry.ny == 1, \
                    f"Unsupported Geometry! Stack: {element.name} Segment {i}: {segment.element.name} " + \
                        "has multiple MPACT assemblies"
                assert mpact_geometry.nz == 1, \
                    f"Unsupported Geometry! Stack: {element.name} Segment {i}: {segment.element.name} " + \
                        "is not a 2D radial geometry"

                length           = segment.length
                target_thickness = segment_specs.target_axial_thickness
                num_subd         = max(1, int(length // target_thickness))
                subd_length      = length / num_subd
                subd_points      = [i * subd_length for i in range(num_subd + 1)]

                unique_segments[segment]    = mpact_geometry
                target_thicknesses[segment] = segment_specs.target_axial_thickness

                lattice = mpact_geometry.lattices[0].with_height(length)

                unique_segments[segment] = [lattice.get_axial_slice(start_pos, stop_pos)
                                            for start_pos, stop_pos in zip(subd_points[:-1], subd_points[1:])]

        # Second pass: create lattices using cached geometries
        lattices = []
        for i, segment in enumerate(element.segments):
            lattices.extend(unique_segments[segment])

        assembly = mpactpy.Assembly(lattices)
        return mpactpy.Core([[assembly]], "360")

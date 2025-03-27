from __future__ import annotations
from typing import List, Any, Optional, Union
from math import isclose, inf
from dataclasses import dataclass

import openmc
import mpactpy
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement

class Stack(GeometryElement):
    """ A class for Z-axis aligned segments (i.e. stacks)

    Here, a stack is a collection of Z-axis aligned 'segments' which
    are 'stacked' atop one another.  The origin for a stack is located at radial
    center of the segements.

    When building MPACT Core geometries, the segments must be 2D z-axis
    extrudable radial profile.  As such, the geometry element to be extruded must
    be a 2D element, in that it's corresponding MPACT core geometry produced using
    make_mpact_core must be a single MPACT Assembly with a single MPACT Lattice with
    MPACT modules that are only a single MPACT Pin in the z-dimension.

    Attributes
    ----------
    segments : List[Segment]
        The collection of segments which comprise the stack, ordered from bottom to top
    bottom_pos : float
        The axial position of the bottom of the stack (cm)
    length : float
        The total length of the stack
    """

    class Segment():
        """ A class for the segments which comprise a Stack

        Attributes
        ----------
        element : GeometryElement
            The geometry element which occupies the segment
        length : float
            The length of the segment
        mpact_build_specs : MPACTBuildSpecs
            Specifications for building the MPACT Core representation of this element
        """

        @dataclass
        class MPACTBuildSpecs():
            """ A dataclass for holding MPACT Core building specifications"

            Attributes
            ----------
            target_axial_thicknesses : ThicknessSpec
                The target thickness of the cells in terms of segment length (cm).
                Cells will be subdivided to limit cells to within this thickness.
            """

            target_axial_thicknesses: Optional[float] = None

            def __post_init__(self):
                if not self.target_axial_thicknesses:
                    self.target_axial_thicknesses = inf

                assert self.target_axial_thicknesses > 0.0, \
                    f"target_axial_thicknesses = {self.target_axial_thicknesses}"

        @property
        def element(self) -> GeometryElement:
            return self._element

        @element.setter
        def element(self, element: GeometryElement) -> None:
            self._element = element

        @property
        def length(self) -> float:
            return self._length

        @length.setter
        def length(self, length: float) -> None:
            assert length > 0., f"length = {length}"
            self._length = length

        @property
        def mpact_build_specs(self) -> MPACTBuildSpecs:
            return self._mpact_build_specs

        @mpact_build_specs.setter
        def mpact_build_specs(self, specs: Union[MPACTBuildSpecs, None]) -> None:
            self._mpact_build_specs = specs if specs else Stack.Segment.MPACTBuildSpecs()

        def __init__(self,
                     element: GeometryElement,
                     length:  float,
                     mpact_build_specs: Optional[MPACTBuildSpecs] = None):
            self.element           = element
            self.length            = length
            self.mpact_build_specs = mpact_build_specs

        def __eq__(self, other: Any) -> bool:
            if self is other:
                return True
            return (isinstance(other, Stack.Segment) and
                    self.element == other.element    and
                    isclose(self.length, other.length, rel_tol=TOL)
                   )

        def __hash__(self) -> int:
            return hash((self.element, relative_round(self.length, TOL)))


    @property
    def segments(self) -> List[Segment]:
        return self._segments

    @segments.setter
    def segments(self, segments: List[Segment]) -> None:
        assert len(segments) > 0, f"len(segments) = {len(segments)}"
        self._segments = segments
        self._length   = sum(segment.length for segment in segments)

    @property
    def bottom_pos(self) -> float:
        return self._bottom_pos

    @bottom_pos.setter
    def bottom_pos(self, bottom_pos: float) -> None:
        self._bottom_pos = bottom_pos

    @property
    def length(self) -> float:
        return self._length

    def __init__(self, segments: List[Segment], name: str = 'stack', bottom_pos: float = 0.):
        super().__init__(name)
        self.segments   = segments
        self.bottom_pos = bottom_pos

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        return (isinstance(other, Stack)                                and
                isclose(self.bottom_pos, other.bottom_pos, rel_tol=TOL) and
                len(self.segments) == len(other.segments)               and
                all(self.segments[i] == other.segments[i] for i in range(len(self.segments)))
               )

    def __hash__(self) -> int:
        return hash((relative_round(self.bottom_pos, TOL), tuple(self.segments)))


    def make_openmc_universe(self) -> openmc.Universe:

        cells = []
        height = self.bottom_pos
        for segment in self.segments:
            segment_universe = segment.element.make_openmc_universe()
            if segment is self.segments[0] and segment is self.segments[-1]:
                region      = None
            elif segment is self.segments[0]:
                upper_bound = openmc.ZPlane(height + segment.length)
                region      = -upper_bound
            elif segment is self.segments[-1]:
                lower_bound = openmc.ZPlane(height)
                region      = +lower_bound
            else:
                lower_bound = openmc.ZPlane(height)
                upper_bound = openmc.ZPlane(height + segment.length)
                region      = +lower_bound & -upper_bound

            cells.append(openmc.Cell(fill=segment_universe, region=region))
            height += segment.length

        universe = openmc.Universe(name=self.name, cells=cells)

        return universe

    def make_mpact_core(self) -> mpactpy.Core:

        def build_lattices(i: int, segment: Stack.Segment) -> List[mpactpy.Lattice]:
            element        = segment.element
            mpact_geometry = element.make_mpact_core()
            assert mpact_geometry.nx == 1 and mpact_geometry.ny == 1, \
                f"Unsupported Geometry! Stack: {self.name} Segment {i}: {element.name} has multiple MPACT assemblies"
            assert mpact_geometry.nz == 1, \
                f"Unsupported Geometry! Stack: {self.name} Segment {i}: {element.name} is not a 2D radial geometry"

            length      = segment.length
            num_subd    = max(1, int(length // segment.mpact_build_specs.target_axial_thicknesses))
            subd_length = length / num_subd
            subd_points = [i * subd_length for i in range(num_subd + 1)]

            lattice = mpact_geometry.lattices[0].with_height(length)

            return [lattice.get_axial_slice(start_pos, stop_pos)
                    for start_pos, stop_pos in zip(subd_points[:-1], subd_points[1:])]


        lattices = [lattice for i, segment in enumerate(self.segments) for lattice in build_lattices(i, segment)]
        assembly = mpactpy.Assembly(lattices)
        return mpactpy.Core([[assembly]], "360")

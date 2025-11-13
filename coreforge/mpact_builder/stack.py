from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from math import inf
from multiprocessing import cpu_count

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.utils import build_elements
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
        num_procs : int
            The number of processes to use for parallel segment builds. If set to 1, building is serial.
            If >1, unique segments are built in parallel using chunked process pools. Defaults to 1 (serial).
        """

        segment_specs: Dict[geometry_elements.Stack.Segment, Stack.Segment.Specs] = field(default_factory=dict)
        num_procs: int = 1

        def __post_init__(self):
            assert self.num_procs > 0, f"num_procs must be > 0 (got {self.num_procs})"
            self.num_procs = min(self.num_procs, cpu_count())


    @property
    def specs(self) -> Optional[Specs]:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else Stack.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


    def build(self, element: geometry_elements.Stack, bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a Stack

        Parameters
        ----------
        element: geometry_elements.Stack
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

        segment_bounds = None
        if bounds:
            if bounds.X or bounds.Y:
                segment_bounds = Bounds(X=bounds.X, Y=bounds.Y)

        # Find unique segments and their build specs
        segment_positions = {}
        for i, segment in enumerate(element.segments):
            if segment not in segment_positions:
                segment_positions[segment] = []
            segment_positions[segment].append(i)

        unique_segments = list(segment_positions.keys())
        results         = build_elements(unique_segments,
                                         _stack_chunk_worker,
                                         self.specs.num_procs,
                                         self.specs.segment_specs,
                                         segment_bounds)

        # Validate & pitch checks, build assembly mapping
        segment_lattices = {}
        for segment, mpact_core in results.items():
            i = segment_positions[segment][0]
            assert mpact_core.nx == 1 and mpact_core.ny == 1, \
                f"Unsupported Geometry! Stack: {element.name} Segment {i}: {segment.element.name} " + \
                    "has multiple MPACT assemblies"
            assert mpact_core.nz == 1, \
                f"Unsupported Geometry! Stack: {element.name} Segment {i}: {segment.element.name} " + \
                    "is not a 2D radial geometry"

            segment_specs    = self.specs.segment_specs.get(segment)
            segment_specs    = segment_specs if segment_specs else Stack.Segment.Specs(None)
            length           = segment.length
            target_thickness = segment_specs.target_axial_thickness
            num_subd         = max(1, int(length // target_thickness))
            subd_length      = length / num_subd
            subd_points      = [i * subd_length for i in range(num_subd + 1)]

            lattice = mpact_core.lattices[0].with_height(length)

            segment_lattices[segment] = [lattice.get_axial_slice(start_pos, stop_pos)
                                         for start_pos, stop_pos in zip(subd_points[:-1], subd_points[1:])]

        # Map built segments back to their positions
        lattices = []
        for segment in element.segments:
            lattices.extend(segment_lattices[segment])

        assembly = mpactpy.Assembly(lattices)
        core     =  mpactpy.Core([[assembly]], "360")

        if bounds and bounds.Z:
            core = core.get_axial_slice(bounds.Z['min'], bounds.Z['max'])

        return core


def _stack_chunk_worker(chunk:         List[geometry_elements.Stack.Segment],
                        segment_specs: Dict[geometry_elements.Stack.Segment, Stack.Segment.Specs],
                        bounds:        Optional[Bounds] = None
    ) -> List[Tuple[geometry_elements.Stack.Segment, mpactpy.Core]]:
    """ Top-level worker for a chunk of unique segments (for parallel build).

    Parameters
    ----------
    chunk : List[geometry_elements.Stack.Segment]
        The unique stack segment entries to build in this chunk.
    segment_specs: Dict[geometry_elements.Stack.Segment, Stack.Segment.Specs]
        The segment specifications for each unique stack segment.
    bounds: Optional[Bounds]
        The spatial bounds to pass to child element builds (X and Y only, Z is not passed)
    """
    results = []
    for segment in chunk:
        build_specs = segment_specs.get(segment).builder_specs if segment_specs and segment_specs.get(segment) else None
        mpact_geometry = build(segment.element, build_specs, bounds)
        results.append((segment, mpact_geometry))
    return results

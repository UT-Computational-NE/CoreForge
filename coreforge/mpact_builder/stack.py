from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from math import inf
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

import mpactpy
import numpy as np

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
        num_procs : Optional[int]
            The number of processes to use for parallel segment builds. If set to 1 or None, building is serial.
            If >1, unique segments are built in parallel using chunked process pools. Defaults to 1 (serial).
        """

        segment_specs: Optional[Dict[geometry_elements.Stack.Segment, Stack.Segment.Specs]] = None
        num_procs: Optional[int] = None

        def __post_init__(self):
            self.segment_specs = self.segment_specs if self.segment_specs else {}

            if self.num_procs is None:
                self.num_procs = 1
            else:
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

        # Find unique segments and their build specs
        segment_positions = {}
        for i, segment in enumerate(element.segments):
            if segment not in segment_positions:
                segment_positions[segment] = []
            segment_positions[segment].append(i)

        unique_segments = segment_positions.keys()
        results         = self._build_segments(unique_segments)

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
        return mpactpy.Core([[assembly]], "360")


    def _build_segments(self, segments: List[geometry_elements.Stack.Segment]
        ) -> Dict[geometry_elements.Stack.Segment, mpactpy.Core]:
        """
        Build each unique segment only once (optionally in parallel, chunked).

        Parameters
        ----------
        segments : List[geometry_elements.Stack.Segment]
            The unique stack segment entries to build.

        Returns
        -------
        Dict[geometry_elements.Stack.Segment, mpactpy.Core]
            Mapping from unique segment to built mpact geometry.
        """
        num_unique   = len(segments)
        use_parallel = self.specs.num_procs and self.specs.num_procs > 1 and num_unique > 1

        if use_parallel:
            num_chunks = min(self.specs.num_procs, num_unique)
            chunk_indices = np.array_split(range(num_unique), num_chunks)
            work_chunks = [[segments[i] for i in indices] for indices in chunk_indices if len(indices) > 0]

            results = {}
            with ProcessPoolExecutor(max_workers=self.specs.num_procs) as executor:
                future_to_chunk_index = {
                    executor.submit(_stack_chunk_worker, chunk, self.specs.segment_specs): i
                    for i, chunk in enumerate(work_chunks)
                }
                chunk_results = [None] * len(work_chunks)
                for future in as_completed(future_to_chunk_index):
                    chunk_index = future_to_chunk_index[future]
                    chunk_results[chunk_index] = future.result()

                for chunk_result in chunk_results:
                    for segment, mpact_geometry in chunk_result:
                        results[segment] = mpact_geometry
        else:
            results = {}
            for segment in segments:
                segment_specs = self.specs.segment_specs.get(segment)
                build_specs = segment_specs.builder_specs if segment_specs else None
                results[segment] = build(segment.element, build_specs)
        return results



def _stack_chunk_worker(chunk:         List[geometry_elements.Stack.Segment],
                        segment_specs: Dict[geometry_elements.Stack.Segment, Stack.Segment.Specs]
    ) -> List[Tuple[geometry_elements.Stack.Segment, Any]]:
    """ Top-level worker for a chunk of unique segments (for parallel build).

    Parameters
    ----------
    chunk : List[geometry_elements.Stack.Segment]
        The unique stack segment entries to build in this chunk.
    """
    results = []
    for segment in chunk:
        build_specs = segment_specs.get(segment).builder_specs if segment_specs.get(segment) else None
        mpact_geometry = build(segment.element, build_specs)
        results.append((segment, mpact_geometry))
    return results

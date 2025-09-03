from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from math import isclose
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

import mpactpy
import numpy as np

from coreforge.mpact_builder.mpact_builder import register_builder, build
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge import geometry_elements


@register_builder(geometry_elements.RectLattice)
class RectLattice:
    """ An MPACT geometry builder class for RectLattice

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
        """ Building specifications for RectLattice

        Attributes
        ----------
        min_thickness : float
            The minimum allowed thickness for axial mesh unionization.  If the unionized mesh
            produces a mesh element with an axial height less than the minimum thickness,
            an error will be thrown.  This is meant as a failsafe to prevent the user from
            creating an axial mesh that is too small for MPACT. (Default: 0.0)
        element_specs : Dict[geometry_elements, BuilderSpecs]
            Specifications for how to build the lattice elements
        num_procs : Optional[int]
            The number of processes to use for parallel element builds. If set to 1 or None, building is serial.
            If >1, unique elements are built in parallel using chunked process pools. Defaults to 1 (serial).
        """

        min_thickness: Optional[float] = None
        element_specs: Optional[Dict[geometry_elements.GeometryElement, BuilderSpecs]] = None
        num_procs: Optional[int] = None


        def __post_init__(self):
            if not self.min_thickness:
                self.min_thickness = 0.0
            assert self.min_thickness >= 0.0, f"min_thickness = {self.min_thickness}"

            self.element_specs = self.element_specs if self.element_specs else {}

            if self.num_procs is None:
                self.num_procs = 1
            else:
                assert self.num_procs > 0, f"num_procs must be > 0 (got {self.num_procs})"
                self.num_procs = min(self.num_procs, cpu_count())


    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else RectLattice.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


    def build(self, element: geometry_elements.RectLattice) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a RectLattice

        Parameters
        ----------
        element: geometry_elements.RectLattice
            The geometry element to be built

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        # Find unique elements and their build specs
        element_positions = {}

        for i, row in enumerate(element.elements):
            for j, entry in enumerate(row):
                if entry:
                    if entry not in element_positions:
                        element_positions[entry] = []
                    element_positions[entry].append((i, j))

        unique_entries = element_positions.keys()
        results        = self._build_entries(unique_entries)

        # Validation & pitch checks, build assembly mapping
        unique_elements = {}
        for entry, mpact_geometry in results.items():
            positions = element_positions[entry]
            i, j = positions[0]
            assert mpact_geometry.nx == 1 and mpact_geometry.ny == 1, \
                f"Unsupported Geometry! {element.name} Row {i}, Column {j}: {entry.name} has multiple MPACT assemblies"

            assembly = mpact_geometry.assemblies[0]

            for axis, idx in zip(('X', 'Y'), (0, 1)):
                assert isclose(assembly.pitch[axis], element.pitch[idx]), (
                    f"Pitch Conflict! {element.name} Row {i}, Column {j}: {entry.name} "
                    f"{axis}-pitch {assembly.pitch[axis]} not equal to lattice {axis}-pitch {element.pitch[idx]}"
                )

            unique_elements[entry] = assembly

        # Map built assemblies back to their positions
        assemblies = []
        for i, row in enumerate(element.elements):
            assemblies.append([])
            for j, entry in enumerate(row):
                if entry:
                    assemblies[-1].append(unique_elements[entry])
                else:
                    assemblies[-1].append(None)

        return mpactpy.Core(assemblies, min_thickness=self.specs.min_thickness)


    def _build_entries(self, entries: List[geometry_elements.GeometryElement]
        ) -> Dict[geometry_elements.GeometryElement, mpactpy.Core]:
        """
        Build each unique entry only once (optionally in parallel, chunked).

        Parameters
        ----------
        entries : List[geometry_elements.GeometryElement]
            The unique geometry element entries to build.

        Returns
        -------
        Dict[geometry_elements.GeometryElement, mpactpy.Core]
            Mapping from unique entry to built mpact geometry.
        """
        num_unique   = len(entries)
        use_parallel = self.specs.num_procs and self.specs.num_procs > 1 and num_unique > 1

        if use_parallel:
            num_chunks = min(self.specs.num_procs, num_unique)
            chunk_indices = np.array_split(range(num_unique), num_chunks)
            work_chunks = [[entries[i] for i in indices] for indices in chunk_indices if len(indices) > 0]

            results = {}
            with ProcessPoolExecutor(max_workers=self.specs.num_procs) as executor:
                future_to_chunk_index = {
                    executor.submit(_rect_lattice_chunk_worker, chunk, self.specs.element_specs): i
                    for i, chunk in enumerate(work_chunks)
                }
                chunk_results = [None] * len(work_chunks)
                for future in as_completed(future_to_chunk_index):
                    chunk_index = future_to_chunk_index[future]
                    chunk_results[chunk_index] = future.result()

                for chunk_result in chunk_results:
                    for entry, mpact_geometry in chunk_result:
                        results[entry] = mpact_geometry
        else:
            results = {entry: build(entry, self.specs.element_specs.get(entry)) for entry in entries}
        return results



def _rect_lattice_chunk_worker(chunk:         List[geometry_elements.GeometryElement],
                               element_specs: Dict[geometry_elements.GeometryElement, BuilderSpecs]
    ) -> List[Tuple[geometry_elements.GeometryElement, Any]]:
    """ Top-level worker for a chunk of unique elements (for parallel build).

    Parameters
    ----------
    chunk : List[geometry_elements.GeometryElement]
        The unique geometry element entries to build in this chunk.
    element_specs : Dict[geometry_elements.GeometryElement, BuilderSpecs]
        Specifications for how to build each geometry element.

    Returns
    -------
    List[Tuple[geometry_elements.GeometryElement, Any]]
        Each tuple is (entry, built_mpact_geometry), where built_mpact_geometry is the result of build().
    """
    results = []
    for entry in chunk:
        mpact_geometry = build(entry, element_specs.get(entry))
        results.append((entry, mpact_geometry))
    return results

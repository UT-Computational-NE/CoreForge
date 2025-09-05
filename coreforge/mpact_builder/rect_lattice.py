from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from math import isclose
from multiprocessing import cpu_count

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.utils import build_elements
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
        num_procs : int
            The number of processes to use for parallel element builds. If set to 1, building is serial.
            If >1, unique elements are built in parallel using chunked process pools. Defaults to 1 (serial).
        """

        min_thickness: float = 0.0
        element_specs: Dict[geometry_elements.GeometryElement, BuilderSpecs] = field(default_factory=dict)
        num_procs: int = 1


        def __post_init__(self):
            assert self.min_thickness >= 0.0, f"min_thickness = {self.min_thickness}"
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

        # Find unique elements and their positions
        element_positions = {}

        for i, row in enumerate(element.elements):
            for j, entry in enumerate(row):
                if entry:
                    if entry not in element_positions:
                        element_positions[entry] = []
                    element_positions[entry].append((i, j))

        unique_entries = list(element_positions.keys())
        results        = build_elements(unique_entries,
                                        _rect_lattice_chunk_worker,
                                        self.specs.num_procs,
                                        self.specs.element_specs)

        # Validation & pitch checks, build assembly mapping
        mpact_geometry = {}
        for entry, mpact_core in results.items():
            i,j = element_positions[entry][0]
            assert mpact_core.nx == 1 and mpact_core.ny == 1, \
                f"Unsupported Geometry! {element.name} Row {i}, Column {j}: {entry.name} has multiple MPACT assemblies"

            assembly = mpact_core.assemblies[0]

            for axis, idx in zip(('X', 'Y'), (0, 1)):
                assert isclose(assembly.pitch[axis], element.pitch[idx]), (
                    f"Pitch Conflict! {element.name} Row {i}, Column {j}: {entry.name} "
                    f"{axis}-pitch {assembly.pitch[axis]} not equal to lattice {axis}-pitch {element.pitch[idx]}"
                )

            mpact_geometry[entry] = assembly

        # Map built assemblies back to their positions
        assemblies = []
        for i, row in enumerate(element.elements):
            assemblies.append([])
            for j, entry in enumerate(row):
                if entry:
                    assemblies[-1].append(mpact_geometry[entry])
                else:
                    assemblies[-1].append(None)

        return mpactpy.Core(assemblies, min_thickness=self.specs.min_thickness)


def _rect_lattice_chunk_worker(chunk:         List[geometry_elements.GeometryElement],
                               element_specs: Dict[geometry_elements.GeometryElement, BuilderSpecs]
    ) -> List[Tuple[geometry_elements.GeometryElement, mpactpy.Core]]:
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

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from multiprocessing import cpu_count
from math import sqrt
import os

import mpactpy

from coreforge.mpact_builder import (
    AxisBounds,
    Bounds,
    Builder,
    BuilderSpecs,
    build,
    register_builder,
)
from coreforge.mpact_builder.utils import build_elements
from coreforge import geometry_elements


@register_builder(geometry_elements.HexLattice)
class HexLattice(Builder[geometry_elements.HexLattice]):
    """ An MPACT geometry builder class for HexLattice

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
        """ Building specifications for HexLattice

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


    def build(self, element: geometry_elements.HexLattice, bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a HexLattice

        Parameters
        ----------
        element: geometry_elements.HexLattice
            The geometry element to be built
        bounds: Optional[Bounds]
            The spatial bounds for the geometry (Bounds dataclass with Z AxisBounds).
            X and Y bounds should NOT be provided as they are determined by lattice pitch.

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        if bounds and (bounds.X or bounds.Y):
            raise AssertionError("HexLattice builder does not accept X or Y bounds - they are determined by lattice pitch")

        entries = self._build_unique_entries(element, bounds)

        axial_positions = self._ring_to_axial(element)
        offset_positions = [self._axial_to_offset(axial, element.orientation) for axial in axial_positions]

        placements = []
        min_r = min_c = float("inf")
        max_r = max_c = float("-inf")
        for elem, (r, c) in zip(self._flatten_rings(element.elements), offset_positions):
            if elem and elem in entries:
                quads = entries[elem]
                base_r = r * 2
                base_c = c * 2
                if element.orientation == 'y' and (c % 2):
                    base_r += 1  # stagger down on odd columns for pointy-top
                if element.orientation == 'x' and (r % 2):
                    base_c += 1  # stagger right on odd rows for flat-top
                placements.append((base_r, base_c, quads))

                # Track min/max index values for grid sizing
                min_r = min(min_r, base_r)
                min_c = min(min_c, base_c)
                max_r = max(max_r, base_r)
                max_c = max(max_c, base_c)


        # Shifts for adjusting axial coordinates to MPACT positive-only grid
        shift_r = -min_r if min_r < 0 else 0
        shift_c = -min_c if min_c < 0 else 0

        grid_height = int(max_r + shift_r + 2)  # +2 accounts for the zero indexing of the center element
        grid_width  = int(max_c + shift_c + 2)
        assembly_map = [[None for _ in range(grid_width)] for _ in range(grid_height)]

        for base_r, base_c, quads in placements:
            r0 = int(base_r + shift_r)
            c0 = int(base_c + shift_c)
            assembly_map[r0][c0]         = quads['NW']
            assembly_map[r0][c0 + 1]     = quads['NE']
            assembly_map[r0 + 1][c0]     = quads['SW']
            assembly_map[r0 + 1][c0 + 1] = quads['SE']

        return mpactpy.Core(assembly_map, min_thickness=self.specs.min_thickness)



    def _flatten_rings(self, rings: List[List[geometry_elements.GeometryElement]]) -> List[geometry_elements.GeometryElement]:
        """Flatten a ring-ordered lattice into a single list (outer to inner).

        Parameters
        ----------
        rings : List[List[geometry_elements.GeometryElement]]
            Ring-based layout, outermost ring first.

        Returns
        -------
        List[geometry_elements.GeometryElement]
            Flattened entries in ring order.
        """
        entries: List[geometry_elements.GeometryElement] = []
        for ring in rings:
            entries.extend(ring)
        return entries

    def _ring_to_axial(self, element: geometry_elements.HexLattice) -> List[Tuple[int, int]]:
        """Convert ring-based ordering to axial (q, r) coordinates on a distance-constant ring.

        Parameters
        ----------
        element : geometry_elements.HexLattice
            Hex lattice with ring-ordered elements.

        Returns
        -------
        List[Tuple[int, int]]
            Axial coordinates corresponding to each lattice entry, ordered to match `element.elements`.

        References
        ----------
        - Red Blob Games: Hexagonal Grids
          https://www.redblobgames.com/grids/hexagons/#coordinates-axial
        """
        coords: List[Tuple[int, int]] = []
        num_rings = element.num_rings
        for ring_index, ring in enumerate(element.elements):
            radius = num_rings - ring_index - 1
            if radius == 0:
                coords.append((0, 0))
                continue
            q, r = radius, -radius  # start at (radius, -radius) to stay on ring
            directions = [(0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1), (1, 0)]
            for direction in directions:
                for _ in range(radius):
                    coords.append((q, r))
                    q += direction[0]
                    r += direction[1]
        return coords

    def _axial_to_offset(self, axial: Tuple[int, int], orientation: str) -> Tuple[int, int]:
        """Convert axial (q, r) to offset (row, col) using even-q (y) or even-r (x).

        Parameters
        ----------
        axial : Tuple[int, int]
            Axial coordinates (q, r).
        orientation : str
            Lattice orientation: 'y' for pointy-top, 'x' for flat-top.

        Returns
        -------
        Tuple[int, int]
            Offset coordinates (row, col) in the staggered grid.
        """
        q, r = axial
        if orientation == 'y':  # pointy-top
            row = r + (q - (q & 1)) // 2
            col = q
        else:  # 'x' flat-top
            row = r
            col = q + (r - (r & 1)) // 2
        return row, col


    def _build_unique_entries(self,
                              element:    geometry_elements.HexLattice,
                              bounds:     Bounds
    ) -> Dict[geometry_elements.GeometryElement, Dict[str, mpactpy.Assembly]]:
        """ Build unique lattice entries in parallel or serially

        Parameters
        ----------
        element : geometry_elements.HexLattice
            The hex lattice geometry element
        bounds: Bounds
            The spatial bounds to pass to child element builds (Z passed through)

        Returns
        -------
        Dict[geometry_elements.GeometryElement, Dict[str, mpactpy.Assembly]]
            Mapping from geometry elements to built MPACT assemblies for each quadrant ('NE', 'NW', 'SE', 'SW')
        """

        hex_height  = element.pitch if element.orientation == 'x' else element.pitch * sqrt(3.0) / 2.0
        hex_width   = element.pitch if element.orientation == 'y' else element.pitch * sqrt(3.0) / 2.0
        half_height = hex_height * 0.5
        half_width  = hex_width * 0.5

        quadrant_bounds = {'NE': Bounds(X=AxisBounds(min=0.0,        max=half_width),
                                        Y=AxisBounds(min=0.0,        max=half_height),
                                        Z=bounds.Z if bounds else None),
                           'NW': Bounds(X=AxisBounds(min=-half_width, max=0.0),
                                        Y=AxisBounds(min=0.0,         max=half_height),
                                        Z=bounds.Z if bounds else None),
                           'SE': Bounds(X=AxisBounds(min=0.0,          max=half_width),
                                        Y=AxisBounds(min=-half_height, max=0.0),
                                        Z=bounds.Z if bounds else None),
                           'SW': Bounds(X=AxisBounds(min=-half_width,  max=0.0),
                                        Y=AxisBounds(min=-half_height, max=0.0),
                                        Z=bounds.Z if bounds else None)}

        # Build quadrants for each unique entry
        quadrant_results = {}
        for quad_name, quad_bounds in quadrant_bounds.items():
            results = build_elements(self._get_unique_entries(element),
                                    _hex_lattice_chunk_worker,
                                    self.specs.num_procs,
                                    self.specs.element_specs,
                                    quad_bounds)

            # Validate that each built core has nx=1 and ny=1
            for entry, mpact_core in results.items():
                assert mpact_core.nx == 1 and mpact_core.ny == 1, \
                    f"Unsupported Geometry! {element.name} Entry {entry.name} {quad_name} " \
                        f"quadrant has multiple MPACT assemblies (nx={mpact_core.nx}, ny={mpact_core.ny})"

                # Store the quadrant result
                if entry not in quadrant_results:
                    quadrant_results[entry] = {}
                quadrant_results[entry][quad_name] = mpact_core.assemblies[0]

        return quadrant_results

    def _get_unique_entries(self, element: geometry_elements.HexLattice) -> List[Optional[geometry_elements.GeometryElement]]:
        """ Get list of unique non-None elements from the hex lattice

        Parameters
        ----------
        element : geometry_elements.HexLattice
            The hex lattice geometry element

        Returns
        -------
        List[Optional[geometry_elements.GeometryElement]]
            List of unique elements (including None if present)
        """
        unique = []
        seen = set()
        for ring in element.elements:
            for elem in ring:
                if elem is not None and id(elem) not in seen:
                    seen.add(id(elem))
                    unique.append(elem)
        return unique


def _hex_lattice_chunk_worker(chunk:         List[geometry_elements.GeometryElement],
                              element_specs: Dict[geometry_elements.GeometryElement, BuilderSpecs],
                              bounds:        Optional[Bounds] = None
    ) -> List[Tuple[geometry_elements.GeometryElement, mpactpy.Core]]:
    """ Top-level worker for a chunk of unique elements (for parallel build).

    Parameters
    ----------
    chunk : List[geometry_elements.GeometryElement]
        The unique geometry element entries to build in this chunk.
    element_specs : Dict[geometry_elements.GeometryElement, BuilderSpecs]
        Specifications for how to build each geometry element.
    bounds: Optional[Bounds]
        The spatial bounds to pass to child element builds (X, Y determined by lattice pitch; Z passed through)

    Returns
    -------
    List[Tuple[geometry_elements.GeometryElement, Any]]
        Each tuple is (entry, built_mpact_geometry), where built_mpact_geometry is the result of build().
    """
    results = []
    for entry in chunk:
        mpact_geometry = build(entry, element_specs.get(entry), bounds)
        results.append((entry, mpact_geometry))
    return results

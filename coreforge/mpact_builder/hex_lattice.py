from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from multiprocessing import cpu_count
from math import sqrt

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.utils import build_elements
from coreforge import geometry_elements


@register_builder(geometry_elements.HexLattice)
class HexLattice:
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


    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else HexLattice.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


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

        # Assert that X and Y bounds are not provided
        if bounds and (bounds.X or bounds.Y):
            raise AssertionError("HexLattice builder does not accept X or Y bounds - they are determined by lattice pitch")

        pitch      = element.pitch
        hex_height = pitch if element.orientation == 'x' else pitch * sqrt(3.0) / 2.0
        hex_width  = pitch if element.orientation == 'y' else pitch * sqrt(3.0) / 2.0

        quadrant_results = self._build_unique_entries(element, hex_height, hex_width, bounds)

        num_rings = element.num_rings
        grid_width  = 2 * (2*num_rings - 1)
        grid_height = 2 * (2*num_rings - 1)

        # Initialize grid with None
        assembly_map = [[None for _ in range(grid_width)] for _ in range(grid_height)]

        # Process each ring from outer to inner
        ring_index = 0
        for ring_elements in element.elements:
            if len(ring_elements) == 1:
                # Center element
                center_row = grid_height // 2 - 1
                center_col = grid_width // 2 - 1
                elem = ring_elements[0]
                if elem and elem in quadrant_results:
                    quads = quadrant_results[elem]
                    assembly_map[center_row][center_col]         = quads['NW']
                    assembly_map[center_row][center_col + 1]     = quads['NE']
                    assembly_map[center_row + 1][center_col]     = quads['SW']
                    assembly_map[center_row + 1][center_col + 1] = quads['SE']
            else:
                # Ring elements - distribute around center
                num_face_elements = len(ring_elements) // 6
                center_row = grid_height // 2 - 1
                center_col = grid_width // 2 - 1

                idx = 0
                # Process each of the 6 faces
                for face in range(6):
                    for elem_in_face in range(num_face_elements):
                        elem = ring_elements[idx]
                        idx += 1

                        # Calculate position offset based on orientation
                        row_offset, col_offset = self._calculate_hex_position_offset(
                            element.orientation, face, ring_index, elem_in_face, num_face_elements
                        )

                        row = center_row + row_offset
                        col = center_col + col_offset

                        if elem and elem in quadrant_results:
                            quads = quadrant_results[elem]
                            if 0 <= row < grid_height - 1 and 0 <= col < grid_width - 1:
                                assembly_map[row][col]         = quads['NW']
                                assembly_map[row][col + 1]     = quads['NE']
                                assembly_map[row + 1][col]     = quads['SW']
                                assembly_map[row + 1][col + 1] = quads['SE']
            ring_index += 1

        return mpactpy.Core(assembly_map, min_thickness=self.specs.min_thickness)



    def _calculate_hex_position_offset(self,
                                       orientation: str,
                                       face: int,
                                       ring_index: int,
                                       elem_in_face: int,
                                       num_face_elements: int) -> Tuple[int, int]:
        """ Calculate the row and column offset for a hex element in the rectangular grid

        Parameters
        ----------
        orientation : str
            The hex orientation ('x' or 'y')
        face : int
            The face index (0-5)
        ring_index : int
            The index of the current ring (0 = outermost)
        elem_in_face : int
            The position of the element within the current face
        num_face_elements : int
            The number of elements per face in this ring

        Returns
        -------
        Tuple[int, int]
            (row_offset, col_offset) in units of assemblies (not quadrants)
        """
        if orientation == 'x':
            if face == 0:  # SE face
                row_offset = (ring_index + elem_in_face + 1) * 2
                col_offset = -(ring_index + elem_in_face) * 2
            elif face == 1:  # S face
                row_offset = (ring_index + num_face_elements) * 2
                col_offset = -(ring_index + num_face_elements - elem_in_face - 1) * 2
            elif face == 2:  # SW face
                row_offset = (ring_index + num_face_elements - elem_in_face - 1) * 2
                col_offset = (elem_in_face + 1) * 2
            elif face == 3:  # NW face
                row_offset = -(ring_index + elem_in_face + 1) * 2
                col_offset = (ring_index + elem_in_face) * 2
            elif face == 4:  # N face
                row_offset = -(ring_index + num_face_elements) * 2
                col_offset = (ring_index + num_face_elements - elem_in_face - 1) * 2
            else:  # NE face (face == 5)
                row_offset = -(ring_index + num_face_elements - elem_in_face - 1) * 2
                col_offset = -(elem_in_face + 1) * 2

        else:  # 'y' orientation
            if face == 0:  # NE face
                row_offset = -(ring_index + elem_in_face) * 2 - 2
                col_offset = (elem_in_face + 1) * 2
            elif face == 1:  # E face
                row_offset = -(ring_index - elem_in_face) * 2
                col_offset = (ring_index + num_face_elements) * 2
            elif face == 2:  # SE face
                row_offset = (elem_in_face + 1) * 2
                col_offset = (ring_index + num_face_elements - elem_in_face - 1) * 2
            elif face == 3:  # SW face
                row_offset = (ring_index + elem_in_face) * 2 + 2
                col_offset = -(elem_in_face + 1) * 2
            elif face == 4:  # W face
                row_offset = (ring_index - elem_in_face) * 2
                col_offset = -(ring_index + num_face_elements) * 2
            else:  # NW face (face == 5)
                row_offset = -(elem_in_face + 1) * 2
                col_offset = -(ring_index + num_face_elements - elem_in_face - 1) * 2

        return row_offset, col_offset


    def _build_unique_entries(self,
                              element:    geometry_elements.HexLattice,
                              hex_height: float,
                              hex_width:  float,
                              bounds:     Bounds
    ) -> Dict[geometry_elements.GeometryElement, Dict[str, mpactpy.Assembly]]:
        """ Build unique lattice entries in parallel or serially

        Parameters
        ----------
        element : geometry_elements.HexLattice
            The hex lattice geometry element
        hex_height : float
            The height of each hex cell
        hex_width : float
            The width of each hex cell
        bounds: Bounds
            The spatial bounds to pass to child element builds (Z passed through)

        Returns
        -------
        Dict[geometry_elements.GeometryElement, Dict[str, mpactpy.Assembly]]
            Mapping from geometry elements to built MPACT assemblies for each quadrant ('NE', 'NW', 'SE', 'SW')
        """

        unique_entries = self._get_unique_entries(element)

        half_height     = hex_height * 0.5
        half_width      = hex_width * 0.5
        quadrant_bounds = {'NE': Bounds(X={'min': 0.0, 'max': half_width},
                                        Y={'min': 0.0, 'max': half_height},
                                        Z=bounds.Z if bounds else None),
                           'NW': Bounds(X={'min': -half_width, 'max': 0.0},
                                        Y={'min': 0.0,         'max': half_height},
                                        Z=bounds.Z if bounds else None),
                           'SE': Bounds(X={'min': 0.0,          'max': half_width},
                                        Y={'min': -half_height, 'max': 0.0},
                                        Z=bounds.Z if bounds else None),
                           'SW': Bounds(X={'min': -half_width,  'max': 0.0},
                                        Y={'min': -half_height, 'max': 0.0},
                                        Z=bounds.Z if bounds else None)}

        # Build quadrants for each unique entry
        quadrant_results = {}
        for quad_name, quad_bounds in quadrant_bounds.items():
            results = build_elements(unique_entries,
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

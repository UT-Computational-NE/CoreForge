from __future__ import annotations
from typing import List, Optional, Any
from math import isclose

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.lattice import Lattice
from coreforge.materials.material import Material
from coreforge.utils import cartesian_to_ring

class HexLattice(Lattice):
    """ A concrete lattice class for hexagonal lattices

    When initializing, users should provide either a cartesian map
    or ring map, but not both.

    Parameters
    ----------
    name : str
        A name for the geometry element
    pitch : float
        The pitch of the lattice cell (cm)
    outer_material : Material
        The material which fills the region outside the lattice as well
        those cells of that lattice not specifically filled with a GeometryElement
    ring_map : Optional[List[List[GeometryElement]]]
        The collection of elements as represented via a ring map. The first dimension
        must correspond to rings (outer-to-inner) and the second dimension correspond
        to the individual elements of each ring, ordered from the “top point” for y-oriented lattices,
        or the “east point” for x-oriented lattices and proceed in a clockwise fashion.
    cartesian_map : Optional[List[List[GeometryElement]]]
        The collection of elements as represented via a cartesian map
        Below are examples of acceptable "cartesian" layouts:

        Y-oriented
                   [[         T,         ],
                    [     T,      T,     ],
                    [ T,      T,      T, ],
                    [     T,      T,     ],
                    [ T,      T,      T, ],
                    [     T,      T,     ],
                    [ T,      T,      T, ],
                    [     T,      T,     ],
                    [         T,         ]]

        X-oriented
                   [[     T,  T,  T,     ],

                    [   T,  T,  T,  T,   ],

                    [ T,  T,  T,  T,  T, ],

                    [   T,  T,  T,  T,   ],

                    [     T,  T,  T,     ]]

    Attributes
    ----------
    pitch : float
        The pitch of the lattice cell (cm)
    num_rings : int
        The number of radial rings the lattice has
    orientation : str
        The orientation of the hexagon, with 'x' meaning that two sides
        are parallel with the x-axis and 'y' meaning that two sides are
        parallel with the y-axis
    elements : List[List[GeometryElement]]
        The geometry elements which fill the lattice, specified by rings,
        with the first dimension corresponding to rings (outer-to-inner)
        and the second dimension corresponding to the individual elements
        of each ring, ordered from the “top point” for y-oriented lattices,
        or the “east point” for x-oriented lattices and proceed in a clockwise fashion.
    """

    @property
    def pitch(self) -> float:
        return self._pitch

    @pitch.setter
    def pitch(self, pitch: float) -> None:
        assert pitch > 0., f"pitch = {pitch}"
        self._pitch = pitch

    @property
    def num_rings(self) -> int:
        return self._num_rings

    @property
    def orientation(self) -> str:
        return self._orientation

    @orientation.setter
    def orientation(self, orientation: str) -> None:
        assert orientation in ['x', 'y', 'X', 'Y']
        orientation = 'x' if orientation == 'X' else orientation
        orientation = 'y' if orientation == 'Y' else orientation
        self._orientation = orientation

    @property
    def elements(self) -> List[List[GeometryElement]]:
        return self._elements

    @elements.setter
    def elements(self, elements: List[List[GeometryElement]]) -> None:

        num_rings = len(elements)
        inner_most_ring = elements[-1]

        assert len(inner_most_ring) == 1, f"len(inner_most_ring) = {len(inner_most_ring)}"
        for i, ring in enumerate(elements[:-1]):
            assert len(ring) == 6*(num_rings-1-i), \
                f"i = {i}, len(ring) = {len(ring)}"

        self._elements  = elements
        self._num_rings = num_rings


    def __init__(self,
                 pitch:          float,
                 outer_material: Material,
                 name:           str = "hex_lattice",
                 orientation:    str = 'y',
                 cartesian_map:  Optional[List[List[GeometryElement]]] = None,
                 ring_map:       Optional[List[List[GeometryElement]]] = None):

        super().__init__(name, outer_material)

        assert cartesian_map or ring_map
        assert not(cartesian_map and ring_map)

        self.pitch       = pitch
        self.orientation = orientation
        self.elements    = ring_map if ring_map else cartesian_to_ring(layout      = cartesian_map,
                                                                       orientation = orientation)


    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        return (isinstance(other, HexLattice)                 and
                isclose(self.pitch, other.pitch, rel_tol=TOL) and
                self.outer_material == other.outer_material   and
                self.num_rings == other.num_rings             and
                all(self.elements[i][j] == other.elements[i][j]
                    for i in range(self.num_rings) for j in range(len(self.elements[i])))
                )

    def __hash__(self) -> int:
        return hash((relative_round(self.pitch, TOL),
                     self.outer_material,
                     tuple(tuple(row) for row in self.elements)))


    def make_openmc_universe(self) -> openmc.Universe:

        outer_universe = openmc.Universe(cells=[openmc.Cell(fill=self.outer_material.openmc_material)])

        universes = []
        for ring in self.elements:
            universes.append([])
            for element in ring:
                universe = element.make_openmc_universe() if element else outer_universe
                universes[-1].append(universe)

        lattice_universe             = openmc.HexLattice()
        lattice_universe.orientation = self.orientation
        lattice_universe.outer       = outer_universe
        lattice_universe.pitch       = [self.pitch]
        lattice_universe.center      = (0., 0.)
        lattice_universe.universes   = universes

        return lattice_universe

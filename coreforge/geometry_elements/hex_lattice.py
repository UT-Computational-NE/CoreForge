from __future__ import annotations
from typing import List, Any, Literal
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.lattice import Lattice
from coreforge.materials.material import Material
from coreforge.utils import offset_to_ring

class HexLattice(Lattice):
    """ A concrete lattice class for hexagonal lattices

    This class represents a hexagonal lattice using a ring-based internal structure.
    Users can initialize the lattice by supplying either a ring-based map or an
    offset-style 2D layout. The `map_type` argument determines how the input `elements`
    list is interpreted.

    Parameters
    ----------
    name : str
        A name for the geometry element
    pitch : float
        The pitch of the lattice cell (cm)
    outer_material : Material
        The material which fills the region outside the lattice as well
        those cells of that lattice not specifically filled with a GeometryElement
    elements : List[List[GeometryElement]]
        The lattice elements, specified using either a ring-based map or an offset-style layout.
        See `map_type` for details.
    orientation : Orientation
        The orientation of the hexagon, with 'x' meaning that two sides
        are parallel with the x-axis and 'y' meaning that two sides are
        parallel with the y-axis
    map_type : MapType
        Determines how to interpret the `elements` list. Must be either 'ring' or 'offset'.
        Default is 'offset'.

        - 'ring': The `elements` list is interpreted as a ring map, where:
            * The outer list indexes concentric rings from outermost to innermost.
            * Each ring contains elements ordered clockwise:
                - For 'y'-oriented lattices, the order starts at the "top point".
                - For 'x'-oriented lattices, the order starts at the "east point".

            Example:
                [[1,2,3,4,5,6,7,8,9,10,11,12],  # Outer ring
                 [13,14,15,16,17,18],           # Middle ring
                 [19]]                          # Center element

        - 'offset': The `elements` list is interpreted as an offset-style layout:
            * The layout mimics offset hex grid coordinates using a 2D array (rows of staggered elements).
            * This form is more intuitive for manual definition or visualization, but is internally
              converted to a ring map using `offset_to_ring()`.

            This is inspired by offset coordinates described here:
            https://www.redblobgames.com/grids/hexagons/#coordinates-offset

            Y-oriented (pointy-top):
                [[         1,         ],
                 [    12,      2,     ],
                 [11,     13,      3, ],
                 [    18,     14,     ],
                 [10,     19,      4, ],
                 [    17,     15,     ],
                 [ 9,     16,      5, ],
                 [     8,      6,     ],
                 [         7,         ]]

            X-oriented (flat-top):
                [[     9, 10, 11,     ],

                 [   8, 17, 18, 12,   ],

                 [ 7, 16, 19, 13,  1, ],

                 [   6, 15, 14,  2,   ],

                 [     5,  4,  3,     ]]

    Attributes
    ----------
    pitch : float
        The pitch of the lattice cell (cm)
    num_rings : int
        The number of radial rings the lattice has
    orientation : str
        The orientation of the hexagon ('x' or 'y').
    elements : List[List[GeometryElement]]
        The internal ring-based representation of the hex lattice.
        Outer list corresponds to rings (outer-to-inner), and each ring is ordered clockwise.
    """

    Orientation = Literal['x', 'y', 'X', 'Y']
    MapType = Literal['offset', 'ring']

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
    def orientation(self, orientation: Orientation) -> None:
        assert orientation in ['x', 'y', 'X', 'Y']
        orientation = 'x' if orientation == 'X' else orientation
        orientation = 'y' if orientation == 'Y' else orientation
        self._orientation = orientation.lower()

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
                 elements:       List[List[GeometryElement]],
                 name:           str = "hex_lattice",
                 orientation:    Orientation = 'y',
                 map_type:       MapType = 'offset'):

        super().__init__(name, outer_material)

        assert map_type in ['offset', 'ring']

        self.pitch       = pitch
        self.orientation = orientation
        self.elements    = elements if map_type == 'ring' else offset_to_ring(elements,
                                                                              orientation)

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

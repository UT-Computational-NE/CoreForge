from __future__ import annotations
from typing import List, Union, Tuple, Any
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.lattice import Lattice
from coreforge.materials.material import Material

class RectLattice(Lattice):
    """ A concrete lattice class for rectangular lattices

    Parameters
    ----------
    name : str
        A name for the geometry element
    pitch : Union[float, Tuple[float, float]]
        The X-Y pair which describe the pitch of the lattice cell (cm).  When assigning,
        users may provide either a single value for square pitches, or an X-Y Tuple for
        rectangular pitches
    elements : List[List[GeometryElement]]
        The geometry elements which fill the lattice, specified by cartesian
        row / columns, where the first dimension corresponds to the rows
        (top-to-bottom) and the second dimension correspond to the columns of a row.
    outer_material : Material
        The material which fills the region outside the lattice as well
        those cells of that lattice not specifically filled with a GeometryElement

    Attributes
    ----------
    pitch : Tuple[float, float]
        The lattice pitch in the x- and y- directions, respectively (cm).
    shape : Tuple[int, int]
        The number of lattice cells in the x- and y- directions, respectively
    elements : List[List[GeometryElement]]
        The geometry elements which fill the lattice.  The first dimension corresponds
        to the rows (top-to-bottom) and the second dimension correspond to the columns of a row.
    """

    @property
    def pitch(self) -> Tuple[float, float]:
        return self._pitch

    @pitch.setter
    def pitch(self, pitch: Union[float, Tuple[float, float]]) -> None:
        pitch = (pitch, pitch) if isinstance(pitch, float) else pitch
        assert pitch[0] > 0.0 and pitch[1] > 0.0, f"pitch = {pitch}"
        self._pitch = pitch

    @property
    def shape(self) -> Tuple[int, int]:
        return self._shape

    @property
    def elements(self) -> List[List[GeometryElement]]:
        return self._elements

    @elements.setter
    def elements(self, elements: List[List[GeometryElement]]) -> None:

        shape = (len(elements), len(elements[0]))

        assert shape[0] > 0, f"Number of row = {shape[0]}"
        assert shape[1] > 0, f"Number of columns = {shape[1]}"
        assert all(len(row) == shape[1] for row in elements), \
            "Number of columns not consistent on all rows"

        self._elements = elements
        self._shape = shape


    def __init__(self,
                 pitch:             Union[float, Tuple[float, float]],
                 outer_material:    Material,
                 elements:          List[List[GeometryElement]],
                 name:              str = "rect_lattice"):

        super().__init__(name, outer_material)
        self.pitch             = pitch
        self.elements          = elements


    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        return (isinstance(other, RectLattice)                      and
                isclose(self.pitch[0], other.pitch[0], rel_tol=TOL) and
                isclose(self.pitch[1], other.pitch[1], rel_tol=TOL) and
                self.outer_material == other.outer_material         and
                self.shape[0] == other.shape[0]                     and
                self.shape[1] == other.shape[1]                     and
                all(self.elements[i][j] == other.elements[i][j]
                    for i in range(self.shape[0]) for j in range(self.shape[1]))
                )

    def __hash__(self) -> int:
        return hash((relative_round(self.pitch[0], TOL),
                     relative_round(self.pitch[1], TOL),
                     self.outer_material,
                     tuple(tuple(row) for row in self.elements)))

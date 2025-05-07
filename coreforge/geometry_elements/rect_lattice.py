from __future__ import annotations
from typing import List, Union, Tuple, Any, Optional
from math import isclose
from dataclasses import dataclass

import openmc
import mpactpy
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
    mpact_build_specs : Optional[MPACTBuildSpecs]
        Specifications for building the MPACT Core representation of this element

    Attributes
    ----------
    pitch : Tuple[float, float]
        The lattice pitch in the x- and y- directions, respectively (cm).
    shape : Tuple[int, int]
        The number of lattice cells in the x- and y- directions, respectively
    elements : List[List[GeometryElement]]
        The geometry elements which fill the lattice.  The first dimension corresponds
        to the rows (top-to-bottom) and the second dimension correspond to the columns of a row.
    mpact_build_specs : Optional[MPACTBuildSpecs]
        Specifications for building the MPACT Core representation of this element
    """

    @dataclass
    class MPACTBuildSpecs():
        """ A dataclass for holding MPACT Core building specifications"

        Attributes
        ----------
        min_thickness : float
            The minimum allowed thickness for axial mesh unionization.  If the unionized mesh
            produces a mesh element with an axial height less than the minimum thickness,
            an error will be thrown.  This is meant as a failsafe to prevent the user from
            creating an axial mesh that is too small for MPACT. (Default: 0.0)
        """

        min_thickness: Optional[float] = None

        def __post_init__(self):
            if not self.min_thickness:
                self.min_thickness = 0.0

            assert self.min_thickness >= 0.0, f"min_thickness = {self.min_thickness}"

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

    @property
    def mpact_build_specs(self) -> MPACTBuildSpecs:
        return self._mpact_build_specs

    @mpact_build_specs.setter
    def mpact_build_specs(self, specs: Optional[MPACTBuildSpecs]) -> None:
        self._mpact_build_specs = specs if specs else RectLattice.MPACTBuildSpecs()


    def __init__(self,
                 pitch:             Union[float, Tuple[float, float]],
                 outer_material:    Material,
                 elements:          List[List[GeometryElement]],
                 name:              str = "rect_lattice",
                 mpact_build_specs: Optional[MPACTBuildSpecs] = None):

        super().__init__(name, outer_material)
        self.pitch             = pitch
        self.elements          = elements
        self.mpact_build_specs = mpact_build_specs


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


    def make_openmc_universe(self) -> openmc.Universe:

        outer_universe = openmc.Universe(cells=[openmc.Cell(fill=self.outer_material.openmc_material)])

        universes = []
        for row in self.elements:
            universes.append([])
            for element in row:
                universe = element.make_openmc_universe() if element else outer_universe
                universes[-1].append(universe)

        lattice_universe            = openmc.RectLattice()
        lattice_universe.outer      = outer_universe
        lattice_universe.pitch      = self.pitch
        lattice_universe.lower_left = (-(self.pitch[0]*self.shape[1])/2.,
                                       -(self.pitch[1]*self.shape[0])/2.)
        lattice_universe.universes  = universes

        return lattice_universe

    def make_mpact_core(self) -> mpactpy.Core:

        assemblies = []
        for i, row in enumerate(self.elements):
            assemblies.append([])
            for j, element in enumerate(row):
                if element:
                    mpact_geometry = element.make_mpact_core()

                    assert mpact_geometry.nx == 1 and mpact_geometry.ny == 1, \
                    f"Unsupported Geometry! {self.name} Row {i}, Column {j}: {element.name} has multiple MPACT assemblies"

                    assembly = mpact_geometry.assemblies[0]

                    for axis, idx in zip(('X', 'Y'), (0, 1)):
                        assert isclose(assembly.pitch[axis], self.pitch[idx]), (
                            f"Pitch Conflict! {self.name} Row {i}, Column {j}: {element.name} "
                            f"{axis}-pitch {assembly.pitch[axis]} not equal to lattice {axis}-pitch {self.pitch[idx]}"
                        )

                    assemblies[-1].append(mpact_geometry.assemblies[0])
                else:
                    assemblies[-1].append(None)

        return mpactpy.Core(assemblies, min_thickness=self.mpact_build_specs.min_thickness)

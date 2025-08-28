from __future__ import annotations
from typing import Dict, Optional
from dataclasses import dataclass
from math import isclose

import mpactpy

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
        """

        min_thickness: Optional[float] = None
        element_specs: Optional[Dict[geometry_elements.GeometryElement, BuilderSpecs]] = None

        def __post_init__(self):
            if not self.min_thickness:
                self.min_thickness = 0.0
            assert self.min_thickness >= 0.0, f"min_thickness = {self.min_thickness}"

            self.element_specs = self.element_specs if self.element_specs else {}


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
        unique_elements = {}
        element_positions = {}

        for i, row in enumerate(element.elements):
            for j, entry in enumerate(row):
                if entry:
                    if entry not in element_positions:
                        element_positions[entry] = []
                    element_positions[entry].append((i, j))

        # Build each unique element only once
        for entry, positions in element_positions.items():
            mpact_geometry = build(entry, self.specs.element_specs.get(entry))

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

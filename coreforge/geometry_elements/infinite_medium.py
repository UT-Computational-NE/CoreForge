from __future__ import annotations
from typing import Any

import openmc
import mpactpy

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material

class InfiniteMedium(GeometryElement):
    """ A class for infinite media regions

    This element is useful for specifying regions filled
    with homogeneous media

    Attributes
    ----------
    material : Material
        The material of the infinite medium
    """

    @property
    def material(self) -> Material:
        return self._material

    @material.setter
    def material(self, material: Material) -> None:
        self._material = material

    def __init__(self, material: Material, name: str = 'infinite_medium'):

        self.name    = name
        self.material = material

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return(isinstance(other, InfiniteMedium) and
               self.material == other.material
              )

    def __hash__(self) -> int:
        return hash(self.material)

    def make_openmc_universe(self) -> openmc.Universe:

        universe = openmc.Universe(name=self.name, cells=[openmc.Cell(fill=self.material.openmc_material)])
        return universe

    def make_mpact_core(self) -> mpactpy.Core:
        raise NotImplementedError("Cannot make an MPACT Core for an infinite medium")

from abc import abstractmethod
from typing import List

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials.material import Material

class Lattice(GeometryElement):
    """ An abstract class for 2D Lattice of geometry elements

    Attributes
    ----------
    elements : List[List[GeometryElement]]
        The geometry elements which fill the lattice
    outer_material : Material
        The material which fills the region outside the lattice as well
        those cells of that lattice not specifically filled with a GeometryElement
    """

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @outer_material.setter
    def outer_material(self, outer_material: Material) -> None:
        self._outer_material = outer_material

    @property
    @abstractmethod
    def elements(self) -> List[List[GeometryElement]]:
        pass

    @elements.setter
    @abstractmethod
    def elements(self, elements: List[List[GeometryElement]]) -> None:
        pass


    def __init__(self, name: str, outer_material: Material):
        self.outer_material = outer_material
        super().__init__(name)

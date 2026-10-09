from __future__ import annotations
from typing import Any, List

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.overlay import register_overlay
from coreforge.materials import Material, unique_materials

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

        super().__init__(name)
        self.material = material

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return(isinstance(other, InfiniteMedium) and
               self.material == other.material
              )

    def __hash__(self) -> int:
        return hash(self.material)

    def get_materials(self) -> List[Material]:
        return unique_materials([self.material])


@register_overlay(GeometryElement, InfiniteMedium)
def _overlay_infinite_medium(lower: GeometryElement,
                             upper: InfiniteMedium) -> InfiniteMedium:
    """Replace lower-priority geometry with an infinite medium.

    Parameters
    ----------
    lower : GeometryElement
        Lower-priority geometry, deep-copied by the overlay dispatcher.
    upper : InfiniteMedium
        Higher-priority medium, deep-copied by the overlay dispatcher.

    Returns
    -------
    InfiniteMedium
        The upper medium, replacing all finite regions of the lower geometry.
    """
    return upper

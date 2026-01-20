from __future__ import annotations

from math import isclose
from typing import List, Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material, Water, unique_materials


class Pool(GeometryElement):
    """TRIGA pool.

    Parameters
    ----------
    radius : float
        Pool radius [cm].
    height : float
        Pool height [cm].
    material : Material, optional
        Pool material. Defaults to ``Water()``.
    name : str, optional
        Name for this pool element. Defaults to ``"pool"``.

    Attributes
    ----------
    radius : float
        Pool radius [cm].
    height : float
        Pool height [cm].
    material : Material
        Pool material.
    """

    @property
    def radius(self) -> float:
        return self._radius

    @property
    def height(self) -> float:
        return self._height

    @property
    def material(self) -> Material:
        return self._material

    def __init__(self,
                 radius: float,
                 height: float,
                 material: Optional[Material] = None,
                 name: str = "pool") -> None:
        super().__init__(name)
        assert radius > 0.0, "Pool radius must be positive."
        assert height > 0.0, "Pool height must be positive."

        self._radius = radius
        self._height = height
        self._material = material or Water()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, Pool) and
            isclose(self.radius, other.radius, rel_tol=TOL) and
            isclose(self.height, other.height, rel_tol=TOL) and
            self.material == other.material
        )

    def __hash__(self) -> int:
        return hash((
            relative_round(self.radius, TOL),
            relative_round(self.height, TOL),
            self.material,
        ))

    def get_materials(self) -> List[Material]:
        return unique_materials([self.material])

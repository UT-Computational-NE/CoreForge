from __future__ import annotations

from math import isclose
from typing import Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Al6061T6, Material


class Shroud(GeometryElement):
    """TRIGA NETL shroud geometry element.

    Parameters
    ----------
    thickness : float
        Shroud wall thickness [cm].
    height : float
        Axial height of the shroud [cm].
    primary_hex_inner_radius : float
        Inradius of the primary (y-oriented) hex that forms part of the shroud wall.
    rotated_hex_inner_radius : float
        Inradius of the rotated hex that, together with the primary hex, forms the wall.
    material : Material, optional
        Shroud material (defaults to ``Al6061T6``).
    name : str, optional
        Name for this shroud element.
    """

    @property
    def thickness(self) -> float:
        return self._thickness

    @property
    def height(self) -> float:
        return self._height

    @property
    def primary_hex_inner_radius(self) -> float:
        return self._primary_hex_inner_radius

    @property
    def rotated_hex_inner_radius(self) -> float:
        return self._rotated_hex_inner_radius

    @property
    def material(self) -> Material:
        return self._material

    def __init__(self,
                 thickness: float,
                 height: float,
                 primary_hex_inner_radius: float,
                 rotated_hex_inner_radius: Optional[float] = None,
                 material: Optional[Material] = None,
                 name: str = "shroud") -> None:
        super().__init__(name)
        assert thickness > 0.0, "Shroud thickness must be positive."
        assert height > 0.0, "Shroud height must be positive."
        assert primary_hex_inner_radius > 0.0, "Primary hex inradius must be positive."
        rotated_hex_inner_radius = rotated_hex_inner_radius or primary_hex_inner_radius
        assert rotated_hex_inner_radius > 0.0, "Rotated hex inradius must be positive."

        self._thickness = thickness
        self._height = height
        self._primary_hex_inner_radius = primary_hex_inner_radius
        self._rotated_hex_inner_radius = rotated_hex_inner_radius
        self._material = material or Al6061T6()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, Shroud)
            and isclose(self.thickness, other.thickness, rel_tol=TOL)
            and isclose(self.height, other.height, rel_tol=TOL)
            and isclose(self.primary_hex_inner_radius, other.primary_hex_inner_radius, rel_tol=TOL)
            and isclose(self.rotated_hex_inner_radius, other.rotated_hex_inner_radius, rel_tol=TOL)
            and self.material == other.material
        )

    def __hash__(self) -> int:
        return hash((
            relative_round(self.thickness, TOL),
            relative_round(self.height, TOL),
            relative_round(self.primary_hex_inner_radius, TOL),
            relative_round(self.rotated_hex_inner_radius, TOL),
            self.material,
        ))

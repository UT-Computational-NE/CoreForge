from __future__ import annotations

from math import isclose
from typing import Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Al6061T6, Material
from coreforge.shapes.hexagon import Hexagon


class Shroud(GeometryElement):
    """TRIGA NETL shroud geometry element.

    Parameters
    ----------
    thickness : float
        Shroud wall thickness [cm].
    height : float
        Axial height of the shroud [cm].
    outer_hex_inner_radius : float
        Outer (large) hexagon inradius [cm].
    inner_hex_inner_radius : float
        Inner (small) hexagon inradius [cm].
    inner_hex : Hexagon
        Hexagon shape for the inner opening (derived).
    outer_hex : Hexagon
        Hexagon shape for the outer boundary (derived).
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
    def outer_hex_inner_radius(self) -> float:
        return self._outer_hex_inner_radius

    @property
    def inner_hex_inner_radius(self) -> float:
        return self._inner_hex_inner_radius

    @property
    def inner_hex(self) -> Hexagon:
        return self._inner_hex

    @property
    def outer_hex(self) -> Hexagon:
        return self._outer_hex

    @property
    def material(self) -> Material:
        return self._material

    def __init__(self,
                 thickness: float,
                 height: float,
                 outer_hex_inner_radius: float,
                 inner_hex_inner_radius: float,
                 material: Optional[Material] = None,
                 name: str = "shroud") -> None:
        super().__init__(name)
        assert thickness > 0.0, "Shroud thickness must be positive."
        assert height > 0.0, "Shroud height must be positive."
        assert outer_hex_inner_radius > 0.0, "Shroud outer hex inradius must be positive."
        assert inner_hex_inner_radius > 0.0, "Shroud inner hex inradius must be positive."
        assert outer_hex_inner_radius > inner_hex_inner_radius, \
            "Shroud outer hex inradius must exceed inner hex inradius."

        self._thickness = thickness
        self._height = height
        self._outer_hex_inner_radius = outer_hex_inner_radius
        self._inner_hex_inner_radius = inner_hex_inner_radius
        self._material = material or Al6061T6()
        self._inner_hex = Hexagon(inner_radius=inner_hex_inner_radius)
        self._outer_hex = Hexagon(inner_radius=outer_hex_inner_radius)

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, Shroud)
            and isclose(self.thickness, other.thickness, rel_tol=TOL)
            and isclose(self.height, other.height, rel_tol=TOL)
            and isclose(self.outer_hex_inner_radius, other.outer_hex_inner_radius, rel_tol=TOL)
            and isclose(self.inner_hex_inner_radius, other.inner_hex_inner_radius, rel_tol=TOL)
            and self.material == other.material
        )

    def __hash__(self) -> int:
        return hash((
            relative_round(self.thickness, TOL),
            relative_round(self.height, TOL),
            relative_round(self.outer_hex_inner_radius, TOL),
            relative_round(self.inner_hex_inner_radius, TOL),
            self.material,
        ))

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
    large_hex_inradius : float
        Inradius of the outer (large) hexagon [cm].
    small_hex_inradius : float
        Inradius of the inner (small) hexagon [cm].
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
    def large_hex_inradius(self) -> float:
        return self._large_hex_inradius

    @property
    def small_hex_inradius(self) -> float:
        return self._small_hex_inradius

    @property
    def material(self) -> Material:
        return self._material

    def __init__(self,
                 thickness: float,
                 height: float,
                 large_hex_inradius: float,
                 small_hex_inradius: float,
                 material: Optional[Material] = None,
                 name: str = "shroud") -> None:
        super().__init__(name)
        assert thickness > 0.0, "Shroud thickness must be positive."
        assert height > 0.0, "Shroud height must be positive."
        assert large_hex_inradius > 0.0, "Shroud large hex inradius must be positive."
        assert small_hex_inradius > 0.0, "Shroud small hex inradius must be positive."
        assert large_hex_inradius > small_hex_inradius, \
            "Shroud large hex inradius must exceed small hex inradius."

        self._thickness = thickness
        self._height = height
        self._large_hex_inradius = large_hex_inradius
        self._small_hex_inradius = small_hex_inradius
        self._material = material or Al6061T6()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, Shroud)
            and isclose(self.thickness, other.thickness, rel_tol=TOL)
            and isclose(self.height, other.height, rel_tol=TOL)
            and isclose(self.large_hex_inradius, other.large_hex_inradius, rel_tol=TOL)
            and isclose(self.small_hex_inradius, other.small_hex_inradius, rel_tol=TOL)
            and self.material == other.material
        )

    def __hash__(self) -> int:
        return hash((
            relative_round(self.thickness, TOL),
            relative_round(self.height, TOL),
            relative_round(self.large_hex_inradius, TOL),
            relative_round(self.small_hex_inradius, TOL),
            self.material,
        ))

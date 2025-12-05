from __future__ import annotations

from math import isclose
from typing import Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material, Al6061T6


class GridPlate(GeometryElement):
    """TRIGA grid plate.

    Parameters
    ----------
    thickness : float
        Thickness of the grid plate [cm].
    fuel_penetration_radius : float
        Radius of penetrations at fuel locations [cm].
    control_rod_penetration_radius : float
        Radius of penetrations at control-rod locations [cm].
    material : Material, optional
        Plate material (defaults to ``Al6061T6``).
    name : str, optional
        Name for this grid plate.

    Attributes
    ----------
    thickness : float
        Thickness of the grid plate [cm].
    fuel_penetration_radius : float
        Radius of penetrations at fuel locations [cm].
    control_rod_penetration_radius : float
        Radius of penetrations at control-rod locations [cm].
    material : Material
        Plate material.
    """

    @property
    def thickness(self) -> float:
        return self._thickness

    @property
    def fuel_penetration_radius(self) -> float:
        return self._fuel_penetration_radius

    @property
    def control_rod_penetration_radius(self) -> float:
        return self._control_rod_penetration_radius

    @property
    def material(self) -> Material:
        return self._material

    def __init__(self,
                 thickness: float,
                 fuel_penetration_radius: float,
                 control_rod_penetration_radius: float,
                 material: Optional[Material] = None,
                 name: str = "grid_plate") -> None:
        super().__init__(name)
        assert thickness > 0.0, "Grid plate thickness must be positive."
        assert fuel_penetration_radius > 0.0, "Fuel penetration radius must be positive."
        assert control_rod_penetration_radius > 0.0, "Control rod penetration radius must be positive."

        self._thickness = thickness
        self._fuel_penetration_radius = fuel_penetration_radius
        self._control_rod_penetration_radius = control_rod_penetration_radius
        self._material = material or Al6061T6()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, GridPlate) and
            isclose(self.thickness, other.thickness, rel_tol=TOL) and
            isclose(self.fuel_penetration_radius, other.fuel_penetration_radius, rel_tol=TOL) and
            isclose(self.control_rod_penetration_radius, other.control_rod_penetration_radius, rel_tol=TOL) and
            self.material == other.material
        )

    def __hash__(self) -> int:
        return hash((
            relative_round(self.thickness, TOL),
            relative_round(self.fuel_penetration_radius, TOL),
            relative_round(self.control_rod_penetration_radius, TOL),
            self.material,
        ))

from __future__ import annotations

from math import isclose
from typing import Dict, List, Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.triga.netl.core import Core
from coreforge.materials import Material, Al6061T6, unique_materials


class GridPlate(GeometryElement):
    """TRIGA grid plate.

    Parameters
    ----------
    thickness : float
        Thickness of the grid plate [cm].
    penetration_map : Dict[str, Optional[float]]
        Map of core locations to penetration radii [cm]. Use ``None`` when no
        penetration is present.
    material : Material, optional
        Plate material (defaults to ``Al6061T6``).
    name : str, optional
        Name for this grid plate.
    three_element_penetration_radius : float, optional
        Radius of the single penetration used when a three-element irradiator
        is present [cm].

    Attributes
    ----------
    thickness : float
        Thickness of the grid plate [cm].
    penetration_map : Dict[str, Optional[float]]
        Map of core locations to penetration radii [cm]. Use ``None`` when no
        penetration is present.
    material : Material
        Plate material.
    three_element_penetration_radius : float, optional
        Radius of the three-element penetration [cm].
    """

    @property
    def thickness(self) -> float:
        return self._thickness

    @property
    def penetration_map(self) -> Dict[str, Optional[float]]:
        return self._penetration_map

    @property
    def material(self) -> Material:
        return self._material

    @property
    def three_element_penetration_radius(self) -> Optional[float]:
        return self._three_element_penetration_radius

    def __init__(self,
                 thickness: float,
                 penetration_map: Dict[str, Optional[float]],
                 material: Optional[Material] = None,
                 name: str = "grid_plate",
                 three_element_penetration_radius: Optional[float] = None) -> None:
        super().__init__(name)
        assert thickness > 0.0, "Grid plate thickness must be positive."
        assert penetration_map, "penetration_map must not be empty."
        if three_element_penetration_radius is not None:
            assert three_element_penetration_radius > 0.0, \
                "Three-element penetration radius must be positive."

        self._thickness = thickness
        self._penetration_map = self._validate_penetration_map(penetration_map)
        self._material = material or Al6061T6()
        self._three_element_penetration_radius = three_element_penetration_radius

    def _validate_penetration_map(self,
                                  penetration_map: Dict[str, Optional[float]],
    ) -> Dict[str, Optional[float]]:
        ordered_locations = [loc for ring in Core.RING_MAP for loc in ring]
        valid_locations = set(ordered_locations)
        full_map = {loc: None for loc in ordered_locations}
        for location, radius in penetration_map.items():
            assert location in valid_locations, \
                f"Invalid core location '{location}' in penetration_map."
            if radius is not None:
                assert radius > 0.0, "Penetration radius must be positive."
            full_map[location] = radius
        return full_map

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, GridPlate) and
            isclose(self.thickness, other.thickness, rel_tol=TOL) and
            self._penetration_maps_equal(other.penetration_map) and
            self.material == other.material and
            (
                self.three_element_penetration_radius is None and
                other.three_element_penetration_radius is None or
                self.three_element_penetration_radius is not None and
                other.three_element_penetration_radius is not None and
                isclose(self.three_element_penetration_radius,
                        other.three_element_penetration_radius,
                        rel_tol=TOL)
            )
        )

    def _penetration_maps_equal(self, other_map: Dict[str, Optional[float]]) -> bool:
        for location, radius in self.penetration_map.items():
            other_radius = other_map.get(location)
            if radius is None or other_radius is None:
                if radius is not other_radius:
                    return False
            elif not isclose(radius, other_radius, rel_tol=TOL):
                return False
        return True

    def __hash__(self) -> int:
        return hash((
            relative_round(self.thickness, TOL),
            tuple(
                (location, None if radius is None else relative_round(radius, TOL))
                for location, radius in sorted(self.penetration_map.items())
            ),
            self.material,
            None if self.three_element_penetration_radius is None else
            relative_round(self.three_element_penetration_radius, TOL),
        ))

    def get_materials(self) -> List[Material]:
        return unique_materials([self.material])


def grid_plate_penetration_map(fuel_location_radius:        float,
                               control_rod_location_radius: float,
                               central_thimble_radius:      float
) -> Dict[str, Optional[float]]:
    """ Create a standard penetration map for a TRIGA grid plate.

    Parameters
    ----------
    fuel_location_radius : float
        Penetration radius for fuel element locations [cm].
    control_rod_location_radius : float
        Penetration radius for control rod locations [cm].
    central_thimble_radius : float
        Penetration radius for the central thimble location [cm].

    Returns
    -------
    Dict[str, Optional[float]]
        Map of core locations to penetration radii [cm]. Use ``None`` when no
        penetration is present.
    """
    assert fuel_location_radius > 0.0, "Fuel penetration radius must be positive."
    assert control_rod_location_radius > 0.0, "Control rod penetration radius must be positive."
    assert central_thimble_radius > 0.0, "Central thimble radius must be positive."

    penetration_map = {loc: fuel_location_radius for ring in Core.RING_MAP for loc in ring}

    penetration_map["A-01"] = central_thimble_radius
    for location in ["C-01", "C-07", "D-06", "D-14"]:
        penetration_map[location] = control_rod_location_radius
    for location in ["G-01", "G-07", "G-13", "G-19", "G-25", "G-31"]:
        penetration_map[location] = None
    return penetration_map

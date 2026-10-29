from __future__ import annotations

from math import isclose
from typing import Dict, List, Optional, Tuple, TypeAlias

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.triga.netl.core import Core
from coreforge.materials import Material, Al6061T6, unique_materials
from coreforge.shapes import Circle


Penetration: TypeAlias = Tuple[float, float, float]
PenetrationMap: TypeAlias = Dict[str, List[Penetration]]


class GridPlate(GeometryElement):
    """TRIGA grid plate with openings expressed in each lattice cell's coordinates.

    Parameters
    ----------
    thickness : float
        Thickness of the grid plate [cm].
    penetration_map : PenetrationMap
        Map of core locations to lists of ``(radius, x_offset, y_offset)``
        openings [cm]. Offsets locate each opening's center relative to the
        cell center. An empty list describes solid plate; omitted locations
        also default to solid plate.
    material : Material, optional
        Plate material (defaults to ``Al6061T6``).
    name : str, optional
        Name for this grid plate.

    Attributes
    ----------
    thickness : float
        Thickness of the grid plate [cm].
    penetration_map : PenetrationMap
        Per-location lists of ``(radius, x_offset, y_offset)`` openings [cm].
        Multiple entries describe the union of openings within a cell.
    material : Material
        Plate material.
    """

    @property
    def thickness(self) -> float:
        return self._thickness

    @property
    def penetration_map(self) -> PenetrationMap:
        return self._penetration_map

    @property
    def material(self) -> Material:
        return self._material

    def __init__(self,
                 thickness: float,
                 penetration_map: PenetrationMap,
                 material: Optional[Material] = None,
                 name: str = "grid_plate") -> None:
        super().__init__(name)
        assert thickness > 0.0, "Grid plate thickness must be positive."
        assert penetration_map, "penetration_map must not be empty."

        self._thickness = thickness
        self._penetration_map = self._validate_penetration_map(penetration_map)
        self._material = material or Al6061T6()

    def _validate_penetration_map(self, penetration_map: PenetrationMap) -> PenetrationMap:
        ordered_locations = [loc for ring in Core.RING_MAP for loc in ring]
        full_map: PenetrationMap = {loc: [] for loc in ordered_locations}
        for location, penetrations in penetration_map.items():
            assert location in full_map, f"Invalid core location '{location}' in penetration_map."
            for radius, _, _ in penetrations:
                assert radius > 0.0, "Penetration radius must be positive."
            full_map[location] = list(penetrations)
        return full_map

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, GridPlate) and
            isclose(self.thickness, other.thickness, rel_tol=TOL) and
            self._penetration_maps_equal(other.penetration_map) and
            self.material == other.material
        )

    def _penetration_maps_equal(self, other_map: PenetrationMap) -> bool:
        for location, penetrations in self.penetration_map.items():
            other_penetrations = other_map.get(location, [])
            if len(penetrations) != len(other_penetrations):
                return False
            if any(not isclose(value, other_value, rel_tol=TOL)
                   for penetration, other in zip(penetrations, other_penetrations)
                   for value, other_value in zip(penetration, other)):
                return False
        return True

    def __hash__(self) -> int:
        return hash((
            relative_round(self.thickness, TOL),
            tuple(
                (location, tuple(tuple(relative_round(value, TOL) for value in penetration)
                                 for penetration in penetrations))
                for location, penetrations in sorted(self.penetration_map.items())
            ),
            self.material,
        ))

    def get_materials(self) -> List[Material]:
        return unique_materials([self.material])


def grid_plate_penetration_map(
    fuel_location_radius: float,
    control_rod_location_radius: float,
    central_thimble_radius: float,
    pnt_location_radius: float,
    three_element_location_radius: Optional[float] = None,
    core: Optional[Core] = None,
) -> PenetrationMap:
    """Create the ordinary and optional three-element openings for a TRIGA plate.

    Parameters
    ----------
    fuel_location_radius : float
        Penetration radius for fuel element locations [cm].
    control_rod_location_radius : float
        Penetration radius for control rod locations [cm].
    central_thimble_radius : float
        Penetration radius for the central thimble location [cm].
    pnt_location_radius : float
        Penetration radius for the PNT location (G-34) [cm].
    three_element_location_radius : Optional[float]
        Radius of the shared three-element opening [cm]. Requires ``core``.
        If omitted, or the supplied core has no irradiator, only ordinary
        openings are generated.
    core : Optional[Core]
        Core whose attributes determine the penetration(s). At the three reserved
        irradiator locations the irradiator penetration replaces the element penetration.
        Neighboring element locations which the irradiator penetration footprint
        intersects will have both the element penetration and irradiator penetration.
        May be omitted when no three-element radius is supplied.

    Returns
    -------
    PenetrationMap
        Core locations mapped to lists of ``(radius, x_offset, y_offset)``
        openings [cm]. An empty list describes solid plate.

    Raises
    ------
    AssertionError
        If a radius is nonpositive, or a three-element radius is supplied
        without a core.
    """
    assert fuel_location_radius > 0.0, "Fuel penetration radius must be positive."
    assert control_rod_location_radius > 0.0, "Control rod penetration radius must be positive."
    assert central_thimble_radius > 0.0, "Central thimble radius must be positive."
    assert pnt_location_radius > 0.0, "PNT penetration radius must be positive."
    if three_element_location_radius is not None:
        assert three_element_location_radius > 0.0, "Three-element penetration radius must be positive."
        assert core is not None, "A core is required for the three-element penetration."

    penetration_map = {loc: [(fuel_location_radius, 0.0, 0.0)]
                       for ring in Core.RING_MAP for loc in ring}
    penetration_map[Core.CENTRAL_THIMBLE_LOCATION] = [(central_thimble_radius, 0.0, 0.0)]
    penetration_map[Core.PNT_LOCATION] = [(pnt_location_radius, 0.0, 0.0)]
    for location in Core.CONTROL_ROD_LOCATIONS:
        penetration_map[location] = [(control_rod_location_radius, 0.0, 0.0)]
    for location in Core.NON_ELEMENT_LOCATIONS:
        penetration_map[location] = []

    if core is not None and three_element_location_radius is not None and core.three_element_irradiator is not None:
        for (i, j), (x0, y0) in core.lattice.cells_intersecting(
            Circle(three_element_location_radius), core.three_element_center,
        ).items():
            location = Core.RING_MAP[i][j]
            if location in Core.THREE_ELEMENT_LOCATIONS:
                penetration_map[location] = []
            penetration_map[location].append((three_element_location_radius, x0, y0))
    return penetration_map

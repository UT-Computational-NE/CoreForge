from __future__ import annotations
from typing import List, Optional

from coreforge.geometry_elements.pincell import PinCell
from coreforge.shapes import Circle
from coreforge.materials import Material

class CylindricalPinCell(PinCell):
    """ A class for pincells that consist entirely of concentric cylinders

    This has two means of construction, either by providing a list of zones and an outer material,
    or a list of radii and materials.

    Parameters
    ----------
    zones : Optional[List[PinCell.Zone]]
        The rings of the cylindrical pincell
        (should be specified with outer_material)
    outer_material : Optional[Material]
        The material that radially surrounds the concentric cylinders
        (should be specified with rings)
    radii : Optional[List[float]]
        The list of cylindrical region radii, proceeding in order from inner most radii to outer most radii
        (should be specified with materials)
    materials : Optional[List[Material]]
        The list of cylindrical region materials, proceeding in order from inner most material to
        outer most material.  The last material represents the outer material of pincell that surrounds
        the cylindrical regions.  Ergo, len(materials) == len(radii)+1
        (should be specified with radii)
    min_zone_thickness : Optional[float]
        If provided, any zone whose thickness is <= this threshold is removed
        after the zones list is constructed. Thickness is computed as the
        difference in outer radii between consecutive zones (inner radius = 0
        for the first zone). If None, no filtering is applied.
    """

    @property
    def zones(self) -> List[PinCell.Zone]:
        return self._zones

    @zones.setter
    def zones(self, zones: List[PinCell.Zone]) -> None:
        assert all(isinstance(zone.shape, Circle) for zone in zones)
        self._set_zones(zones=zones)


    def __init__(self,
                 zones:             Optional[List[PinCell.Zone]] = None,
                 outer_material:    Optional[Material] = None,
                 radii:             Optional[List[float]] = None,
                 materials:         Optional[List[Material]] = None,
                 name:              str = 'pincell',
                 min_zone_thickness: Optional[float] = None):

        assert (zones and outer_material) or (radii and materials)
        if min_zone_thickness is not None:
            assert min_zone_thickness >= 0.0

        if radii and materials:
            assert len(radii) > 0
            assert len(radii) + 1 == len(materials)
            outer_material = materials[-1]
            zones = []
            for radius, material in zip(radii, materials[:-1]):
                zones.append(PinCell.Zone(shape = Circle(r=radius), material = material))

        if min_zone_thickness is not None:
            filtered_zones: List[PinCell.Zone] = []
            prev_outer = 0.0
            for zone in zones:
                thickness = zone.shape.outer_radius - prev_outer
                if thickness > min_zone_thickness:
                    filtered_zones.append(zone)
                    prev_outer = zone.shape.outer_radius
            zones = filtered_zones

        super().__init__(zones = zones, outer_material = outer_material, name = name)

from __future__ import annotations
from typing import List, Tuple, Any
from math import isclose

import openmc
import mpactpy
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes import Shape_2D
from coreforge.materials import Material
from coreforge.geometry_elements.geometry_element import GeometryElement

class PinCell(GeometryElement):
    """ A class for the reactor concentric "pincells"

    In traditional LWRs, pincells are simply concentric cylinders. However,
    this pincell class pertains to any concentric shapes that are of such
    dimensions such that the outer radius of a inner shape does not exceeed
    the inner radius of the next outer shape.

    Attributes
    ----------
    zones : List[Zone]
        The collection of zones that define the pincell, listed in order of
        the inner-most zone to the outer-most zone.  Each zone's outer-radius
        may not exceed the next zone's inner-radius.
    origin  : Tuple[float, float]
        The X-Y origin of the "pin" within the pincell (Default: (0.0, 0.0))
    outer_material : Material
        The material that radially surrounds the concentric shapes
    """

    class Zone():
        """ A shape-material pair used for representing the different "zones" of a pincell

        Attributes
        ----------
        name : str
            A name for the zone
        shape : Shape_2D
            The shape of this pincell zone
        material : Material
            The material which fills this pincell zone
        rotation : float
            The rotation of the shape about its origin (degrees)
        """

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        def name(self, name: str) -> str:
            self._name = name

        @property
        def shape(self) -> Shape_2D:
            return self._shape

        @shape.setter
        def shape(self, shape: Shape_2D) -> None:
            self._shape = shape

        @property
        def material(self) -> Material:
            return self._material

        @material.setter
        def material(self, material: Material) -> None:
            self._material = material

        @property
        def rotation(self) -> float:
            return self._rotation

        @rotation.setter
        def rotation(self, rotation: float) -> None:
            self._rotation = rotation

        def __init__(self, shape: Shape_2D, material: Material, name: str = 'zone', rotation: float=0.):
            self.name    = name
            self.shape    = shape
            self.material = material
            self.rotation = rotation

        def __eq__(self, other: Any) -> bool:
            if self is other:
                return True
            return (isinstance(other, PinCell.Zone) and
                    self.shape == other.shape       and
                    self.material == other.material and
                    isclose(self.rotation, other.rotation, rel_tol=TOL)
                   )

        def __hash__(self) -> int:
            return hash((self.shape,
                         self.material,
                         relative_round(self.rotation, TOL)))


    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @outer_material.setter
    def outer_material(self, outer_material: Material) -> None:
        self._outer_material = outer_material

    @property
    def zones(self) -> List[Zone]:
        return self._zones

    @zones.setter
    def zones(self, zones: List[Zone]) -> None:
        self._zones = None
        self._set_zones(zones=zones)

    def _set_zones(self, zones: List[Zone]) -> None:
        """ A zone setter method which captures the basic assertion logic

        This is being created to allow for child classes to wrap additional assertion logic
        around the base assertion logic

        Parameters
        ----------
        zones : List[Zone]
            The collection of zones to assign to the pincell
        """
        assert len(zones) > 0, f"len(zones) = {len(zones)}"
        assert all(zones[i-1].shape.o_r < zones[i].shape.i_r for i in range(1,len(zones))), \
            "The boundary of zones cannot intersect"
        self._zones = zones

    @property
    def origin(self) -> Tuple[float, float]:
        return self._origin

    @origin.setter
    def origin(self, origin: Tuple[float, float]) -> None:
        self._origin = origin


    def __init__(self, zones: List[Zone], outer_material: openmc.Material,
                name: str = 'pincell', origin: Tuple[float, float]=(0., 0.)):

        self.name           = name
        self.zones          = zones
        self.outer_material = outer_material
        self.origin         = origin

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, PinCell)                            and
                self.outer_material == other.outer_material           and
                isclose(self.origin[0], other.origin[0], rel_tol=TOL) and
                isclose(self.origin[1], other.origin[1], rel_tol=TOL) and
                len(self.zones) == len(other.zones)                   and
                all(self.zones[i] == other.zones[i] for i in range(len(self.zones)))
               )

    def __hash__(self) -> int:
        return hash((self.outer_material,
                     relative_round(self.origin[0], TOL),
                     relative_round(self.origin[1], TOL),
                     tuple(self.zones)))

    def make_openmc_universe(self) -> openmc.Universe:

        cells = []
        previous_regions = []
        for zone in self.zones:
            region = zone.shape.make_region()
            region = region.rotate((0., 0., zone.rotation))
            region = region.translate([self.origin[0], self.origin[1], 0.])
            for previous_region in previous_regions:
                region &= ~previous_region
            previous_regions.append(region)
            cells.append(openmc.Cell(fill=zone.material.openmc_material, region=region))

        outer_region = ~cells[0].region
        for previous_region in previous_regions:
            if previous_region is not cells[0].region:
                outer_region &= ~previous_region
        cells.append(openmc.Cell(fill=self.outer_material.openmc_material, region=outer_region))

        universe = openmc.Universe(name=self.name, cells=cells)

        return universe

    def make_mpact_core(self) -> mpactpy.Core:
        raise NotImplementedError("Cannot make an MPACT Core for a generic pincell")

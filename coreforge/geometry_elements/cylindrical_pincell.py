from __future__ import annotations
from typing import List, TypedDict, Tuple, Optional
from dataclasses import dataclass
from math import inf

import mpactpy

from coreforge.geometry_elements.pincell import PinCell
from coreforge.shapes import Circle
from coreforge.materials import Material


class CylindricalPincell(PinCell):
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
    mpact_build_specs : Optional[MPACTBuildSpecs]
        Specifications for building the MPACT Core representation of this element

    Attributes
    ----------
    mpact_build_specs : Optional[MPACTBuildSpecs]
        Specifications for building the MPACT Core representation of this element
    """

    @dataclass
    class MPACTBuildSpecs():
        """ A dataclass for holding MPACT Core building specifications

        Attributes
        ----------
        target_cell_thicknesses : ThicknessSpec
            The target thickness of the cells in terms of 'radial' thickness
            and 'azimuthal' arc length (cm).
            Cells will be subdivided to limit cells to within these specifications.
        bounds : Tuple[float, float, float, float]
                The bounds of the cylindrical pincell (order: x_min, x_max, y_min, y_max)
        height : float
            The height to build the extruded PinCell in the axial direction (cm).
            Default value is 1.0
        divide_into_quadrants : bool
            An optional setting to divide the pincell into 4 separate MPACT Module quadrants.
            This will represent the pincell with 4 MPACT Modules rather than just one.
            Default value is False
        """

        class ThicknessSpec(TypedDict):
            """ Class specifying the keys for target cell thickness
            """
            radial:    float
            azimuthal: float

        bounds:                  Tuple[float, float, float, float]
        target_cell_thicknesses: Optional[ThicknessSpec] = None
        height:                  float = 1.0
        divide_into_quadrants:   bool = False

        def __post_init__(self):
            if not self.target_cell_thicknesses:
                self.target_cell_thicknesses = {'radial': inf, 'azimuthal': inf}

            assert all(thickness > 0. for thickness in self.target_cell_thicknesses.values()), \
                f"target_cell_thicknesses = {self.target_cell_thicknesses}"

            assert self.height > 0., f"height = {self.height}"
            assert self.bounds[0] < self.bounds[1], f"xmin = {self.bounds[0]}, xmax = {self.bounds[1]}"
            assert self.bounds[2] < self.bounds[3], f"ymin = {self.bounds[2]}, ymax = {self.bounds[3]}"


    @property
    def zones(self) -> List[PinCell.Zone]:
        return self._zones

    @zones.setter
    def zones(self, zones: List[PinCell.Zone]) -> None:
        assert all(isinstance(zone.shape, Circle) for zone in zones)
        self._set_zones(zones=zones)

    @property
    def mpact_build_specs(self) -> Optional[MPACTBuildSpecs]:
        return self._mpact_build_specs

    @mpact_build_specs.setter
    def mpact_build_specs(self, specs: Optional[MPACTBuildSpecs]) -> None:
        outer_radius = self.zones[-1].shape.outer_radius
        self._mpact_build_specs = specs if specs else \
                                  CylindricalPincell.MPACTBuildSpecs(bounds=(-outer_radius, outer_radius
                                                                             -outer_radius, outer_radius))

        self._radial_thicknesses = []
        prev_radius = 0.
        for zone in self.zones:
            self._radial_thicknesses.append(zone.shape.inner_radius - prev_radius)
            prev_radius = zone.shape.inner_radius

        self._module_specs = [{"bounds" : specs.bounds}]
        if specs.divide_into_quadrants:
            xmin = specs.bounds[0]
            xmax = specs.bounds[1]
            ymin = specs.bounds[2]
            ymax = specs.bounds[3]
            hp = {"X": (xmax-xmin)*0.5, "Y": (ymax-ymin)*0.5} # half pitch
            self._module_specs = [{"bounds" : (        xmin, xmin+hp["X"], ymin+hp["Y"],         ymax)},
                                  {"bounds" : (xmin+hp["X"],         xmax, ymin+hp["Y"],         ymax)},
                                  {"bounds" : (        xmin, xmin+hp["X"],         ymin, ymin+hp["Y"])},
                                  {"bounds" : (xmin+hp["X"],         xmax,         ymin, ymin+hp["Y"])}]


    def __init__(self,
                 zones:             Optional[List[PinCell.Zone]] = None,
                 outer_material:    Optional[Material] = None,
                 radii:             Optional[List[float]] = None,
                 materials:         Optional[List[Material]] = None,
                 name:              str = 'pincell',
                 mpact_build_specs: Optional[MPACTBuildSpecs] = None):

        assert (zones and outer_material) or (radii and materials)

        if radii and materials:
            assert len(radii) > 0
            assert len(radii) + 1 == len(materials)
            outer_material = materials[-1]
            zones = []
            for radius, material in zip(radii, materials[:-1]):
                zones.append(PinCell.Zone(shape = Circle(r=radius), material = material))

        super().__init__(zones = zones, outer_material = outer_material, name = name)

        self.mpact_build_specs = mpact_build_specs


    def make_mpact_core(self) -> mpactpy.Core:
        specs = self.mpact_build_specs

        materials = [zone.material for zone in self.zones] + [self.outer_material]
        materials = [material.mpact_material for material in materials]

        target_cell_thicknesses = {"R": specs.target_cell_thicknesses["radial"],
                                   "S": specs.target_cell_thicknesses["azimuthal"]}

        def build_module(bounds: Tuple[float, float, float, float]) -> mpactpy.Module:
            pin = mpactpy.build_gcyl_pin(bounds                  = bounds,
                                         materials               = materials,
                                         target_cell_thicknesses = target_cell_thicknesses,
                                         thicknesses             = {"R": self._radial_thicknesses,
                                                                    "Z": [specs.height]})
            return mpactpy.Module(1, [[pin]])

        modules    = [build_module(spec["bounds"]) for spec in self._module_specs]
        module_map = [[modules[0]]] if not specs.divide_into_quadrants else [[modules[0], modules[1]],
                                                                             [modules[2], modules[3]]]

        lattice  = mpactpy.Lattice(module_map)
        assembly = mpactpy.Assembly([lattice])
        core     = mpactpy.Core([[assembly]])

        return core

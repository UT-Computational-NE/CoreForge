import openmc

from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.triga as geometry_elements_triga

@register_builder(geometry_elements_triga.FuelElement)
class FuelElement(Builder[geometry_elements_triga.FuelElement]):
    """ An OpenMC geometry builder class for a TRIGA Fuel Element
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga.FuelElement) -> openmc.Universe:
        """ Origin of contructed universe is at the bottom center of the fuel element."""
        cells = []

        height = element.lower_end_fitting.length

        cone     = element.lower_end_fitting.cone(outer_material = element.outer_material,
                                                  name           = element.name + "_lower_end_fitting_cone")
        cone     = cone.shape.make_region()
        cone     = cone.rotate((180.0, 0.0, 0.0))
        cone     = cone.translate([0.0, 0.0, height])
        plane    = openmc.ZPlane(height)
        cylinder = openmc.ZCylinder(r=element.cladding.outer_radius)
        fixture  =  -cone & -cylinder
        cells.append(openmc.Cell(fill=element.lower_end_fitting.material.openmc_material, region=-plane & fixture))
        cells.append(openmc.Cell(fill=element.outer_material.openmc_material,   region=-plane & ~fixture))

        pincell = element.pincell
        fuel_region_length = element.fuel_meat.length / element.fuel_meat.num_axial_regions
        fuel_pincells = list(reversed(pincell["fuel"]))
        segments = [pincell["lower_reflector"],
                    pincell["moly_disc"],
                    *fuel_pincells,
                    pincell["upper_reflector"],
                    pincell["air_gap"]]

        lengths  = [element.lower_graphite_reflector.thickness,
                    element.moly_disc.thickness,
                    *([fuel_region_length] * len(fuel_pincells)),
                    element.upper_graphite_reflector.thickness,
                    element.upper_air_gap.thickness]

        for segment, length in zip(segments, lengths):
            lower_bound = openmc.ZPlane(height)
            upper_bound = openmc.ZPlane(height + length)
            cells.append(openmc.Cell(fill=build(segment), region=+lower_bound & -upper_bound))
            height += length

        cone     = element.upper_end_fitting.cone(outer_material = element.outer_material,
                                                  name           = element.name + "_upper_end_fitting_cone")
        cone     = cone.shape.make_region()
        cone     = cone.translate([0.0, 0.0, height])
        plane    = openmc.ZPlane(height)
        fixture  =  -cone & -cylinder
        cells.append(openmc.Cell(fill=element.upper_end_fitting.material.openmc_material, region=+plane & fixture))
        cells.append(openmc.Cell(fill=element.outer_material.openmc_material,    region=+plane & ~fixture))

        universe = openmc.Universe(name=element.name, cells=cells)

        return universe

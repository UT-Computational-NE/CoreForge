import openmc

from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.triga as geometry_elements_triga

@register_builder(geometry_elements_triga.GraphiteElement)
class GraphiteElement(Builder[geometry_elements_triga.GraphiteElement]):
    """ An OpenMC geometry builder class for a TRIGA Graphite Element
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga.GraphiteElement) -> openmc.Universe:
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

        lower_bound = openmc.ZPlane(height)
        upper_bound = openmc.ZPlane(height + element.graphite_meat.length)
        cells.append(openmc.Cell(fill=build(element.graphite_pincell), region=+lower_bound & -upper_bound))

        height += element.graphite_meat.length

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

import openmc

from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.triga as geometry_elements_triga
from coreforge.shapes import OneSidedCone

@register_builder(geometry_elements_triga.GraphiteElement)
class GraphiteElement:
    """ An OpenMC geometry builder class for a TRIGA Graphite Element
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga.GraphiteElement) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a TRIGA Graphite Element

        Origin of contructed universe is at the bottom center of the graphite element.

        Parameters
        ----------
        element: geometry_elements_triga.GraphiteElement
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        cells = []

        height = 0.0

        cone = OneSidedCone(r=element.cladding.outer_radius,
                            h=element.lower_end_fitting.length).make_region()
        cone = cone.rotate((180.0, 0.0, 0.0))
        cone = cone.translate([0.0, 0.0, height])
        plane = openmc.ZPlane(height)
        cells.append(openmc.Cell(fill=element.cladding.material.openmc_material, region=-plane & -cone))
        cells.append(openmc.Cell(fill=element.outer_material.openmc_material,    region=-plane & +cone))

        height += element.lower_end_fitting.length

        lower_bound = openmc.ZPlane(height)
        upper_bound = openmc.ZPlane(height + element.graphite_meat.length)
        cells.append(openmc.Cell(fill=build(element.graphite_pincell), region=+lower_bound & -upper_bound))

        height += element.graphite_meat.length

        cone = OneSidedCone(r=element.cladding.outer_radius,
                            h=element.upper_end_fitting.length).make_region()
        plane = openmc.ZPlane(height)
        cells.append(openmc.Cell(fill=element.cladding.material.openmc_material, region=-plane & -cone))
        cells.append(openmc.Cell(fill=element.outer_material.openmc_material,    region=-plane & +cone))

        universe = openmc.Universe(name=element.name, cells=cells)

        return universe
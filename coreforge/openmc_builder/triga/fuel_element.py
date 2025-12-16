from math import sqrt
import openmc

from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.triga as geometry_elements_triga
from coreforge.shapes import OneSidedCone

@register_builder(geometry_elements_triga.FuelElement)
class FuelElement:
    """ An OpenMC geometry builder class for a TRIGA Fuel Element
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga.FuelElement) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a TRIGA Fuel Element

        Origin of contructed universe is at the bottom center of the fuel element.

        Parameters
        ----------
        element: geometry_elements_triga.FuelElement
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        cells = []

        height = element.lower_end_fitting.length

        cone     = OneSidedCone(r=sqrt(element.lower_end_fitting.r2) * element.lower_end_fitting.length,
                            h=element.lower_end_fitting.length).make_region()
        cone     = cone.rotate((180.0, 0.0, 0.0))
        cone     = cone.translate([0.0, 0.0, height])
        plane    = openmc.ZPlane(height)
        cylinder = openmc.ZCylinder(r=element.cladding.outer_radius)
        fixture  =  -cone & -cylinder
        cells.append(openmc.Cell(fill=element.cladding.material.openmc_material, region=-plane & fixture))
        cells.append(openmc.Cell(fill=element.outer_material.openmc_material,   region=-plane & ~fixture))

        segments = [element.lower_reflector_pincell,
                    element.moly_disc_pincell,
                    element.fuel_pincell,
                    element.upper_reflector_pincell,
                    element.air_gap_pincell]

        lengths  = [element.lower_graphite_reflector.thickness,
                    element.moly_disc.thickness,
                    element.fuel_meat.length,
                    element.upper_graphite_reflector.thickness,
                    element.upper_air_gap.thickness]

        for segment, length in zip(segments, lengths):
            lower_bound = openmc.ZPlane(height)
            upper_bound = openmc.ZPlane(height + length)
            cells.append(openmc.Cell(fill=build(segment), region=+lower_bound & -upper_bound))
            height += length

        cone     = OneSidedCone(r=sqrt(element.upper_end_fitting.r2) * element.upper_end_fitting.length,
                                h=element.upper_end_fitting.length).make_region()
        cone     = cone.translate([0.0, 0.0, height])
        plane    = openmc.ZPlane(height)
        fixture  =  -cone & -cylinder
        cells.append(openmc.Cell(fill=element.cladding.material.openmc_material, region=+plane & fixture))
        cells.append(openmc.Cell(fill=element.outer_material.openmc_material,    region=+plane & ~fixture))

        universe = openmc.Universe(name=element.name, cells=cells)

        return universe

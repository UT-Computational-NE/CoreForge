import openmc

from coreforge.openmc_builder.registry import register_builder
from coreforge import geometry_elements

@register_builder(geometry_elements.PinCell)
class PinCell:
    """ An OpenMC geometry builder class for PinCell
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements.PinCell) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a PinCell

        Parameters
        ----------
        element: PinCell
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        cells = []
        previous_regions = []
        for zone in element.zones:
            region = zone.shape.make_region()
            region = region.rotate((0., 0., zone.rotation))
            region = region.translate([element.x0, element.y0, 0.])
            for previous_region in previous_regions:
                region &= ~previous_region
            previous_regions.append(region)
            cells.append(openmc.Cell(fill=zone.material.openmc_material, region=region))

        outer_region = ~cells[0].region
        for previous_region in previous_regions:
            if previous_region is not cells[0].region:
                outer_region &= ~previous_region
        cells.append(openmc.Cell(fill=element.outer_material.openmc_material, region=outer_region))

        universe = openmc.Universe(name=element.name, cells=cells)

        return universe

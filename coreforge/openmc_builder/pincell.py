import openmc

from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import register_builder
from coreforge import geometry_elements

@register_builder(geometry_elements.PinCell)
class PinCell(Builder[geometry_elements.PinCell]):
    """ An OpenMC geometry builder class for PinCell
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements.PinCell) -> openmc.Universe:
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


@register_builder(geometry_elements.PinCells)
class PinCells(Builder[geometry_elements.PinCells]):
    """An OpenMC builder for ordered layers of pin cells.

    Later pin cells cover earlier pin cells within their finite regions.
    The common outer material fills the region outside all pin cells.
    """

    def build(self, element: geometry_elements.PinCells) -> openmc.Universe:
        """Build pin-cell layers from latest to earliest.

        Parameters
        ----------
        element : geometry_elements.PinCells
            Ordered pin-cell layers to build.

        Returns
        -------
        openmc.Universe
            Non-overlapping layer cells and one common background cell.
        """
        cells = []
        outer_regions = []
        for pincell in reversed(element.pincells):
            pin_cells = list(PinCell().build(pincell).cells.values())
            outer_region = pin_cells.pop().region
            for cell in pin_cells:
                cell.region = openmc.Intersection([cell.region] + outer_regions)
            cells.extend(pin_cells)
            outer_regions.append(outer_region)

        cells.append(openmc.Cell(fill=element.outer_material.openmc_material,
                                 region=openmc.Intersection(outer_regions)))
        return openmc.Universe(name=element.name, cells=cells)

import openmc

from coreforge.openmc_builder.registry import register_builder
from coreforge import geometry_elements

@register_builder(geometry_elements.Block)
class Block:
    """ An OpenMC geometry builder class for Block
    """

    def __init__(self):
        pass

    def build_channel_cell(self, channel: geometry_elements.Block.Channel) -> openmc.Cell:
        """ A method for creating a new cell based on a block channel

        Parameters
        ----------
        channel : geometry_elements.Block.Channel
            The channel to build cells for

        Returns
        -------
        openmc.Cell
            A new cell based on the provided channel
        """

        region = channel.shape.make_region()
        region = region.rotate((0., 0., channel.shape_rotation))
        region = region.translate([0., -channel.distance_from_block_center, 0.])
        region = region.rotate((0., 0., channel.rotation_about_block_center))
        cell = openmc.Cell(name=channel.name, fill=channel.material.openmc_material, region=region)
        return cell

    def build(self, element: geometry_elements.Block) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a Block

        Parameters
        ----------
        element: Block
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        channel_cells = []
        for channel in element.channels:
            if channel is None:
                continue
            channel_cells.append(self.build_channel_cell(channel))

        prism_region = element.shape.make_region()
        outer_region = ~prism_region
        for channel in channel_cells:
            prism_region &= ~channel.region
            outer_region &= ~channel.region

        block_cell = openmc.Cell(fill=element.prism_material.openmc_material, region=prism_region)
        outer_cell = openmc.Cell(fill=element.outer_material.openmc_material, region=outer_region)

        universe = openmc.Universe(name=element.name)
        universe.add_cells([block_cell, outer_cell])
        for channel in channel_cells:
            universe.add_cell(channel)

        return universe

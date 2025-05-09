import openmc

from coreforge.openmc_builder.registry import register_builder, build
from coreforge import geometry_elements

@register_builder(geometry_elements.Stack)
class Stack:
    """ An OpenMC geometry builder class for Stack
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements.Stack) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a Stack

        Parameters
        ----------
        element: Stack
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        cells = []
        height = element.bottom_pos
        for segment in element.segments:
            segment_universe = build(segment.element)
            if segment is element.segments[0] and segment is element.segments[-1]:
                region      = None
            elif segment is element.segments[0]:
                upper_bound = openmc.ZPlane(height + segment.length)
                region      = -upper_bound
            elif segment is element.segments[-1]:
                lower_bound = openmc.ZPlane(height)
                region      = +lower_bound
            else:
                lower_bound = openmc.ZPlane(height)
                upper_bound = openmc.ZPlane(height + segment.length)
                region      = +lower_bound & -upper_bound

            cells.append(openmc.Cell(fill=segment_universe, region=region))
            height += segment.length

        universe = openmc.Universe(name=element.name, cells=cells)

        return universe

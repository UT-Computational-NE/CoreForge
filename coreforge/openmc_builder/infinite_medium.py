import openmc

from coreforge.openmc_builder.openmc_builder import register_builder
from coreforge import geometry_elements

@register_builder(geometry_elements.InfiniteMedium)
class InfiniteMedium:
    """ An OpenMC geometry builder class for InfiniteMedium
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements.InfiniteMedium) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a PinCeInfiniteMediumll

        Parameters
        ----------
        element: InfiniteMedium
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        universe = openmc.Universe(name=element.name,
                                   cells=[openmc.Cell(fill=element.material.openmc_material)])
        return universe

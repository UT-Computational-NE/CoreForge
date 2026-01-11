import openmc

from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import register_builder
from coreforge import geometry_elements

@register_builder(geometry_elements.InfiniteMedium)
class InfiniteMedium(Builder[geometry_elements.InfiniteMedium]):
    """ An OpenMC geometry builder class for InfiniteMedium
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements.InfiniteMedium) -> openmc.Universe:
        universe = openmc.Universe(name=element.name,
                                   cells=[openmc.Cell(fill=element.material.openmc_material)])
        return universe

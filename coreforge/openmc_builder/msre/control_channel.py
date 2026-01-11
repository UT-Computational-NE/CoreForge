import openmc

from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.msre as geometry_elements_msre

@register_builder(geometry_elements_msre.ControlChannel)
class ControlChannel(Builder[geometry_elements_msre.ControlChannel]):
    """ An OpenMC geometry builder class for an MSRE ControlChannel
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_msre.ControlChannel) -> openmc.Universe:
        return build(element.as_stack())

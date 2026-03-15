import openmc

from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl

@register_builder(geometry_elements_triga_netl.SourceHolder)
class SourceHolder(Builder[geometry_elements_triga_netl.SourceHolder]):
    """ An OpenMC geometry builder class for a TRIGA Source Holder
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga_netl.SourceHolder) -> openmc.Universe:
        """ Origin of contructed universe is at the bottom center of the fuel element."""
        return build(element.as_stack(bottom_pos = 0.0))

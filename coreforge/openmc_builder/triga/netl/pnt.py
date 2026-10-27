import openmc

from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


@register_builder(geometry_elements_triga_netl.PNT)
class PNT(Builder[geometry_elements_triga_netl.PNT]):
    """An OpenMC geometry builder class for a TRIGA NETL PNT."""

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga_netl.PNT) -> openmc.Universe:
        """Build the PNT with its bottom at zero."""
        return build(element.as_stack(bottom_pos=0.0))

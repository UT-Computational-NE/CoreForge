import openmc

from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import build, register_builder
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


@register_builder(geometry_elements_triga_netl.ThreeElementIrradiator)
class ThreeElementIrradiator(Builder[geometry_elements_triga_netl.ThreeElementIrradiator]):
    """OpenMC geometry builder for a conventional NETL three-element irradiator."""

    def __init__(self):
        pass

    def build(
        self,
        element: geometry_elements_triga_netl.ThreeElementIrradiator,
    ) -> openmc.Universe:
        """Build an irradiator universe whose origin is at the casing bottom."""
        return build(element.as_stack(bottom_pos=0.0))

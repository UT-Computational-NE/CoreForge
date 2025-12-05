import openmc

from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl

@register_builder(geometry_elements_triga_netl.TransientRod)
class TransientRod:
    """ An OpenMC geometry builder class for a TRIGA Transient Rod
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga_netl.TransientRod) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a TRIGA Transient Rod

        Origin of contructed universe is at the bottom center of the transient rod.

        Parameters
        ----------
        element: geometry_elements_triga_netl.TransientRod
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        return build(element.as_stack(bottom_pos = 0.0))
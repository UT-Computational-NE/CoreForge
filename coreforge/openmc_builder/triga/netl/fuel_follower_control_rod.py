import openmc

from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl

@register_builder(geometry_elements_triga_netl.FuelFollowerControlRod)
class FuelFollowerControlRod:
    """ An OpenMC geometry builder class for a TRIGA Fuel Follower Control Rod
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga_netl.FuelFollowerControlRod) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a TRIGA Fuel Follower Control Rod

        Origin of contructed universe is at the bottom center of the fuel follower control rod.

        Parameters
        ----------
        element: geometry_elements_triga_netl.FuelFollowerControlRod
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        return build(element.as_stack(bottom_pos = 0.0))
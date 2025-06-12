import openmc

from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.msre as geometry_elements_msre

@register_builder(geometry_elements_msre.ControlChannel)
class ControlChannel:
    """ An OpenMC geometry builder class for an MSRE ControlChannel
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_msre.ControlChannel) -> openmc.Universe:
        """ Method for building an OpenMC geometry of an MSRE ControlChannel

        Parameters
        ----------
        element: geometry_elements_msre.ControlChannel
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        return build(element.as_stack())

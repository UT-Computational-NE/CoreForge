import openmc

from coreforge.openmc_builder.openmc_builder import register_builder, build
import coreforge.geometry_elements.msre as geometry_elements_msre

@register_builder(geometry_elements_msre.Stringer)
class Stringer:
    """ An OpenMC geometry builder class for an MSRE Stringer
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_msre.Stringer) -> openmc.Universe:
        """ Method for building an OpenMC geometry of an MSRE Stringer

        Parameters
        ----------
        element: geometry_elements_msre.Stringer
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        return build(element.as_stack())

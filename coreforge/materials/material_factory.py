from abc import ABC, abstractmethod

import openmc

class MaterialFactory(ABC):
    """ An abstract class for OpenMC material factories
    """

    @abstractmethod
    def make_material(self) -> openmc.Material:
        """ Primary method for building instances of an OpenMC Material

        Returns
        -------
        openmc.Material
            The OpenMC material that was made
        """

import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class Water(Material):
    """ Factory for creating water materials

    Default water density assumed to be 1 g/cm3

    Parameters
    ----------
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    density : float
        The density of the material (g/cm3)
    """

    def __init__(self,
                 name: str = 'Water',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 1.0):

        openmc_material = openmc.Material()
        openmc_material.add_element('H', 2)
        openmc_material.add_element('O', 1)
        openmc_material.add_s_alpha_beta('c_H_in_H2O')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material)

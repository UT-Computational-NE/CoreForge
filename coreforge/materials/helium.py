import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class Helium(Material):
    """ Factory for creating Helium Gas materials

    Default density calculated using CoolProp (Reference 1) at 293.6K and 1 atm

    Parameters
    ----------
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    density : float
        The density of the material (g/cm3)

    References
    ----------
    1. Bell, Ian H., Wronski, Jorrit, Quoilin, Sylvain, and Lemort, Vincent.
    “Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the
    Open-Source Thermophysical Property Library CoolProp.” Industrial & Engineering
    Chemistry Research, volume 53, number 6, pages 2498-2508, 2014
    """

    def __init__(self,
                 name: str = 'Helium',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 0.00016606):

        openmc_material = openmc.Material()
        openmc_material.set_density('g/cm3', density)
        openmc_material.add_element('He', 100., percent_type='wo')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material)

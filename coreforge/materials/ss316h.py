import openmc

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

class SS316H(Material):
    """ Factory for creating 316H Stainless Steel materials

    - Default density from Ref 1 SS-316H Physical Properties Table
    - Composition from Ref 1 SS-316H Chemical Analysis Table

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
    1. Sandmeyer Steel Company, accessed October 10, 2024, https://www.sandmeyersteel.com
    """

    def __init__(self,
                 name: str = 'SS-316H',
                 temperature: float = STANDARD_TEMPERATURE,
                 density: float = 8.0):

        components = {'Cr': 18.0,
                      'Ni': 14.0,
                      'Mo':  3.0,
                       'C':  0.1,
                      'Mn':  2.0,
                       'P':  0.045,
                       'S':  0.03,
                      'Si':  0.75,
                      'Fe': 62.075}
        openmc_material = openmc.Material()
        openmc_material.add_components(components, percent_type='wo')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material)

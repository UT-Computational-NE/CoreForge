import openmc

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

class SS304(Material):
    """ Factory for creating 304 Stainless Steel materials

    - Default density from Ref 1 SS-304 Physical Properties Table
    - Composition from Ref 1 SS-304 Chemical Analysis Table

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
    1. Sandmeyer Steel Company, accessed June 4, 2024, https://www.sandmeyersteel.com
    """

    def __init__(self,
                 name: str = 'SS-304',
                 temperature: float = STANDARD_TEMPERATURE,
                 density: float = 7.90):

        components = { 'C':  0.08,
                      'Mn':  2.00,
                       'P':  0.045,
                       'S':  0.030,
                      'Si':  0.75,
                      'Cr': 20.00,
                      'Ni': 10.5,
                       'N':  0.10,
                      'Fe': 66.495}
        openmc_material = openmc.Material()
        openmc_material.add_components(components, percent_type='wo')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material)

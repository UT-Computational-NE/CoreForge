import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE

class INOR8(Material):
    """ Factory for creating INOR-8 materials

    - Default density from Ref 1 Table 4.4
    - Composition from Ref 1 Table 2.3 and Table 4.4

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
    1. Fratoni M., et. al., "Molten Salt Reactor Experiment Benchmark Evaluation
       (Project 16-10240)", United States, (2020) https://www.osti.gov/servlets/purl/1617123
    """

    def __init__(self,
                 name: str = 'INOR-8',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 8.7745):

        components = {'Ni': 68.0,
                      'Mo': 17.0,
                      'Cr':  7.0,
                      'Fe':  5.0,
                       'C':  0.06,
                      'Ti':  0.2045,
                      'Al':  0.2045,
                       'S':  0.016,
                      'Mn':  0.818,
                      'Si':  0.818,
                      'Cu':  0.286,
                       'B':  0.008,
                       'W':  0.409,
                       'P':  0.012,
                      'Co':  0.164}
        openmc_material = openmc.Material()
        openmc_material.add_components(components, percent_type='wo')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material)

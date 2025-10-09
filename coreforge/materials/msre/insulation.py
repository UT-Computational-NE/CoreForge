import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class Insulation(Material):
    """ Factory for creating   materials

        - Default density from Reference 1 page 12
        - Composition from Section 5.6.6.3 (simplifying to pure Silica)

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
    1. Haubenreich, P. N. Tritium in the MSRE: Calculated Production Rates
       and Observed Amounts. United States: N. p., 1970.
    2. Robertson, R. C., “MSRE Design and Operations Report Part I: Description
       of Reactor Design”, ORNL-TM-0728, Oak Ridge National Laboratory, Oak Ridge, Tennessee (1965).
    """

    def __init__(self,
                 name: str = 'Insulation',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 0.160185):

        openmc_material = openmc.Material()
        openmc_material.add_elements_from_formula('SiO2')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material)

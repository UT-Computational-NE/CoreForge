import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class Mo(Material):
    """Factory for creating molybdenum materials.

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
    .. [1] D. R. Redhouse, et al., "Radiation Characterization Summary: NETL Beam Port
           1/5 Free-Field Environment at the 128-inch Core Centerline Adjacent Location,
           (NETL-FF-BP1/5-128-cca).", Nov. 2022. https://doi.org/10.2172/1898256
           Compositions from pg 60, density from pg 51
    """

    def __init__(self,
                 name: str = 'Mo',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 10.3):

        assert temperature >= 0.0, "Temperature must be positive in Kelvin."
        assert density > 0.0, f"density = {density}"

        openmc_material = openmc.Material(name=name)
        openmc_material.temperature = temperature
        openmc_material.set_density('g/cm3', density)
        openmc_material.add_nuclide('Mo92',  0.1477, percent_type='ao')
        openmc_material.add_nuclide('Mo94',  0.0923, percent_type='ao')
        openmc_material.add_nuclide('Mo95',  0.159,  percent_type='ao')
        openmc_material.add_nuclide('Mo96',  0.1668, percent_type='ao')
        openmc_material.add_nuclide('Mo97',  0.0956, percent_type='ao')
        openmc_material.add_nuclide('Mo98',  0.2419, percent_type='ao')
        openmc_material.add_nuclide('Mo100', 0.0967, percent_type='ao')

        super().__init__(openmc_material)

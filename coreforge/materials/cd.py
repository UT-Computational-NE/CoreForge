import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class Cd(Material):
    """Factory for creating cadmium materials.

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
           Composition from pg. 60 and density from pg. 53.
    """

    def __init__(self,
                 name: str = 'Cd',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 8.65):

        assert temperature >= 0.0, "Temperature must be positive in Kelvin."
        assert density > 0.0, f"density = {density}"

        openmc_material = openmc.Material(name=name)
        openmc_material.temperature = temperature
        openmc_material.set_density('g/cm3', density)
        openmc_material.add_nuclide('Cd106', 0.0125, percent_type='ao')
        openmc_material.add_nuclide('Cd108', 0.0089, percent_type='ao')
        openmc_material.add_nuclide('Cd110', 0.1249, percent_type='ao')
        openmc_material.add_nuclide('Cd111', 0.1280, percent_type='ao')
        openmc_material.add_nuclide('Cd112', 0.2413, percent_type='ao')
        openmc_material.add_nuclide('Cd113', 0.1222, percent_type='ao')
        openmc_material.add_nuclide('Cd114', 0.2873, percent_type='ao')
        openmc_material.add_nuclide('Cd116', 0.0749, percent_type='ao')

        super().__init__(openmc_material)

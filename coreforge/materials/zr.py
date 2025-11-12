import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class Zr(Material):
    """Factory for creating zirconium materials.

    Parameters
    ----------
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    density : float
        The atom density of the material (atom/b-cm)

    References
    ----------
    .. [1] D. R. Redhouse, et al., "Radiation Characterization Summary: NETL Beam Port
           1/5 Free-Field Environment at the 128-inch Core Centerline Adjacent Location,
           (NETL-FF-BP1/5-128-cca).", Nov. 2022. https://doi.org/10.2172/1898256
           Compositions and density from pg 60.
    """

    def __init__(self,
                 name: str = 'Zr',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 6.5):

        assert temperature >= 0.0, "Temperature must be positive in Kelvin."
        assert density > 0.0, f"density = {density}"

        openmc_material = openmc.Material(name=name)
        openmc_material.temperature = temperature
        openmc_material.set_density('g/cm3', density)
        openmc_material.add_nuclide('Zr90', 0.5145, percent_type='ao')
        openmc_material.add_nuclide('Zr91', 0.1122, percent_type='ao')
        openmc_material.add_nuclide('Zr92', 0.1715, percent_type='ao')
        openmc_material.add_nuclide('Zr94', 0.1738, percent_type='ao')
        openmc_material.add_nuclide('Zr96', 0.0280, percent_type='ao')

        super().__init__(openmc_material)

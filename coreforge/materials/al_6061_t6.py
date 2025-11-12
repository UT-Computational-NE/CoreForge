import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class Al6061T6(Material):
    """Factory for creating aluminum 6061-T6 alloy materials.

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
           Compositions from pg 60, density from pg 48
    """

    def __init__(self,
                 name: str = 'Al-6061-T6',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 2.7):

        assert temperature >= 0.0, "Temperature must be positive in Kelvin."
        assert density > 0.0, f"density = {density}"

        openmc_material = openmc.Material(name=name)
        openmc_material.temperature = temperature
        openmc_material.set_density('g/cm3', density)
        openmc_material.add_nuclide('B10',  2.3945e-07, percent_type='ao')
        openmc_material.add_nuclide('Mg24', 0.00053511, percent_type='ao')
        openmc_material.add_nuclide('Mg25', 6.503e-05,  percent_type='ao')
        openmc_material.add_nuclide('Mg26', 6.8851e-05, percent_type='ao')
        openmc_material.add_nuclide('Al27', 0.059015,   percent_type='ao')
        openmc_material.add_nuclide('Si28', 0.00032153, percent_type='ao')
        openmc_material.add_nuclide('Si29', 1.5771e-05, percent_type='ao')
        openmc_material.add_nuclide('Si30', 1.0062e-05, percent_type='ao')
        openmc_material.add_nuclide('Cr50', 2.6872e-06, percent_type='ao')
        openmc_material.add_nuclide('Cr52', 4.983e-05,  percent_type='ao')
        openmc_material.add_nuclide('Cr53', 5.5435e-06, percent_type='ao')
        openmc_material.add_nuclide('Cr54', 1.3544e-06, percent_type='ao')
        openmc_material.add_nuclide('Cu63', 5.0017e-05, percent_type='ao')
        openmc_material.add_nuclide('Cu65', 2.1628e-05, percent_type='ao')

        super().__init__(openmc_material)

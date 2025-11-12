import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class UZrH(Material):
    """Factory for creating U-ZrH (Uranium-Zirconium Hydride) fuel materials.

    This is the standard TRIGA fuel composition with 8.5 wt% uranium enriched to 19.5% in U-235.
    The fuel matrix is zirconium hydride with uranium dispersed throughout.

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
           Compositions from pg 59-60, density from pg 51
    """

    def __init__(self,
                 name: str = 'U-ZrH',
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 5.85):

        assert temperature >= 0.0, "Temperature must be positive in Kelvin."
        assert density > 0.0, f"density = {density}"

        openmc_material = openmc.Material(name=name)
        openmc_material.temperature = temperature
        openmc_material.set_density('g/cm3', density)
        openmc_material.add_nuclide('H1',   0.014355,  percent_type='wo')
        openmc_material.add_nuclide('Mn55', 0.0014287, percent_type='wo')
        openmc_material.add_nuclide('U235', 0.0152,    percent_type='wo')
        openmc_material.add_nuclide('U238', 0.061568,  percent_type='wo')
        openmc_material.add_nuclide('Zr90', 0.43706,   percent_type='wo')
        openmc_material.add_nuclide('Zr91', 0.0942,    percent_type='wo')
        openmc_material.add_nuclide('Zr92', 0.14253,   percent_type='wo')
        openmc_material.add_nuclide('Zr94', 0.14136,   percent_type='wo')
        openmc_material.add_nuclide('Zr96', 0.02228,   percent_type='wo')
        openmc_material.add_element('Cr',   0.013573,  percent_type='wo')
        openmc_material.add_element('Fe',   0.049647,  percent_type='wo')
        openmc_material.add_element('Ni',   0.0067863, percent_type='wo')
        openmc_material.add_s_alpha_beta('c_H_in_ZrH')
        openmc_material.add_s_alpha_beta('c_Zr_in_ZrH')

        super().__init__(openmc_material)

import openmc

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = ['H'],
                                               is_fluid                    = True,
                                               is_depletable               = False,
                                               has_resonance               = False,
                                               is_fuel                     = False)

class Water(Material):
    """ Factory for creating water materials

    Default water density corresponds to standard temperature and pressure

    Parameters
    ----------
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    density : float
        The density of the material (g/cm3)
    mpact_build_specs : Material.MPACTBuildSpecs
        Specifications for building the MPACT material
    """

    def __init__(self,
                 name: str = 'Water',
                 temperature: float = STANDARD_TEMPERATURE,
                 density: float = 1.0,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.add_element('H', 2)
        openmc_material.add_element('O', 1)
        openmc_material.add_s_alpha_beta('c_H_in_H2O')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

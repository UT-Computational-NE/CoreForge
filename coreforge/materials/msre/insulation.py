import openmc

from coreforge.materials.material import Material

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                               is_fluid                    = False,
                                               is_depletable               = False,
                                               has_resonance               = False,
                                               is_fuel                     = False)

class Insulation(Material):
    """ Factory for creating   materials

        - Density from Reference 1 page 12
        - Composition from Section 5.6.6.3 (simplifying to pure Silica)

    Parameters
    ----------
    name : str
        The name for the salt
    temperature : float
        The temperature of the salt (K)
    mpact_build_specs : Material.MPACTBuildSpecs
        Specifications for building the MPACT material

    References
    ----------
    1. Haubenreich, P. N. Tritium in the MSRE: Calculated Production Rates
       and Observed Amounts. United States: N. p., 1970.
    2. Robertson, R. C., “MSRE Design and Operations Report Part I: Description
       of Reactor Design”, ORNL-TM-0728, Oak Ridge National Laboratory, Oak Ridge, Tennessee (1965).
    """

    def __init__(self,
                 name: str = 'Insulation',
                 temperature: float = 900.,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.add_elements_from_formula('SiO2')
        openmc_material.set_density('g/cm3', 0.160185)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

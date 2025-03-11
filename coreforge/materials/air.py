import openmc

from coreforge.materials.material import Material

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                               is_fluid                    = False,
                                               is_depletable               = False,
                                               has_resonance               = False,
                                               is_fuel                     = False)

class Air(Material):
    """ Factory for creating air materials

    Base density and composition from Reference 1.  Composition
    was simplified from Reference 1 to consider only N, O, and Ar,
    meaning the mole fraction of all other particulates are just
    rolled into Ar

    - Density from Reference 1 Section 1
    - Composition from Reference 1 Table 1

    Parameters
    ----------
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    mpact_build_specs : Material.MPACTBuildSpecs
        Specifications for building the MPACT material

    References
    ----------
    1. Picard, A., et al., "Revised formula for the density of moist air (CIPM-2007)",
       Metrologia, 45, pg 149-155. (2008) https://www.nist.gov/system/files/documents/calibrations/CIPM-2007.pdf
    """

    def __init__(self,
                 name: str = 'Air',
                 temperature: float = 900.,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.set_density('g/cc', 0.0012)
        openmc_material.add_element('N',  78.08, percent_type='ao')
        openmc_material.add_element('O',  20.95, percent_type='ao')
        openmc_material.add_element('Ar',  0.97, percent_type='ao')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

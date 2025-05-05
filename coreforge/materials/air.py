import openmc
import mpactpy

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

DEFAULT_MPACT_SPECS = mpactpy.Material.MPACTSpecs(thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

class Air(Material):
    """ Factory for creating dry air materials

    Default density and composition from Reference 1 Section 1. Composition
    was simplified from Reference 1 Table 1 to consider only N, O, and Ar,
    meaning the mole fraction of all other gases are just rolled into Ar

    Table 1:
    .. math::
        \\begin{array}{lc}
        \\hline
        \\text{Constituent} & \\text{Mole fraction } x_i \\\\
        \\hline
        \\text{N}_2 & 0.7808 \\\\
        \\text{O}_2 & 0.2095 \\\\
        \\text{Ar}  & 0.0097 \\\\
        \\hline
        \\end{array}

    Parameters
    ----------
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    density : float
        The density of the material (g/cm3)
    mpact_build_specs : mpactpy.Material.MPACTSpecs
        Specifications for building the MPACT material

    References
    ----------
    1. Picard, A., et al., "Revised formula for the density of moist air (CIPM-2007)",
       Metrologia, 45, pg 149-155. (2008) https://www.nist.gov/system/files/documents/calibrations/CIPM-2007.pdf
    """

    def __init__(self,
                 name: str = 'Air',
                 temperature: float = STANDARD_TEMPERATURE,
                 density: float = 0.0012,
                 mpact_build_specs: mpactpy.Material.MPACTSpecs = DEFAULT_MPACT_SPECS):

        components = { 'N': 78.08,
                       'O': 20.95,
                      'Ar':  0.97,}
        openmc_material = openmc.Material()
        openmc_material.add_components(components, percent_type='ao')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

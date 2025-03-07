import openmc

from coreforge.materials.material_factory import MaterialFactory

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                                      is_fluid                    = False,
                                                      is_depletable               = False,
                                                      has_resonance               = False,
                                                      is_fuel                     = False)

class Insulation(MaterialFactory):
    """ Factory for creating   materials

        - Density from Reference 1 page 12
        - Composition from Section 5.6.6.3 (simplifying to pure Silica)

    References
    ----------
    1. Haubenreich, P. N. Tritium in the MSRE: Calculated Production Rates
       and Observed Amounts. United States: N. p., 1970.
    2. Robertson, R. C., “MSRE Design and Operations Report Part I: Description
       of Reactor Design”, ORNL-TM-0728, Oak Ridge National Laboratory, Oak Ridge, Tennessee (1965).
    """

    def __init__(self,
                 label: str = 'Insulation',
                 temperature: float = 900.,
                 mpact_build_specs: MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):
        self.label             = label
        self.temperature       = temperature
        self.mpact_build_specs = mpact_build_specs

    def make_openmc_material(self) -> openmc.Material:

        insulation = openmc.Material()
        insulation.add_elements_from_formula('SiO2')
        insulation.set_density('g/cm3', 0.160185)
        insulation.temperature = self.temperature
        insulation.name = self.label
        return insulation

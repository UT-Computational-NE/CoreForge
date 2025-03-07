import openmc

from coreforge.materials.material_factory import MaterialFactory

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                                      is_fluid                    = False,
                                                      is_depletable               = False,
                                                      has_resonance               = False,
                                                      is_fuel                     = False)

class Air(MaterialFactory):
    """ Factory for creating air materials

    Base density and composition from Reference 1.  Composition
    was simplified from Reference 1 to consider only N, O, and Ar,
    meaning the mole fraction of all other particulates are just
    rolled into Ar

    - Density from Reference 1 Section 1
    - Composition from Reference 1 Table 1

    References
    ----------
    1. Picard, A., et al., "Revised formula for the density of moist air (CIPM-2007)",
       Metrologia, 45, pg 149-155. (2008) https://www.nist.gov/system/files/documents/calibrations/CIPM-2007.pdf
    """

    def __init__(self,
                 label: str = 'Air',
                 temperature: float = 900.,
                 mpact_build_specs: MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):
        self.label             = label
        self.temperature       = temperature
        self.mpact_build_specs = mpact_build_specs

    def make_openmc_material(self) -> openmc.Material:

        air = openmc.Material()
        air.set_density('g/cc', 0.0012)
        air.add_element('N',  78.08, percent_type='ao')
        air.add_element('O',  20.95, percent_type='ao')
        air.add_element('Ar',  0.97, percent_type='ao')
        air.temperature = self.temperature
        air.name = self.label
        return air

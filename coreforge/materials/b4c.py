import openmc

from coreforge.materials.material_factory import MaterialFactory

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                                      is_fluid                    = False,
                                                      is_depletable               = False,
                                                      has_resonance               = False,
                                                      is_fuel                     = False)

class B4C(MaterialFactory):
    """ Factory for creating B4C Poison material

    - Sepcification in Table 8 of Ref. 1

    References
    ----------
    1. Godfrey A., “VERA Core Physics Benchmark Progression Problem Specifications”, CASL-U-2012-0131-004,
    Consortium for Advanced Simulation of LWRs, (2012) https://corephysics.com/docs/CASL-U-2012-0131-004.pdf
    """

    def __init__(self,
                 label: str = 'B4C',
                 temperature: float = 900.,
                 mpact_build_specs: MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):
        self.label             = label
        self.temperature       = temperature
        self.mpact_build_specs = mpact_build_specs

    def make_openmc_material(self) -> openmc.Material:

        b4c = openmc.Material()
        b4c.set_density('g/cm3', 1.76)
        b4c.add_elements_from_formula('B4C')
        b4c.temperature = self.temperature
        b4c.name = self.label
        return b4c

import openmc

from coreforge.materials.material_factory import MaterialFactory

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = ['H'],
                                                      is_fluid                    = True,
                                                      is_depletable               = False,
                                                      has_resonance               = False,
                                                      is_fuel                     = False)

class Water(MaterialFactory):
    """ Factory for creating water materials

    Base water density corresponds to standard temperature and pressure
    """

    def __init__(self,
                 label: str = 'Water',
                 temperature: float = 900.,
                 mpact_build_specs: MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):
        self.label             = label
        self.temperature       = temperature
        self.mpact_build_specs = mpact_build_specs

    def make_openmc_material(self) -> openmc.Material:

        water = openmc.Material()
        water.add_element('H', 2)
        water.add_element('O', 1)
        water.add_s_alpha_beta('c_H_in_H2O')
        water.set_density('g/cm3', 1.)
        water.temperature = self.temperature
        water.name = self.label
        return water

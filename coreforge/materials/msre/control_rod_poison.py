import openmc

from coreforge.materials.material_factory import MaterialFactory

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                                      is_fluid                    = False,
                                                      is_depletable               = False,
                                                      has_resonance               = True,
                                                      is_fuel                     = False)

class ControlRodPoison(MaterialFactory):
    """ Factory for creating control rod poison materials

    Density and Composition from Reference 1 Table 4.4

    References
    ----------
    1. Fratoni M., et. al., "Molten Salt Reactor Experiment Benchmark Evaluation
       (Project 16-10240)", United States, (2020) https://www.osti.gov/servlets/purl/1617123
    """

    def __init__(self,
                 label: str = 'Poison',
                 temperature: float = 900.,
                 mpact_build_specs: MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):
        self.label             = label
        self.temperature       = temperature
        self.mpact_build_specs = mpact_build_specs

    def make_openmc_material(self) -> openmc.Material:

        gd2o3 = openmc.Material()
        gd2o3.add_elements_from_formula('Gd2O3')

        al2o3 = openmc.Material()
        al2o3.add_elements_from_formula('Al2O3')

        poison = openmc.Material.mix_materials([gd2o3, al2o3], [0.7, 0.3], 'wo')
        poison.set_density('g/cm3', 5.873)
        poison.temperature = self.temperature
        poison.name = self.label
        return poison

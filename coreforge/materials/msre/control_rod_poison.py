import openmc

from coreforge.materials.material import Material

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                               is_fluid                    = False,
                                               is_depletable               = False,
                                               has_resonance               = True,
                                               is_fuel                     = False)

class ControlRodPoison(Material):
    """ Factory for creating control rod poison materials

    Density and Composition from Reference 1 Table 4.4

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
    1. Fratoni M., et. al., "Molten Salt Reactor Experiment Benchmark Evaluation
       (Project 16-10240)", United States, (2020) https://www.osti.gov/servlets/purl/1617123
    """

    def __init__(self,
                 name: str = 'Poison',
                 temperature: float = 900.,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        gd2o3 = openmc.Material()
        gd2o3.add_elements_from_formula('Gd2O3')

        al2o3 = openmc.Material()
        al2o3.add_elements_from_formula('Al2O3')

        openmc_material = openmc.Material.mix_materials([gd2o3, al2o3], [0.7, 0.3], 'wo')
        openmc_material.set_density('g/cm3', 5.873)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

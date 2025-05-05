import openmc
import mpactpy

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

DEFAULT_MPACT_SPECS = mpactpy.Material.MPACTSpecs(thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = True,
                                                  is_fuel                     = False)

class ControlRodPoison(Material):
    """ Factory for creating control rod poison materials

    Default density and Composition from Reference 1 Table 4.4

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
    1. Fratoni M., et. al., "Molten Salt Reactor Experiment Benchmark Evaluation
       (Project 16-10240)", United States, (2020) https://www.osti.gov/servlets/purl/1617123
    """

    def __init__(self,
                 name: str = 'Poison',
                 temperature: float = STANDARD_TEMPERATURE,
                 density: float = 5.873,
                 mpact_build_specs: mpactpy.Material.MPACTSpecs = DEFAULT_MPACT_SPECS):

        gd2o3 = openmc.Material()
        gd2o3.add_elements_from_formula('Gd2O3')

        al2o3 = openmc.Material()
        al2o3.add_elements_from_formula('Al2O3')

        openmc_material = openmc.Material.mix_materials([gd2o3, al2o3], [0.7, 0.3], 'wo')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

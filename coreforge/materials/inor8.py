import openmc

from coreforge.materials.material import Material

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                               is_fluid                    = False,
                                               is_depletable               = False,
                                               has_resonance               = True,
                                               is_fuel                     = False)

class INOR8(Material):
    """ Factory for creating INOR-8 materials

    - Density from Ref 1 Table 4.4
    - Composition from Ref 1 Table 2.3 and Table 4.4

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
                 name: str = 'INOR-8',
                 temperature: float = 900.,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.set_density('g/cm3', 8.7745)
        openmc_material.add_element('Ni',    68., percent_type='wo')
        openmc_material.add_element('Mo',    17., percent_type='wo')
        openmc_material.add_element('Cr',     7., percent_type='wo')
        openmc_material.add_element('Fe',     5., percent_type='wo')
        openmc_material.add_element( 'C',   0.06, percent_type='wo')
        openmc_material.add_element('Ti', 0.2045, percent_type='wo')
        openmc_material.add_element('Al', 0.2045, percent_type='wo')
        openmc_material.add_element( 'S',  0.016, percent_type='wo')
        openmc_material.add_element('Mn',  0.818, percent_type='wo')
        openmc_material.add_element('Si',  0.818, percent_type='wo')
        openmc_material.add_element('Cu',  0.286, percent_type='wo')
        openmc_material.add_element( 'B',  0.008, percent_type='wo')
        openmc_material.add_element( 'W',  0.409, percent_type='wo')
        openmc_material.add_element( 'P',  0.012, percent_type='wo')
        openmc_material.add_element('Co',  0.164, percent_type='wo')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

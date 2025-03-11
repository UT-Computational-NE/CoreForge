import openmc

from coreforge.materials.material import Material

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                               is_fluid                    = False,
                                               is_depletable               = False,
                                               has_resonance               = True,
                                               is_fuel                     = False)

class Inconel(Material):
    """ Factory for creating Inconel materials

    All data retrieved from Ref. 1 from the Inconel Alloy 718 entry

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
    1. MatWeb: Material Property Data accessed June 4, 2024, https://www.matweb.com/
    """

    def __init__(self,
                 name: str = 'Inconel',
                 temperature: float = 900.,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.set_density('g/cm3', 8.19)
        openmc_material.add_element('Al',  0.800, percent_type='ao')
        openmc_material.add_element( 'B',  0.006, percent_type='ao')
        openmc_material.add_element( 'C',  0.080, percent_type='ao')
        openmc_material.add_element('Cr', 21.000, percent_type='ao')
        openmc_material.add_element('Co',  1.000, percent_type='ao')
        openmc_material.add_element('Cu',  0.300, percent_type='ao')
        openmc_material.add_element('Fe', 17.000, percent_type='ao')
        openmc_material.add_element('Mn',  0.350, percent_type='ao')
        openmc_material.add_element('Mo',  3.300, percent_type='ao')
        openmc_material.add_element('Ni', 49.134, percent_type='ao')
        openmc_material.add_element('Nb',  5.500, percent_type='ao')
        openmc_material.add_element( 'P',  0.015, percent_type='ao')
        openmc_material.add_element('Si',  0.350, percent_type='ao')
        openmc_material.add_element( 'S',  0.015, percent_type='ao')
        openmc_material.add_element('Ti',  1.150, percent_type='ao')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

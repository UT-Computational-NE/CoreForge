import openmc

from coreforge.materials.material import Material

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                               is_fluid                    = False,
                                               is_depletable               = False,
                                               has_resonance               = True,
                                               is_fuel                     = False)

class SS316H(Material):
    """ Factory for creating 316H Stainless Steel materials

    - Density from Ref 1 SS-316H Physical Properties Table
    - Composition from Ref 1 SS-316H Chemical Analysis Table

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
    1. Sandmeyer Steel Company, accessed October 10, 2024, https://www.sandmeyersteel.com
    """

    def __init__(self,
                 name: str = 'SS-316H',
                 temperature: float = 900.,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.set_density('g/cm3', 8.0)
        openmc_material.add_element('Cr',   18.0, percent_type='wo')
        openmc_material.add_element('Ni',   14.0, percent_type='wo')
        openmc_material.add_element('Mo',    3.0, percent_type='wo')
        openmc_material.add_element( 'C',   0.1, percent_type='wo')
        openmc_material.add_element('Mn',    2.0, percent_type='wo')
        openmc_material.add_element( 'P',  0.045, percent_type='wo')
        openmc_material.add_element( 'S',   0.03, percent_type='wo')
        openmc_material.add_element('Si',   0.75, percent_type='wo')
        openmc_material.add_element('Fe', 62.075, percent_type='wo')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

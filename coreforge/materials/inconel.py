import openmc
import mpactpy

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

DEFAULT_MPACT_SPECS = mpactpy.Material.MPACTSpecs(thermal_scattering_isotopes = [],
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
    density : float
        The density of the material (g/cm3)
    mpact_build_specs : mpactpy.Material.MPACTSpecs
        Specifications for building the MPACT material

    References
    ----------
    1. MatWeb: Material Property Data accessed June 4, 2024, https://www.matweb.com/
    """

    def __init__(self,
                 name: str = 'Inconel',
                 temperature: float = STANDARD_TEMPERATURE,
                 density: float = 8.19,
                 mpact_build_specs: mpactpy.Material.MPACTSpecs = DEFAULT_MPACT_SPECS):

        components = {'Al':  0.800,
                       'B':  0.006,
                       'C':  0.080,
                      'Cr': 21.000,
                      'Co':  1.000,
                      'Cu':  0.300,
                      'Fe': 17.000,
                      'Mn':  0.350,
                      'Mo':  3.300,
                      'Ni': 49.134,
                      'Nb':  5.500,
                       'P':  0.015,
                      'Si':  0.350,
                       'S':  0.015,
                      'Ti':  1.150}
        openmc_material = openmc.Material()
        openmc_material.add_components(components, percent_type='ao')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

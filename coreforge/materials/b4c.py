import openmc
import mpactpy

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

DEFAULT_MPACT_SPECS = mpactpy.Material.MPACTSpecs(thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

class B4C(Material):
    """ Factory for creating B4C Poison material

    - Sepcification in Table 8 of Ref. 1

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
    1. Godfrey A., “VERA Core Physics Benchmark Progression Problem Specifications”, CASL-U-2012-0131-004,
    Consortium for Advanced Simulation of LWRs, (2012) https://corephysics.com/docs/CASL-U-2012-0131-004.pdf
    """

    def __init__(self,
                 name: str = 'B4C',
                 temperature: float = STANDARD_TEMPERATURE,
                 density: float = 1.76,
                 mpact_build_specs: mpactpy.Material.MPACTSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.set_density('g/cm3', density)
        openmc_material.add_elements_from_formula('B4C')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

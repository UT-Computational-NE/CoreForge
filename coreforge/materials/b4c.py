import openmc

from coreforge.materials.material import Material

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = [],
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
    mpact_build_specs : Material.MPACTBuildSpecs
        Specifications for building the MPACT material

    References
    ----------
    1. Godfrey A., “VERA Core Physics Benchmark Progression Problem Specifications”, CASL-U-2012-0131-004,
    Consortium for Advanced Simulation of LWRs, (2012) https://corephysics.com/docs/CASL-U-2012-0131-004.pdf
    """

    def __init__(self,
                 name: str = 'B4C',
                 temperature: float = 900.,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.set_density('g/cm3', 1.76)
        openmc_material.add_elements_from_formula('B4C')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

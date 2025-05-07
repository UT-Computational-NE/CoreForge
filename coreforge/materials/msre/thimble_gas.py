import openmc
import mpactpy

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

DEFAULT_MPACT_SPECS = mpactpy.Material.MPACTSpecs(thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

class ThimbleGas(Material):
    """ Material for MSRE Thimble Gas materials

    - Default density calculated using CoolProps (Reference 1) at 273.15K and 1 atm
    - Composition from Reference 2 Section 5.3.5.2

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
    1. Bell, Ian H., Wronski, Jorrit, Quoilin, Sylvain, and Lemort, Vincent.
       “Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the Open-Source Thermophysical
       Property Library CoolProp.” Industrial & Engineering Chemistry Research, volume 53, number 6, pages 2498-2508, 2014
    2. Robertson, R. C., “MSRE Design and Operations Report Part I: Description of Reactor Design”,
       ORNL-TM-0728, Oak Ridge National Laboratory, Oak Ridge, Tennessee (1965).
    """

    def __init__(self,
                 name: str = 'Thimble Gas',
                 temperature: float = STANDARD_TEMPERATURE,
                 density: float = 0.00125932,
                 mpact_build_specs: mpactpy.Material.MPACTSpecs = DEFAULT_MPACT_SPECS):

        components = {'N': 95., 'O':  5.,}
        openmc_material = openmc.Material()
        openmc_material.add_components(components, percent_type='wo')
        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

import openmc

from coreforge.materials.material import Material

DEFAULT_MPACT_SPECS = Material.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                               is_fluid                    = False,
                                               is_depletable               = False,
                                               has_resonance               = False,
                                               is_fuel                     = False)

class Helium(Material):
    """ Factory for creating Helium Gas materials

    Density calculated using CoolProps (Reference 1) at 300K and 1 atm

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
    1. Bell, Ian H., Wronski, Jorrit, Quoilin, Sylvain, and Lemort, Vincent.
    “Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the
    Open-Source Thermophysical Property Library CoolProp.” Industrial & Engineering
    Chemistry Research, volume 53, number 6, pages 2498-2508, 2014
    """

    def __init__(self,
                 name: str = 'Helium',
                 temperature: float = 900.,
                 mpact_build_specs: Material.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        openmc_material = openmc.Material()
        openmc_material.set_density('g/cm3', 0.0001625)
        openmc_material.add_element('He', 100., percent_type='wo')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material, mpact_build_specs)

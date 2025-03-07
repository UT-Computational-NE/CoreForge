import openmc

from coreforge.materials.material_factory import MaterialFactory

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                                      is_fluid                    = False,
                                                      is_depletable               = False,
                                                      has_resonance               = False,
                                                      is_fuel                     = False)

class Helium(MaterialFactory):
    """ Factory for creating Helium Gas materials

    Density calculated using CoolProps (Reference 1) at 300K and 1 atm

    References
    ----------
    1. Bell, Ian H., Wronski, Jorrit, Quoilin, Sylvain, and Lemort, Vincent.
    “Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the
    Open-Source Thermophysical Property Library CoolProp.” Industrial & Engineering
    Chemistry Research, volume 53, number 6, pages 2498-2508, 2014
    """

    def __init__(self,
                 label: str = 'Helium',
                 temperature: float = 900.,
                 mpact_build_specs: MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):
        self.label             = label
        self.temperature       = temperature
        self.mpact_build_specs = mpact_build_specs

    def make_openmc_material(self) -> openmc.Material:

        gas = openmc.Material()
        gas.set_density('g/cm3', 0.0001625)
        gas.add_element('He', 100., percent_type='wo')
        gas.temperature = self.temperature
        gas.name = self.label
        return gas

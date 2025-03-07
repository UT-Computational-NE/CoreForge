import openmc

from coreforge.materials.material_factory import MaterialFactory

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                                      is_fluid                    = False,
                                                      is_depletable               = False,
                                                      has_resonance               = True,
                                                      is_fuel                     = False)

class SS304(MaterialFactory):
    """ Factory for creating 304 Stainless Steel materials

    - Density from Ref 1 SS-304 Physical Properties Table
    - Composition from Ref 1 SS-304 Chemical Analysis Table

    References
    ----------
    1. Sandmeyer Steel Company, accessed June 4, 2024, https://www.sandmeyersteel.com
    """

    def __init__(self,
                 label: str = 'SS-304',
                 temperature: float = 900.,
                 mpact_build_specs: MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):
        self.label             = label
        self.temperature       = temperature
        self.mpact_build_specs = mpact_build_specs

    def make_openmc_material(self) -> openmc.Material:

        ss = openmc.Material()
        ss.set_density('g/cm3', 7.90)
        ss.add_element( 'C',  0.08,  percent_type='wo')
        ss.add_element('Mn',  2.00,  percent_type='wo')
        ss.add_element( 'P',  0.045, percent_type='wo')
        ss.add_element( 'S',  0.030, percent_type='wo')
        ss.add_element('Si',  0.75,  percent_type='wo')
        ss.add_element('Cr', 20.00,  percent_type='wo')
        ss.add_element('Ni',  10.5,  percent_type='wo')
        ss.add_element( 'N',  0.10,  percent_type='wo')
        ss.add_element('Fe', 66.495, percent_type='wo')
        ss.temperature = self.temperature
        ss.name = self.label
        return ss

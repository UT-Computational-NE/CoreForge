import openmc

from coreforge.materials.material_factory import MaterialFactory

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = [],
                                                      is_fluid                    = False,
                                                      is_depletable               = False,
                                                      has_resonance               = True,
                                                      is_fuel                     = False)

class Inconel(MaterialFactory):
    """ Factory for creating Inconel materials

    All data retrieved from Ref. 1 from the Inconel Alloy 718 entry

    References
    ----------
    1. MatWeb: Material Property Data accessed June 4, 2024, https://www.matweb.com/
    """

    def __init__(self,
                 label: str = 'Inconel',
                 temperature: float = 900.,
                 mpact_build_specs: MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):
        self.label             = label
        self.temperature       = temperature
        self.mpact_build_specs = mpact_build_specs

    def make_openmc_material(self) -> openmc.Material:

        inconel = openmc.Material()
        inconel.set_density('g/cm3', 8.19)
        inconel.add_element('Al',  0.800, percent_type='ao')
        inconel.add_element( 'B',  0.006, percent_type='ao')
        inconel.add_element( 'C',  0.080, percent_type='ao')
        inconel.add_element('Cr', 21.000, percent_type='ao')
        inconel.add_element('Co',  1.000, percent_type='ao')
        inconel.add_element('Cu',  0.300, percent_type='ao')
        inconel.add_element('Fe', 17.000, percent_type='ao')
        inconel.add_element('Mn',  0.350, percent_type='ao')
        inconel.add_element('Mo',  3.300, percent_type='ao')
        inconel.add_element('Ni', 49.134, percent_type='ao')
        inconel.add_element('Nb',  5.500, percent_type='ao')
        inconel.add_element( 'P',  0.015, percent_type='ao')
        inconel.add_element('Si',  0.350, percent_type='ao')
        inconel.add_element( 'S',  0.015, percent_type='ao')
        inconel.add_element('Ti',  1.150, percent_type='ao')
        inconel.temperature = self.temperature
        inconel.name = self.label
        return inconel

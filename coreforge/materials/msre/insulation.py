import openmc

from coreforge.materials.material_factory import MaterialFactory

class Insulation(MaterialFactory):
    """ Factory for creating   materials

        - Density from Reference 1 page 12
        - Composition from Section 5.6.6.3 (simplifying to pure Silica)

    References
    ----------
    1. Haubenreich, P. N. Tritium in the MSRE: Calculated Production Rates
       and Observed Amounts. United States: N. p., 1970.
    2. Robertson, R. C., “MSRE Design and Operations Report Part I: Description
       of Reactor Design”, ORNL-TM-0728, Oak Ridge National Laboratory, Oak Ridge, Tennessee (1965).
    """

    def __init__(self):
        pass

    def make_material(self) -> openmc.Material:

        insulation = openmc.Material()
        insulation.add_elements_from_formula('SiO2')
        insulation.set_density('g/cm3', 0.160185)
        insulation.temperature = 900.
        insulation.name = 'Insulation'
        return insulation

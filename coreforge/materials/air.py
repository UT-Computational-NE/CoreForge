import openmc

from coreforge.materials.material_factory import MaterialFactory

class Air(MaterialFactory):
    """ Factory for creating air materials

    Base density and composition from Reference 1.  Composition
    was simplified from Reference 1 to consider only N, O, and Ar,
    meaning the mole fraction of all other particulates are just
    rolled into Ar

    - Density from Reference 1 Section 1
    - Composition from Reference 1 Table 1

    References
    ----------
    1. Picard, A., et al., "Revised formula for the density of moist air (CIPM-2007)",
       Metrologia, 45, pg 149-155. (2008) https://www.nist.gov/system/files/documents/calibrations/CIPM-2007.pdf
    """

    def __init__(self):
        pass

    def make_material(self) -> openmc.Material:

        air = openmc.Material()
        air.set_density('g/cc', 0.0012)
        air.add_element('N',  78.08, percent_type='ao')
        air.add_element('O',  20.95, percent_type='ao')
        air.add_element('Ar',  0.97, percent_type='ao')
        air.temperature = 900.
        air.name = 'Air'
        return air

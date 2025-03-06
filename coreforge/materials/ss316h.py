import openmc

from coreforge.materials.material_factory import MaterialFactory

class SS316H(MaterialFactory):
    """ Factory for creating 316H Stainless Steel materials

    - Density from Ref 1 SS-316H Physical Properties Table
    - Composition from Ref 1 SS-316H Chemical Analysis Table

    References
    ----------
    1. Sandmeyer Steel Company, accessed October 10, 2024, https://www.sandmeyersteel.com
    """

    def __init__(self):
        pass

    def make_material(self) -> openmc.Material:

        ss = openmc.Material()
        ss.set_density('g/cm3', 8.0)
        ss.add_element('Cr',   18.0, percent_type='wo')
        ss.add_element('Ni',   14.0, percent_type='wo')
        ss.add_element('Mo',    3.0, percent_type='wo')
        ss.add_element( 'C',   0.1, percent_type='wo')
        ss.add_element('Mn',    2.0, percent_type='wo')
        ss.add_element( 'P',  0.045, percent_type='wo')
        ss.add_element( 'S',   0.03, percent_type='wo')
        ss.add_element('Si',   0.75, percent_type='wo')
        ss.add_element('Fe', 62.075, percent_type='wo')
        ss.temperature = 900.
        ss.name = 'SS-316H'
        return ss

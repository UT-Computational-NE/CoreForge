import openmc

from coreforge.materials.material_factory import MaterialFactory

class INOR8(MaterialFactory):
    """ Factory for creating INOR-8 materials

    - Density from Ref 1 Table 4.4
    - Composition from Ref 1 Table 2.3 and Table 4.4

    References
    ----------
    1. Fratoni M., et. al., "Molten Salt Reactor Experiment Benchmark Evaluation
       (Project 16-10240)", United States, (2020) https://www.osti.gov/servlets/purl/1617123
    """

    def __init__(self):
        pass

    def make_material(self) -> openmc.Material:

        inor = openmc.Material()
        inor.set_density('g/cm3', 8.7745)
        inor.add_element('Ni',    68., percent_type='wo')
        inor.add_element('Mo',    17., percent_type='wo')
        inor.add_element('Cr',     7., percent_type='wo')
        inor.add_element('Fe',     5., percent_type='wo')
        inor.add_element( 'C',   0.06, percent_type='wo')
        inor.add_element('Ti', 0.2045, percent_type='wo')
        inor.add_element('Al', 0.2045, percent_type='wo')
        inor.add_element( 'S',  0.016, percent_type='wo')
        inor.add_element('Mn',  0.818, percent_type='wo')
        inor.add_element('Si',  0.818, percent_type='wo')
        inor.add_element('Cu',  0.286, percent_type='wo')
        inor.add_element( 'B',  0.008, percent_type='wo')
        inor.add_element( 'W',  0.409, percent_type='wo')
        inor.add_element( 'P',  0.012, percent_type='wo')
        inor.add_element('Co',  0.164, percent_type='wo')
        inor.temperature = 900.
        inor.name = 'INOR-8'
        return inor

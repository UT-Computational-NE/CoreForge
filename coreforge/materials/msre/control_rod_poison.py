import openmc

from coreforge.materials.material_factory import MaterialFactory

class ControlRodPoison(MaterialFactory):
    """ Factory for creating control rod poison materials

    Density and Composition from Reference 1 Table 4.4

    References
    ----------
    1. Fratoni M., et. al., "Molten Salt Reactor Experiment Benchmark Evaluation
       (Project 16-10240)", United States, (2020) https://www.osti.gov/servlets/purl/1617123
    """

    def __init__(self):
        pass

    def make_material(self) -> openmc.Material:

        gd2o3 = openmc.Material()
        gd2o3.add_elements_from_formula('Gd2O3')

        al2o3 = openmc.Material()
        al2o3.add_elements_from_formula('Al2O3')

        poison = openmc.Material.mix_materials([gd2o3, al2o3], [0.7, 0.3], 'wo')
        poison.set_density('g/cm3', 5.873)
        poison.temperature = 900.
        poison.name = 'Poison'
        return poison

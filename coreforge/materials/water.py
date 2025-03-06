import openmc

from coreforge.materials.material_factory import MaterialFactory

class Water(MaterialFactory):
    """ Factory for creating water materials

    Base water density corresponds to standard temperature and pressure
    """

    def __init__(self):
        pass

    def make_material(self) -> openmc.Material:

        water = openmc.Material()
        water.add_element('H', 2)
        water.add_element('O', 1)
        water.add_s_alpha_beta('c_H_in_H2O')
        water.set_density('g/cm3', 1.)
        water.temperature = 900.
        water.name = 'Water'
        return water
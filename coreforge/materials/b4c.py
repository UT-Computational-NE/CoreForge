import openmc

from coreforge.materials.material_factory import MaterialFactory

class B4C(MaterialFactory):
    """ Factory for creating B4C Poison material

    - Sepcification in Table 8 of Ref. 1

    References
    ----------
    1. Godfrey A., “VERA Core Physics Benchmark Progression Problem Specifications”, CASL-U-2012-0131-004,
    Consortium for Advanced Simulation of LWRs, (2012) https://corephysics.com/docs/CASL-U-2012-0131-004.pdf
    """

    def __init__(self):
        pass

    def make_material(self) -> openmc.Material:

            b4c = openmc.Material()
            b4c.set_density('g/cm3', 1.76)
            b4c.add_elements_from_formula('B4C')
            b4c.temperature = 900.
            b4c.name = 'B4C'
            return b4c
import openmc

from coreforge.materials.material_factory import MaterialFactory

class ThimbleGas(MaterialFactory):
    """ Factory for creating MSRE Thimble Gas materials

    - Density calculated using CoolProps (Reference 1) at 300K and 1 atm
    - Composition from Reference 2 Section 5.3.5.2

    References
    ----------
    1. Bell, Ian H., Wronski, Jorrit, Quoilin, Sylvain, and Lemort, Vincent.
       “Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the Open-Source Thermophysical
       Property Library CoolProp.” Industrial & Engineering Chemistry Research, volume 53, number 6, pages 2498-2508, 2014
    2. Robertson, R. C., “MSRE Design and Operations Report Part I: Description of Reactor Design”,
       ORNL-TM-0728, Oak Ridge National Laboratory, Oak Ridge, Tennessee (1965).
    """

    def __init__(self):
        pass

    def make_material(self) -> openmc.Material:

        gas = openmc.Material()
        gas.set_density('g/cm3', 0.001146)
        gas.add_element('N', 95., percent_type='wo')
        gas.add_element('O',  5., percent_type='wo')
        gas.temperature = 900.
        gas.name = 'Thimble Gas'
        return gas

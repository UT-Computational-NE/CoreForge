from typing import TypedDict
from math import isclose

import openmc

from coreforge.materials.material import Material

class Salt(Material):
    """ Factory for creating materials based on the MSRE fuel salt

    Salt composition will default to what is specified in Ref 1:
        - Density (Table 4.4)
        - Composition (Section 3.2)
        - U-235 Enrichment (Table 3.3)
        - Li-7 Enrichment (Section 3.2)
    Isotopic concentration of Uranium based on enrichment is calculated
    using what is specified in Ref 2 in Section 3.3

    Parameters
    ----------
    density : float
        Density of the salt (g/cm3)
    composition : Composition
        Composition of the salt (mol%)
        Acceptable Keys: 'LiF', 'BeF2', 'ZrF4', 'UF4'
    uranium_enrichment : float
        U-235 enrichment of the uranium in the salt (wt%)
    lithium_enrichment : float
        Li-7 enrichment of the lithium in the salt (wt%)
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)

    Attributes
    ----------
    composition : Composition
        Composition of the salt (mol%)
        Acceptable Keys: 'LiF', 'BeF2', 'ZrF4', 'UF4'
    uranium_enrichment : float
        U-235 enrichment of the uranium in the salt (wt%)
    lithium_enrichment : float
        Li-7 enrichment of the lithium in the salt (wt%)

    References
    ----------
    1. Fratoni M., et. al., "Molten Salt Reactor Experiment Benchmark Evaluation (Project 16-10240)",
       United States, (2020) https://www.osti.gov/servlets/purl/1617123
    2. Palmtag, S., "VERAIn User's Manual", ORNL/SPR-2022-2509, VERA: Virtual Environment for Reactor
       Applications, (2022) https://info.ornl.gov/sites/publications/Files/Pub179530.pdf
    """

    class Composition(TypedDict):
        """ TypedDict class for MSRE Salt Compositions
        """
        LiF:  float
        BeF2: float
        ZrF4: float
        UF4:  float

    @property
    def composition(self) -> Composition:
        return self._composition

    @property
    def uranium_enrichment(self) -> float:
        return self._uranium_enrichment

    @property
    def lithium_enrichment(self) -> float:
        return self._lithium_enrichment


    def __init__(self,
                 density:            float = 2.3275,
                 composition:        Composition = {"LiF": 0.6488, "BeF2": 0.2927, "ZrF4": 0.0506, "UF4": 0.0079},
                 uranium_enrichment: float = 31.355,
                 lithium_enrichment: float = 99.995,
                 name:               str = 'Salt',
                 temperature:        float = 900.):

        assert density > 0., f"density = {density}"
        assert all(values >= 0. for values in composition.values()), \
            f"composition = {composition}"
        assert isclose(sum(values for values in composition.values()), 1.0), \
            f"composition = {composition}"
        assert 0. <= uranium_enrichment  <= 100., f"uranium_enrichment = {uranium_enrichment}"
        assert 0. <= lithium_enrichment <= 100., f"lithium_enrichment = {lithium_enrichment}"
        assert temperature >= 0., f"temperature = {temperature}"

        self._composition        = composition
        self._uranium_enrichment = uranium_enrichment
        self._lithium_enrichment = lithium_enrichment

        lif  = openmc.Material()
        lif.add_elements_from_formula('LiF', enrichment=self.lithium_enrichment, enrichment_target='Li7', enrichment_type='wo')

        bef2 = openmc.Material()
        bef2.add_elements_from_formula('BeF2')

        zrf4 = openmc.Material()
        zrf4.add_elements_from_formula('ZrF4')

        u234 = openmc.Material()
        u234.add_nuclide('U234', 1.)

        u235 = openmc.Material()
        u235.add_nuclide('U235', 1.)

        u236 = openmc.Material()
        u236.add_nuclide('U236', 1.)

        u238 = openmc.Material()
        u238.add_nuclide('U238', 1.)

        w_235 = self.uranium_enrichment / 100.
        w_234 = 0.0089 * w_235
        w_236 = 0.0046 * w_235
        w_238 = 1. - w_234 - w_235 - w_236

        u    = openmc.Material.mix_materials([u234, u235, u236, u238], [w_234, w_235, w_236, w_238], 'wo')
        f    = openmc.Material()
        f.add_element('F', 1.)
        uf4  = openmc.Material.mix_materials([u,f], [0.2, 0.8], 'ao')

        fractions = [self.composition[i] if i in self.composition else 0.0 for i in ["LiF", "BeF2", "ZrF4", "UF4"]]
        openmc_material = openmc.Material.mix_materials([lif, bef2, zrf4, uf4], fractions, 'ao')

        openmc_material.set_density('g/cm3', density)
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material)

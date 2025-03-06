from typing import Dict
import warnings

import openmc

from coreforge.materials.material_factory import MaterialFactory

GRAPHITE_THEORETICAL_DENSITY = {'min' : 2.3, 'max': 2.72}  # g/cc  CRC Handbook of Chemistry and Physics 104th Edition (Table: Density Ranges of Solid Materials)

class Graphite(MaterialFactory):
    """ Factory for creating graphite materials

    If no value is provided for the theoretical density,
    the maximum theoretical density of pure graphite will be used
    from Ref 1 Table: Density Ranges of Solid Materials

    Attributes
    ----------
    density : float
        The density of the graphite (g/cc)
    boron_equiv_contamination : float
        The boron equivalent contamination of the graphite (wt%)
    pore_intrusion : Dict[openmc.Material, float]
        Specifications on the intrusion of material into the graphite pores
        (key: intruding material, value: fraction of graphite volume filled by intruding material)
    theoretical_density : float
        The theoretical density of graphite with no pores / voids (g/cc)

    References
    ----------
    1. CRC Handbook of Chemistry and Physics 104th Edition
    """

    @property
    def density(self) -> float:
        return self._density

    @density.setter
    def density(self, density: float) -> None:
        assert density > 0.
        self._density = density

    @property
    def boron_equiv_contamination(self) -> float:
        return self._boron_equiv_contamination

    @boron_equiv_contamination.setter
    def boron_equiv_contamination(self, boron_equiv_contamination: float) -> None:
        assert boron_equiv_contamination >= 0.
        assert boron_equiv_contamination <= 1.
        self._boron_equiv_contamination = boron_equiv_contamination

    @property
    def pore_intrusion(self) -> Dict[openmc.Material, float]:
        return self._pore_intrusion

    @pore_intrusion.setter
    def pore_intrusion(self, pore_intrusion: Dict[openmc.Material, float]) -> None:
        assert all(values >= 0. for values in pore_intrusion.values())
        assert sum([values for values in pore_intrusion.values()]) <= 1.0 or len(pore_intrusion.values()) == 0
        self._pore_intrusion = pore_intrusion

    @property
    def theoretical_density(self) -> float:
        return self._theoretical_density

    @theoretical_density.setter
    def theoretical_density(self, theoretical_density: float) -> None:
        assert theoretical_density > 0.
        self._theoretical_density = theoretical_density


    def __init__(self,
                 density:                   float,
                 boron_equiv_contamination: float = 0.,
                 pore_intrusion:            Dict[openmc.Material, float] = {},
                 theoretical_density:       float = GRAPHITE_THEORETICAL_DENSITY['max']):

        self.density                   = density
        self.boron_equiv_contamination = boron_equiv_contamination
        self.pore_intrusion            = pore_intrusion
        self.theoretical_density       = theoretical_density


    def make_material(self) -> openmc.Material:

        b_frac = self.boron_equiv_contamination/100.
        c_frac = 1. - b_frac

        c = openmc.Material(); c.add_element('C', 1.)
        b = openmc.Material(); b.add_element('B', 1.)

        pure_graphite = openmc.Material.mix_materials([c, b], [c_frac, b_frac], 'wo')
        pure_graphite.set_density('g/cm3', self.theoretical_density)
        porosity = 1. - self.density / self.theoretical_density

        materials = [pure_graphite]
        vol_fracs = [(1. - porosity)]

        assert(sum([values for values in self.pore_intrusion.values()]) <= porosity)
        for material, intrusion_frac in self.pore_intrusion.items():
            materials.append(material)
            vol_fracs.append(intrusion_frac)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning) # This is for ignoring "Warning: sum of fractions do not add to 1, void fraction set to..."
            graphite = openmc.Material.mix_materials(materials, vol_fracs, 'vo')

        graphite.add_s_alpha_beta('c_Graphite')
        graphite.temperature = 900.
        graphite.name = 'Graphite'

        return graphite
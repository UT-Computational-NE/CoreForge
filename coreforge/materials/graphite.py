from typing import Dict
import warnings

import openmc

from coreforge.materials.material_factory import MaterialFactory

# g/cc  CRC Handbook of Chemistry and Physics 104th Edition (Table: Density Ranges of Solid Materials)
GRAPHITE_THEORETICAL_DENSITY = {'min' : 2.3, 'max': 2.72}

DEFAULT_MPACT_SPECS = MaterialFactory.MPACTBuildSpecs(thermal_scattering_isotopes = ['C'],
                                                      is_fluid                    = False,
                                                      is_depletable               = False,
                                                      has_resonance               = False,
                                                      is_fuel                     = False)

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
        assert density > 0., f"density = {density}"
        self._density = density

    @property
    def boron_equiv_contamination(self) -> float:
        return self._boron_equiv_contamination

    @boron_equiv_contamination.setter
    def boron_equiv_contamination(self, boron_equiv_contamination: float) -> None:
        assert boron_equiv_contamination >= 0., f"boron_equiv_contamination = {boron_equiv_contamination}"
        assert boron_equiv_contamination <= 1., f"boron_equiv_contamination = {boron_equiv_contamination}"
        self._boron_equiv_contamination = boron_equiv_contamination

    @property
    def pore_intrusion(self) -> Dict[openmc.Material, float]:
        return self._pore_intrusion

    @pore_intrusion.setter
    def pore_intrusion(self, pore_intrusion: Dict[openmc.Material, float]) -> None:
        assert all(values >= 0. for values in pore_intrusion.values()), f"pore_intrusion = {pore_intrusion}"
        assert sum(values for values in pore_intrusion.values()) <= 1.0 or len(pore_intrusion.values()) == 0, \
            f"pore_intrusion = {pore_intrusion}"
        self._pore_intrusion = pore_intrusion

    @property
    def theoretical_density(self) -> float:
        return self._theoretical_density

    @theoretical_density.setter
    def theoretical_density(self, theoretical_density: float) -> None:
        assert theoretical_density > 0., f"theoretical_density = {theoretical_density}"
        self._theoretical_density = theoretical_density


    def __init__(self,
                 density:                   float,
                 boron_equiv_contamination: float = 0.,
                 pore_intrusion:            Dict[openmc.Material, float] = {},
                 label:                     str = 'Graphite',
                 theoretical_density:       float = GRAPHITE_THEORETICAL_DENSITY['max'],
                 temperature:               float = 900.,
                 mpact_build_specs:         MaterialFactory.MPACTBuildSpecs = DEFAULT_MPACT_SPECS):

        self.density                   = density
        self.boron_equiv_contamination = boron_equiv_contamination
        self.pore_intrusion            = pore_intrusion
        self.theoretical_density       = theoretical_density
        self.label                     = label
        self.temperature               = temperature
        self.mpact_build_specs         = mpact_build_specs


    def make_openmc_material(self) -> openmc.Material:

        b_frac = self.boron_equiv_contamination/100.
        c_frac = 1. - b_frac

        c = openmc.Material()
        c.add_element('C', 1.)
        b = openmc.Material()
        b.add_element('B', 1.)

        pure_graphite = openmc.Material.mix_materials([c, b], [c_frac, b_frac], 'wo')
        pure_graphite.set_density('g/cm3', self.theoretical_density)
        porosity = 1. - self.density / self.theoretical_density

        materials = [pure_graphite]
        vol_fracs = [(1. - porosity)]

        assert sum(values for values in self.pore_intrusion.values()) <= porosity, \
            f"porosity = {porosity}, pore_intrusion = {self.pore_intrusion}"
        for material, intrusion_frac in self.pore_intrusion.items():
            materials.append(material)
            vol_fracs.append(intrusion_frac)

        # This is for ignoring "Warning: sum of fractions do not add to 1, void fraction set to..."
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            graphite = openmc.Material.mix_materials(materials, vol_fracs, 'vo')

        graphite.add_s_alpha_beta('c_Graphite')
        graphite.temperature = self.temperature
        graphite.name = self.label

        return graphite

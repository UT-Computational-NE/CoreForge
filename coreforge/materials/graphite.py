from typing import Dict
import warnings
from contextlib import contextmanager

import openmc

from coreforge.materials.material import Material, STANDARD_TEMPERATURE

# g/cm3  CRC Handbook of Chemistry and Physics 104th Edition (Table: Density Ranges of Solid Materials)
GRAPHITE_THEORETICAL_DENSITY = {'min' : 2.3, 'max': 2.72}


class Graphite(Material):
    """ Factory for creating graphite materials

    If no value is provided for the theoretical density,
    the maximum theoretical density of pure graphite will be used
    from Ref 1 Table: Density Ranges of Solid Materials

    Parameters
    ----------
    graphite_density : float
        The density of the graphite (g/cm3)
    boron_equiv_contamination : float
        The boron equivalent contamination of the graphite (wt%)
    pore_intrusion : Dict[openmc.Material, float]
        Specifications on the intrusion of material into the graphite pores
        (key: intruding material, value: fraction of graphite volume filled by intruding material)
    theoretical_graphite_density : float
        The theoretical density of graphite with no pores / voids (g/cm3)
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    suppress_warnings : bool
        A flag for suppressing OpenMC warnings that arise during material creation.
        Default setting is True.

    Attributes
    ----------
    graphite_density : float
        The density of the graphite (g/cm3)
    boron_equiv_contamination : float
        The boron equivalent contamination of the graphite (wt%)
    pore_intrusion : Dict[Material, float]
        Specifications on the intrusion of material into the graphite pores
        (key: intruding material, value: fraction of graphite volume filled by intruding material)
    theoretical_graphite_density : float
        The theoretical density of graphite with no pores / voids (g/cm3)


    References
    ----------
    1. CRC Handbook of Chemistry and Physics 104th Edition
    """

    @property
    def graphite_density(self) -> float:
        return self._graphite_density

    @property
    def boron_equiv_contamination(self) -> float:
        return self._boron_equiv_contamination

    @property
    def pore_intrusion(self) -> Dict[Material, float]:
        return self._pore_intrusion

    @property
    def theoretical_graphite_density(self) -> float:
        return self._theoretical_graphite_density

    def __init__(self,
                 graphite_density:             float,
                 boron_equiv_contamination:    float = 0.,
                 pore_intrusion:               Dict[Material, float] = {},
                 name:                         str = 'Graphite',
                 temperature:                  float = STANDARD_TEMPERATURE,
                 theoretical_graphite_density: float = GRAPHITE_THEORETICAL_DENSITY['max'],
                 suppress_warnings:            bool = True):

        assert graphite_density > 0., f"density = {graphite_density}"
        assert 0. <= boron_equiv_contamination <= 100., \
            f"boron_equiv_contamination = {boron_equiv_contamination}"
        assert all(values >= 0. for values in pore_intrusion.values()), \
            f"pore_intrusion = {pore_intrusion}"
        assert sum(values for values in pore_intrusion.values()) <= 1.0 or \
               len(pore_intrusion.values()) == 0, \
            f"pore_intrusion = {pore_intrusion}"
        assert theoretical_graphite_density > 0.,\
            f"theoretical_density = {theoretical_graphite_density}"

        self._graphite_density             = graphite_density
        self._boron_equiv_contamination    = boron_equiv_contamination
        self._pore_intrusion               = pore_intrusion
        self._theoretical_graphite_density = theoretical_graphite_density

        b_frac = self.boron_equiv_contamination/100.
        c_frac = 1. - b_frac

        c = openmc.Material()
        c.add_element('C', 1.)
        b = openmc.Material()
        b.add_element('B', 1.)

        pure_graphite = openmc.Material.mix_materials([c, b], [c_frac, b_frac], 'wo')
        pure_graphite.set_density('g/cm3', self.theoretical_graphite_density)
        porosity = 1. - graphite_density / self.theoretical_graphite_density

        materials = [pure_graphite]
        vol_fracs = [(1. - porosity)]

        assert sum(values for values in self.pore_intrusion.values()) <= porosity, \
            f"porosity = {porosity}, pore_intrusion = {self.pore_intrusion}"
        for material, intrusion_frac in self.pore_intrusion.items():
            materials.append(material.openmc_material)
            vol_fracs.append(intrusion_frac)

        @contextmanager
        def warning_suppressor(enabled: bool):
            """
            A simple context manager to suppress OpenMC's warning for the sum fraction
            not adding to 1.0 and setting the remaining volume to void
            """
            if enabled:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    yield
            else:
                yield

        with warning_suppressor(suppress_warnings):
            openmc_material = openmc.Material.mix_materials(materials, vol_fracs, 'vo')

        openmc_material.add_s_alpha_beta('c_Graphite')
        openmc_material.temperature = temperature
        openmc_material.name = name

        super().__init__(openmc_material)

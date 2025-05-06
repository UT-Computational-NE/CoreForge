from abc import ABC
from typing import Dict, Optional, Any
from math import isclose

import openmc
import mpactpy
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

STANDARD_TEMPERATURE = 273.15

class Material(ABC):
    """ An interface class for translating materials into solver specific representations

    Parameters
    ----------
    openmc_material : openmc.Material
        The OpenMC Material object used to define this material
    mpact_build_specs : Optional[mpactpy.Material.MPACTSpecs]
        Specifications for building the MPACT material

    Attributes
    ----------
    mpact_build_specs : Optional[mpactpy.Material.MPACTSpecs]
        Specifications for building the MPACT material
    openmc_material : openmc.Material
        The OpenMC Material object representing this material
    mpact_material : mpactpy.Material
        The MPACT Material object representing this material
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    density : float
        The density of the material (g/cm3)
    number_densities : Dict[str, float]
        The isotopic number densities (atom/b-cm)
        Dictionary keys are nuclide names and values are number densities.
    """

    @property
    def mpact_build_specs(self) -> Optional[mpactpy.Material.MPACTSpecs]:
        return self._mpact_build_specs

    @mpact_build_specs.setter
    def mpact_build_specs(self, mpact_build_specs: Optional[mpactpy.Material.MPACTSpecs] = None) -> None:
        self._mpact_build_specs = mpact_build_specs
        if mpact_build_specs:
            self._mpact_material = mpactpy.Material.from_openmc_material(self.openmc_material,
                                                                         mpact_build_specs)

    @property
    def openmc_material(self) -> openmc.Material:
        return self._openmc_material

    @property
    def mpact_material(self) -> mpactpy.Material:
        assert self.mpact_build_specs, \
            f"{self.name} was not provided mpact_build_specs"
        return self._mpact_material

    @property
    def name(self) -> str:
        return self._openmc_material.name

    @property
    def temperature(self) -> float:
        return self._openmc_material.temperature

    @property
    def density(self) -> float:
        return self._openmc_material.get_mass_density()

    @property
    def number_densities(self) -> Dict[str, float]:
        return self._openmc_material.get_nuclide_atom_densities()


    def __init__(self,
                 openmc_material: openmc.Material,
                 mpact_build_specs: Optional[mpactpy.Material.MPACTSpecs] = None) -> None:

        self._openmc_material = openmc_material
        self.mpact_build_specs = mpact_build_specs

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Material)                                   and
                isclose(self.density, other.density, rel_tol=TOL)             and
                isclose(self.temperature, other.temperature, rel_tol=TOL)     and
                self.number_densities.keys() == other.number_densities.keys() and
                all(isclose(self.number_densities[iso], other.number_densities[iso], rel_tol=TOL)
                    for iso in self.number_densities.keys())
        )

    def __hash__(self) -> int:
        number_densities = sorted({iso: relative_round(numd, TOL)
                                   for iso, numd in self.number_densities.items()})
        return hash((relative_round(self.density, TOL),
                     relative_round(self.temperature, TOL),
                     tuple(number_densities)))

from abc import ABC
from dataclasses import dataclass
from typing import Dict, List, Union, Optional, Any

import openmc
import mpactpy.material

class Material(ABC):
    """ An interface class for translating materials into solver specific representations

    Parameters
    ----------
    openmc_material : openmc.Material
        The OpenMC Material object used to define this material
    mpact_build_specs : Optional[MPACTBuildSpecs]
        Specifications for building the MPACT material

    Attributes
    ----------
    mpact_build_specs : Union[MPACTBuildSpecs, None]
        Specifications for building the MPACT material
    openmc_material : openmc.Material
        The OpenMC Material object representing this material
    mpact_material : Union[mpactpy.material.Material, None]
        The MPACT Material object representing this material
    name : str
        The name for the material
    temperature : float
        The temperature of the material (K)
    density : float
        The density of the material (g/cc)
    number_densities : Dict[str, float]
        The isotopic number densities (atom/b-cm)
        Dictionary keys are nuclide names and values are number densities.
    """

    @dataclass
    class MPACTBuildSpecs():
        """ A dataclass for holding MPACT material building specifications

        Attributes
        ----------
        thermal_scattering_isotopes : List[str]
            List of isotopes that should use thermal scattering libraries
        is_fluid : bool
            Boolean flag indicating whether or not the material is a fluid
        is_depletable : bool
            Boolean flag indicating whether or not the material is depletable
        has_resonance : bool
            Boolean flag indicating whether or not the material has resonance data
        is_fuel : bool
            Boolean flag indicating whether or not the material is fuel
        """

        thermal_scattering_isotopes : List[str]
        is_fluid                    : bool
        is_depletable               : bool
        has_resonance               : bool
        is_fuel                     : bool

    @property
    def mpact_build_specs(self) -> Union[MPACTBuildSpecs, None]:
        return self._mpact_build_specs

    @mpact_build_specs.setter
    def mpact_build_specs(self, mpact_build_specs: Optional[MPACTBuildSpecs] = None) -> None:
        self._mpact_build_specs = mpact_build_specs
        if mpact_build_specs:
            self._mpact_material = mpactpy.material.Material.from_openmc_material(
                self.openmc_material,
                mpact_build_specs.thermal_scattering_isotopes,
                mpact_build_specs.is_fluid,
                mpact_build_specs.is_depletable,
                mpact_build_specs.has_resonance,
                mpact_build_specs.is_fuel
            )

    @property
    def openmc_material(self) -> openmc.Material:
        return self._openmc_material

    @property
    def mpact_material(self) -> mpactpy.material.Material:
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
                 mpact_build_specs: Optional[MPACTBuildSpecs] = None) -> None:

        self._openmc_material = openmc_material
        self.mpact_build_specs = mpact_build_specs

    def __eq__(self, other: Any) -> bool:
        """ Check that materials are the same
        """
        if self is other:
            return True
        return (isinstance(other, Material) and
                self.openmc_material.id == other.openmc_material.id)

    def __hash__(self) -> int:
        return hash(self.openmc_material)

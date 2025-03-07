from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

import openmc
import mpactpy.material

class MaterialFactory(ABC):
    """ An abstract class for OpenMC material factories

    Attributes
    ----------
    label : str
        The label of the material
    temperature : float
        Material temperature in Kelvin
    mpact_build_specs : MPACTBuildSpecs
        Specifications for building the MPACT material
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
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, label: str) -> None:
        self._label = label

    @property
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, temperature: float) -> None:
        assert temperature >= 0.0, f"temperature = {temperature}"
        self._temperature = temperature

    @property
    def mpact_build_specs(self) -> MPACTBuildSpecs:
        return self._mpact_build_specs

    @mpact_build_specs.setter
    def mpact_build_specs(self, mpact_build_specs: MPACTBuildSpecs) -> None:
        self._mpact_build_specs = mpact_build_specs

    @abstractmethod
    def make_openmc_material(self) -> openmc.Material:
        """ Method for building instances of an OpenMC Material

        Returns
        -------
        openmc.Material
            The OpenMC material that was made
        """

    def make_mpact_material(self) -> mpactpy.material.Material:
        """ Method for building instances of an MPACT Material

        Returns
        -------
        mpactpy.Material
            The MPACT material that was made
        """

        return mpactpy.material.Material.from_openmc_material(self.make_openmc_material(),
                                                              self.mpact_build_specs.thermal_scattering_isotopes,
                                                              self.mpact_build_specs.is_fluid,
                                                              self.mpact_build_specs.is_depletable,
                                                              self.mpact_build_specs.has_resonance,
                                                              self.mpact_build_specs.is_fuel)

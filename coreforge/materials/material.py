from abc import ABC
from typing import Dict, Any, Iterable, List, Tuple
from math import isclose

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.serialization import Serializable

STANDARD_TEMPERATURE = 273.15
ROOM_TEMPERATURE     = 293.6

class Material(ABC, Serializable):
    """ An interface class for translating materials into solver specific representations

    Parameters
    ----------
    openmc_material : openmc.Material
        The OpenMC Material object used to define this material

    Attributes
    ----------
    openmc_material : openmc.Material
        The OpenMC Material object representing this material
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
    def openmc_material(self) -> openmc.Material:
        return self._openmc_material

    @property
    def thermal_scattering(self) -> Tuple[str, ...]:
        """ The thermal scattering law names this material uses

        Declared by the subclass rather than read back out of the OpenMC
        object, so a consumer can ask for it without depending on OpenMC's
        internal representation. Materials with no bound-atom treatment return
        an empty tuple.

        Returns
        -------
        Tuple[str, ...]
            S(alpha,beta) table names, e.g. ``('c_H_in_ZrH', 'c_Zr_in_ZrH')``
        """
        return ()

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


    def __init__(self, openmc_material: openmc.Material) -> None:

        self._openmc_material             = openmc_material.clone()
        self._openmc_material.temperature = self.temperature if self.temperature is not None else ROOM_TEMPERATURE


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


    # ---- serialization -----------------------------------------------------
    #
    # Materials store their *recipe*, not their resolved composition. The class
    # is load-bearing: mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS is keyed by
    # type, so a material rebuilt as a plain Material would compare equal and
    # still render to MPACT without its thermal scattering specs.
    #
    # Twelve of the thirteen concrete materials share the signature
    # (name, temperature, density), all recoverable from properties, so the base
    # handles them. Graphite takes a required graphite_density plus extras and
    # overrides both methods.

    def _serial_state(self, intern):
        return {"name":        self.name,
                "temperature": self.temperature,
                "density":     self.density}

    @classmethod
    def _from_serial_state(cls, state, resolve):
        """ Rebuild a material from the recipe the base implementation stores

            A template method: it is never valid on ``Material`` itself, whose
            constructor takes an ``openmc.Material``. It is valid on any
            subclass whose constructor is ``(name, temperature, density)``,
            which is sixteen of the eighteen concrete materials. ``Graphite``
            and ``msre.Salt`` are recipes with more arguments and override both
            halves in their own modules.

            pylint reads ``cls`` as ``Material`` here and objects to the call
            signature. It is right about the base class and wrong about every
            class this actually runs on; the constraint is stated above rather
            than encoded, because encoding it would mean an abstract
            declaration on a mixin that most subclasses would then have to
            restate.
        """
        # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
        return cls(name        = state["name"],
                   temperature = state["temperature"],
                   density     = state["density"])


def unique_materials(materials: Iterable["Material"]) -> List["Material"]:
    """Return a list of unique materials, preserving the first-seen order.

    Parameters
    ----------
    materials : Iterable[Material]
        Materials to de-duplicate.

    Returns
    -------
    List[Material]
        Unique materials by name, preserving first-seen order.

    Raises
    ------
    ValueError
        If two materials share a name but differ in composition.
    """
    unique: List[Material] = []
    seen_by_name: Dict[str, Material] = {}
    for material in materials:
        seen_material = seen_by_name.get(material.name)
        if seen_material is None:
            seen_by_name[material.name] = material
            unique.append(material)
            continue
        if seen_material != material:
            raise ValueError(
                f"Materials named '{material.name}' must be equal to be treated as duplicates."
            )
    return unique

""" Code-agnostic composition records, and the catalogue CoreForge publishes

A :class:`Composition` is what a material *is*, stated without reference to any
physics code: a density, a temperature, isotopic number densities keyed by
nuclide name, and the thermal scattering laws that apply. It is a plain record,
so a consumer can read CoreForge's curated compositions without holding an
OpenMC object, and without CoreForge having to guess what representation that
consumer wants.

:func:`compositions` is the published entry point. Downstream catalogues call it
to import CoreForge's compositions as authoritative rather than maintaining a
second copy — two definitions of the same fuel is how a reactivity discrepancy
gets discovered a year late.

Materials that have no single canonical composition are deliberately absent. See
:func:`compositions` for which, and why.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from coreforge.materials import (Air, Al6061T6, B4C, Helium, INOR8, Inconel,
                                 Material, Mo, SS304, SS316H, UZrH, Water, Zr)


@dataclass(frozen=True)
class Composition:
    """ A material stated independently of any physics code

    Attributes
    ----------
    name : str
        The material's name
    density : float
        Mass density (g/cm3)
    temperature : float
        Temperature (K)
    number_densities : Dict[str, float]
        Isotopic number densities (atom/b-cm), keyed by nuclide name
        (e.g. ``'U235'``)
    thermal_scattering : Tuple[str, ...]
        S(alpha,beta) table names that apply to this material. Empty when the
        material has no bound-atom treatment. A tuple rather than a single
        value because materials such as U-ZrH need more than one.
    source_class : str
        The CoreForge class this came from, so a consumer can trace a
        composition back to the code and citation that produced it
    """

    name:               str
    density:            float
    temperature:        float
    number_densities:   Dict[str, float]
    thermal_scattering: Tuple[str, ...]
    source_class:       str


def from_material(material: Material) -> Composition:
    """ Build a code-agnostic record from a CoreForge material

    Parameters
    ----------
    material : Material
        The material to describe

    Returns
    -------
    Composition
        The code-agnostic record
    """
    return Composition(name               = material.name,
                       density            = material.density,
                       temperature        = material.temperature,
                       number_densities   = dict(material.number_densities),
                       thermal_scattering = tuple(material.thermal_scattering),
                       source_class       = type(material).__name__)


#: Names of the materials with a single canonical definition, constructible from
#: their own documented defaults. ``Graphite`` is deliberately absent: it
#: requires a density per application (NETL graphite and MSRE graphite differ in
#: density, boron-equivalent contamination and pore intrusion), so there is no
#: one composition to publish, and inventing a default would be worse than the
#: omission.
CANONICAL_MATERIALS = (Air, Al6061T6, B4C, Helium, INOR8, Inconel,
                       Mo, SS304, SS316H, UZrH, Water, Zr)


def compositions() -> List[Composition]:
    """ CoreForge's curated compositions, as code-agnostic records

    This is the published interface for downstream consumers. It returns only
    materials with a single canonical definition; parameterised materials such
    as graphite are excluded because they have no one composition to publish.

    Returns
    -------
    List[Composition]
        One record per canonical material, in a stable order
    """
    return [from_material(material_cls()) for material_cls in CANONICAL_MATERIALS]

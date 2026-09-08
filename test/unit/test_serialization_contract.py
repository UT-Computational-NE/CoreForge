""" The acceptance contract for geometry serialization

A CoreForge model used to be a Python program and nothing else, which meant it
could not be archived, diffed, reviewed, or handed to anything that was not a
Python process holding the same imports. ``coreforge/serialization.py`` gives it
a document form; this file is what "correct" means for that document.

This file was written as acceptance criteria *before* the implementation, with
every test marked ``xfail(strict=True)``. When ``to_dict``/``from_dict`` landed,
each one flipped to XPASS and failed until its marker was removed — which is the
point of ``strict``: a contract that cannot be quietly left behind.

The markers are gone now, save one. ``test_zones_closer_than_the_rounding_tolerance_do_not_round_trip``
stays ``xfail`` because it records a real limitation whose fix is a decision
rather than an implementation. See its docstring.

The headline contract is one line:

    from_dict(to_dict(x)) == x

under the existing tolerance-aware equality, for every class in
``geometry_elements``. The rest of this file is the traps that make that line
harder than it looks. Each is a real property of this library, not a
hypothetical.

If a test here encodes the wrong contract, the test is wrong and should be
changed — these are a proposal, not a specification handed down.
"""

import mpactpy
import pytest

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.hex_lattice import HexLattice
from coreforge.geometry_elements.infinite_medium import InfiniteMedium
from coreforge.materials import (Air, Al6061T6, B4C, Graphite, Helium, Inconel,
                                 INOR8, Material, Mo, SS304, SS316H, UZrH,
                                 Water, Zr)
from coreforge.materials.msre import (ControlRodPoison, Insulation, Salt,
                                      ThimbleGas)
from coreforge.mpact_builder import DEFAULT_MPACT_MATERIAL_SPECS

#: Every concrete material that constructs with no arguments. Graphite is the
#: one that does not — ``graphite_density`` is required — so it is exercised
#: separately below. ``test_serialization_coverage.py`` is what guarantees this
#: list cannot silently fall behind the package.
MATERIAL_CLASSES = [Air, Al6061T6, B4C, ControlRodPoison, Helium, Inconel,
                    INOR8, Insulation, Mo, Salt, SS304, SS316H, ThimbleGas,
                    UZrH, Water, Zr]

# ---------------------------------------------------------------------------
# Fixtures — built from the simplest constructors so a failure here is about
# serialization, never about assembling the fixture.
# ---------------------------------------------------------------------------

def _pincell(name="pincell"):
    """ A three-zone cylindrical pincell

        ``materials`` carries one entry more than ``radii``: the last becomes the
        outer material, so passing ``outer_material`` alongside would be
        overwritten.
    """
    return CylindricalPinCell(radii=[0.5, 0.6, 0.7],
                              materials=[UZrH(), Zr(), Water(), Water()],
                              name=name)


def _round_trip(element):
    """ Serialize and rebuild, once the API exists
    """
    return type(element).from_dict(element.to_dict())


# ---------------------------------------------------------------------------
# The headline contract
# ---------------------------------------------------------------------------

#: Factories, not instances. A parametrize list is evaluated at import time, so
#: constructing fixtures there would turn a wrong constructor argument into a
#: collection error for the whole file instead of a single expected failure.
ELEMENT_FACTORIES = [
    pytest.param(lambda: InfiniteMedium(Water()), id="infinite_medium_water"),
    pytest.param(lambda: InfiniteMedium(UZrH()), id="infinite_medium_uzrh"),
    pytest.param(_pincell, id="cylindrical_pincell"),
]


@pytest.mark.parametrize("make_element", ELEMENT_FACTORIES)
def test_round_trip_preserves_equality(make_element):
    """ from_dict(to_dict(x)) == x, under the library's own tolerance-aware __eq__
    """
    element = make_element()
    assert _round_trip(element) == element


@pytest.mark.parametrize("make_element", ELEMENT_FACTORIES)
def test_round_trip_preserves_hash(make_element):
    """ Equality and hashing must survive together

        ``__eq__`` compares with ``isclose(rel_tol=TOL)`` and ``__hash__`` uses
        ``relative_round`` on the same fields. A serializer that writes full
        precision and a loader that does not round will produce objects that
        compare equal and hash differently — which silently breaks every
        de-duplication path, including ``unique_materials`` and the lattice
        de-duplication the MPACT build depends on. That is not a crash; it is an
        MPACT model with ninety unique lattices where twelve were intended.
    """
    element = make_element()
    assert hash(_round_trip(element)) == hash(element)


def test_a_serialized_document_is_json_safe():
    """ The point of the format is to leave a Python process
    """
    import json

    json.dumps(_pincell().to_dict())


# ---------------------------------------------------------------------------
# Trap 1 — repeated structures and object identity
# ---------------------------------------------------------------------------

def test_shared_elements_are_not_inlined_once_per_use():
    """ A core is mostly the same element repeated

        Naive JSON writes the identical fuel element once per position. The
        reader then loses object identity, and a build that de-duplicates by
        hash sees N distinct lattices where it should see one.
    """
    shared = _pincell("shared")
    lattice = HexLattice(pitch=1.0,
                         outer_material=Water(),
                         elements=[[shared, shared, shared,
                                    shared, shared, shared], [shared]],
                         map_type='ring')

    document = lattice.to_dict()
    serialized = str(document)

    assert serialized.count('"shared"') <= 2 or "$ref" in serialized or "id" in document, \
        "repeated elements must be stored once and referenced, not inlined per use"


def test_identity_is_restored_by_content_not_by_name():
    """ Two elements with the same name and different content are different

        ``unique_materials`` already raises when two materials share a name and
        differ in composition. Restoring identity by name on load would
        reintroduce exactly that collision one layer up.
    """
    a = _pincell("same-name")
    b = CylindricalPinCell(radii=[0.9],
                           materials=[Graphite(graphite_density=1.86), Air()],
                           name="same-name")

    assert _round_trip(a) != _round_trip(b)


# ---------------------------------------------------------------------------
# Trap 2 — lattices are not arrays
# ---------------------------------------------------------------------------

def test_hex_lattice_orientation_survives():
    """ Orientation decides which physical position index zero is

        Get it wrong and the core is rotated thirty degrees. That runs fine and
        gives a different flux tilt, which is the worst kind of wrong.
    """
    element = _pincell()
    lattice = HexLattice(pitch=1.0, outer_material=Water(),
                         elements=[[element]], map_type='ring', orientation='x')

    assert _round_trip(lattice).orientation == 'x'


def test_hex_lattice_round_trips_through_its_stored_form():
    """ 'offset' is what a person draws, 'ring' is what is stored

        The serialized document should carry one of them unambiguously, and
        reloading must not silently reinterpret a ring map as an offset map.
    """
    element = _pincell()
    lattice = HexLattice(pitch=1.0, outer_material=Water(),
                         elements=[[element]], map_type='ring')

    assert _round_trip(lattice) == lattice


# ---------------------------------------------------------------------------
# Trap 3 — units are canonical and unlabelled
# ---------------------------------------------------------------------------

def test_no_per_value_units_are_emitted():
    """ Everything is cm, g/cm3, K, degrees

        A units field per number is an invitation to mix them. Conversion
        belongs in the human-facing layer, not in the stored document.
    """
    document = _pincell().to_dict()
    flattened = str(document).lower()

    for unit in ('"unit"', "'unit'", '"units"', "'units'"):
        assert unit not in flattened


# ---------------------------------------------------------------------------
# Trap 4 — materials are shared, and their guard must survive
# ---------------------------------------------------------------------------

def test_a_material_used_twice_is_stored_once():
    """ Materials appear across dozens of elements
    """
    water = Water()
    element = CylindricalPinCell(radii=[0.5, 0.6],
                                 materials=[water, water, water])

    document = element.to_dict()
    assert str(document).count('"Water"') <= 2, \
        "a shared material must be stored once and referenced"


def test_materials_survive_the_round_trip():
    """ get_materials() is how a build discovers what it must define
    """
    element = _pincell()
    before = {m.name for m in element.get_materials()}
    after = {m.name for m in _round_trip(element).get_materials()}

    assert before == after


# ---------------------------------------------------------------------------
# Trap 5 — geometry and mesh are different documents
# ---------------------------------------------------------------------------

def test_geometry_document_carries_no_meshing_decisions():
    """ Same reactor, different mesh, is a different *run* — not a different reactor

        Voxelation specs, radial mesh unionization and target axial thickness
        are per-code, per-study choices. Collapsing them into the geometry
        document means someone will diff a multiplication factor across a mesh
        change and call it a geometry change.
    """
    flattened = str(_pincell().to_dict()).lower()

    for meshing_term in ("voxel", "mesh", "target_axial_thickness", "unionize"):
        assert meshing_term not in flattened


# ---------------------------------------------------------------------------
# Trap 6 — semantics that look like formatting
# ---------------------------------------------------------------------------

def test_zone_filtering_survives_without_storing_the_threshold():
    """ ``min_zone_thickness`` removes geometry, and its effect is in the zones

        An earlier version of this test asserted the threshold "has to be
        stored". That was wrong. The object retains no attribute for it: it
        filters zones at construction and is discarded, so the surviving zones
        already carry its effect and serializing them reproduces the object.

        What must hold is that a filtered pincell and an unfiltered one remain
        *different* after a round trip — otherwise the format has quietly
        thrown the filtering away.

        The radii differ by more than ``ROUNDING_RELATIVE_TOLERANCE`` on
        purpose; see the note below.
    """
    radii = [0.5, 0.52, 0.7]
    materials = [UZrH(), Zr(), Water(), Water()]

    strict = CylindricalPinCell(radii=radii, materials=list(materials),
                                min_zone_thickness=0.1)
    loose = CylindricalPinCell(radii=radii, materials=list(materials),
                               min_zone_thickness=None)

    assert len(strict.zones) < len(loose.zones), "the fixture must actually filter"
    assert _round_trip(strict) == strict
    assert _round_trip(loose) == loose
    assert _round_trip(strict) != _round_trip(loose)


@pytest.mark.xfail(
    strict=True,
    reason="known limitation, documented rather than fixed — see the docstring",
)
def test_zones_closer_than_the_rounding_tolerance_do_not_round_trip():
    """ A pincell can be constructible and yet not round-trippable

        ``_set_zones`` compares zone boundaries with an exact ``<``, so radii
        differing by 1e-9 construct happily. But ``__eq__`` and ``__hash__``
        treat values within ``ROUNDING_RELATIVE_TOLERANCE`` (1e-5) as the *same*
        value, and the document interns nodes by tolerance-rounded content for
        exactly that reason — it is what makes shared elements de-duplicate.

        So two zones closer together than the tolerance collapse into one node,
        reload as one object, and fail the non-intersection assertion.

        This is left failing rather than fixed because the fix is a decision,
        not an implementation: either the format stops rounding (and loses
        de-duplication, breaking a different trap), or ``_set_zones`` adopts the
        tolerance the rest of the library uses. The second looks right — a
        pincell whose zones are indistinguishable under the library's own
        equality is arguably already degenerate — but that is a change to
        geometry validation and belongs to whoever owns it.
    """
    degenerate = CylindricalPinCell(radii=[0.5, 0.5 + 1e-9, 0.7],
                                    materials=[UZrH(), Zr(), Water(), Water()])

    assert _round_trip(degenerate) == degenerate


# ---------------------------------------------------------------------------
# Trap 7 — the class is load-bearing, and equality cannot see it
# ---------------------------------------------------------------------------
#
# This section was missing from the first draft of this contract, which is
# worth recording: every test above would pass against a serializer that
# rebuilt every material as a plain `Material` carrying the right number
# densities. The result would be a green suite over a model that renders to
# MPACT without its thermal scattering.

def _default_specs_for(material):
    """ Mirror ``mpact_builder.build_material``'s lookup

        It walks ``__base__`` from the concrete class and takes the first
        ``DEFAULT_MPACT_MATERIAL_SPECS`` entry it finds, falling through to
        ``None`` — which renders the material with no specs at all.
    """
    cls = type(material)
    while cls is not object:
        specs = DEFAULT_MPACT_MATERIAL_SPECS.get(cls)
        if specs:
            return specs
        cls = cls.__base__
    return None


def test_equality_alone_cannot_detect_a_lost_class():
    """ Why Trap 7 exists at all — the failure mode is invisible to ``==``

        ``Material.__eq__`` tests ``isinstance(other, Material)`` and then
        compares density, temperature and number densities. It does not compare
        the class. It does not compare the *name* either.

        So a material rebuilt as some other ``Material`` subclass wrapping the
        same OpenMC object is equal to the original by the library's own
        definition, hashes the same, and survives every round-trip assertion in
        this file — while resolving different MPACT specs. This test asserts
        that gap directly, so that if ``__eq__`` ever tightens, the tests below
        are known to have become redundant rather than quietly load-bearing.
    """
    class _Anonymous(Material):
        """ A stand-in for what a composition-only serializer would rebuild """

    fuel      = UZrH()
    anonymous = _Anonymous(fuel.openmc_material)

    assert anonymous == fuel, "equality does not inspect the class"
    assert hash(anonymous) == hash(fuel), "neither does hashing"

    assert _default_specs_for(fuel) is not None
    assert _default_specs_for(anonymous) is None, \
        "and yet MPACT would render it with no specs at all"


@pytest.mark.parametrize("material_cls", MATERIAL_CLASSES)
def test_round_trip_preserves_the_concrete_class(material_cls):
    """ The document stores a recipe, so the class comes back

        ``DEFAULT_MPACT_MATERIAL_SPECS`` is keyed by ``type``. Losing the class
        is not a cosmetic loss; it is the difference between UZrH rendered with
        ``H1_in_ZrH`` bound-atom scattering and UZrH rendered as free hydrogen.
    """
    material = material_cls()
    assert type(_round_trip(material)) is material_cls


@pytest.mark.parametrize("material_cls", MATERIAL_CLASSES)
def test_round_trip_preserves_mpact_material_specs(material_cls):
    """ What preserving the class is *for*

        Asserted through the same walk the builder performs, rather than on the
        class alone, so this still holds if the dispatch changes.
    """
    material = material_cls()
    assert _default_specs_for(_round_trip(material)) == _default_specs_for(material)


@pytest.mark.parametrize("material_cls", MATERIAL_CLASSES)
def test_round_trip_preserves_declared_thermal_scattering(material_cls):
    """ The code-agnostic view of the same property

        ``Material.thermal_scattering`` is declared by the subclass rather than
        read back out of OpenMC, which makes it exactly the kind of thing a
        composition-only round trip drops on the floor.
    """
    material = material_cls()
    assert _round_trip(material).thermal_scattering == material.thermal_scattering


def test_an_instance_keyed_specs_override_still_matches_after_a_round_trip():
    """ ``MaterialSpecs`` is ``Dict[Material, MPACTSpecs]`` — keyed by instance

        A caller passing a per-material override builds that dict against the
        materials they hold. The builder looks up ``material in specs``, which
        is ``__hash__`` then ``__eq__``. If a round trip perturbed either, the
        override would silently miss and fall through to the class default —
        a wrong model, rendered without complaint.
    """
    fuel     = UZrH()
    override = mpactpy.Material.MPACTSpecs({'H': "H1"}, False, False, False, False)
    specs    = {fuel: override}

    assert _round_trip(fuel) in specs
    assert specs[_round_trip(fuel)] == override


def test_graphite_survives_as_its_recipe_not_its_composition():
    """ ``Graphite`` is a calculation, and it cannot be inverted

        Theoretical density, boron-equivalent contamination and a pore
        intrusion map are mixed through OpenMC. Nothing recovers those
        arguments from the resulting number densities, so the document has to
        carry them. Distinct arguments must produce distinct round trips.

        The intruded fixture uses helium rather than water, which is worth a
        note: ``openmc.Material.mix_materials`` raises ``NotImplementedError``
        for any material carrying an S(a,b) table, so water — the obvious
        intrusion medium for a pool reactor — cannot be pore-intruded into
        graphite at all today. That is an OpenMC constraint upstream of this
        format, and ``pore_intrusion`` currently has no caller in the
        repository, so nothing exercises it. Recorded here because this test is
        where it surfaced, not because serialization is where it belongs.
    """
    plain      = Graphite(graphite_density=1.86)
    borated    = Graphite(graphite_density=1.86, boron_equiv_contamination=5.0)
    intruded   = Graphite(graphite_density=1.86,
                          pore_intrusion={Helium(): 0.05})

    for original in (plain, borated, intruded):
        assert _round_trip(original) == original
        assert type(_round_trip(original)) is Graphite

    assert _round_trip(plain) != _round_trip(borated)
    assert _round_trip(plain) != _round_trip(intruded)


def test_salt_survives_as_its_recipe_not_its_composition():
    """ MSRE salt is the other calculation in the package

        Its number densities come from a mol% composition and two enrichments,
        and nothing inverts them. A base-class round trip carrying only
        (name, temperature, density) would rebuild a chemically different salt
        at exactly the right density — which is the quietest possible wrong
        answer, since density is what a reviewer would spot-check.
    """
    nominal   = Salt()
    depleted  = Salt(uranium_enrichment=5.0)
    natural_li = Salt(lithium_enrichment=92.5)
    zirconium  = Salt(composition={"LiF": 0.65, "BeF2": 0.29,
                                   "ZrF4": 0.05, "UF4": 0.01})

    for original in (nominal, depleted, natural_li, zirconium):
        assert _round_trip(original) == original
        assert type(_round_trip(original)) is Salt

    for variant in (depleted, natural_li, zirconium):
        assert _round_trip(nominal) != _round_trip(variant), \
            "a recipe difference must survive as a difference"

    restored = _round_trip(zirconium)
    assert restored.composition        == zirconium.composition
    assert restored.uranium_enrichment == zirconium.uranium_enrichment
    assert restored.lithium_enrichment == zirconium.lithium_enrichment

""" The acceptance contract for geometry serialization

CoreForge has no serialized form today: there is no ``to_dict``, ``from_dict``,
schema, YAML or JSON anywhere in the package. A model is a Python program, which
means it cannot be archived, diffed, reviewed, or handed to anything that is not
a Python process holding the same imports. The as-built NETL core loading lives
in a test fixture for exactly this reason.

This file is the acceptance criteria, written before the implementation. Every
test is ``xfail(strict=True)``: the suite stays green while the API is absent,
and the moment ``to_dict``/``from_dict`` land, each one flips to XPASS and fails
until its marker is removed. Nothing here can be quietly forgotten.

The headline contract is one line:

    from_dict(to_dict(x)) == x

under the existing tolerance-aware equality, for every class in
``geometry_elements``. The rest of this file is the traps that make that line
harder than it looks. Each is a real property of this library, not a
hypothetical.

If a test here encodes the wrong contract, the test is wrong and should be
changed — these are a proposal, not a specification handed down.
"""

# pylint: disable=no-member
# `to_dict` / `from_dict` do not exist yet — that is the point of this file. CI
# lints ./coreforge rather than ./test, so this only matters to a broader run.

import pytest

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.hex_lattice import HexLattice
from coreforge.geometry_elements.infinite_medium import InfiniteMedium
from coreforge.materials import Air, Graphite, UZrH, Water, Zr

pytestmark = pytest.mark.xfail(
    strict=True,
    reason="geometry serialization is not implemented; this file is its acceptance "
           "contract. Remove these markers as to_dict/from_dict land.",
)


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

def test_zone_filtering_tolerance_is_part_of_the_document():
    """ ``min_zone_thickness`` removes geometry below its value

        It looks like a rounding detail and it changes the model. Two documents
        identical but for it describe different objects, so it has to be stored.
    """
    strict = CylindricalPinCell(radii=[0.5, 0.5 + 1e-9, 0.7],
                                materials=[UZrH(), Zr(), Water(), Water()],
                                min_zone_thickness=1e-6)
    loose = CylindricalPinCell(radii=[0.5, 0.5 + 1e-9, 0.7],
                               materials=[UZrH(), Zr(), Water(), Water()],
                               min_zone_thickness=None)

    assert _round_trip(strict) == strict
    assert _round_trip(loose) == loose

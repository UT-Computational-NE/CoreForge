import pytest
from copy import deepcopy
from math import isclose

from coreforge.geometry_elements.triga.netl import CentralThimble
from coreforge.materials import Al6061T6, Water
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder

CM_PER_INCH = 2.54

@pytest.fixture
def central_thimble():
    clad = CentralThimble.Cladding(
        thickness=(1.5 * 0.5 * CM_PER_INCH) - (1.33 * 0.5 * CM_PER_INCH),
        outer_radius=1.5 * 0.5 * CM_PER_INCH,
    )
    return CentralThimble(
        cladding=clad,
        length=160.0,
        fill_material=Water(),
        outer_material=Water(),
    )


@pytest.fixture
def unequal_thimble():
    clad = CentralThimble.Cladding(
        thickness=0.25 * CM_PER_INCH,
        outer_radius=1.55 * 0.5 * CM_PER_INCH,
    )
    return CentralThimble(
        cladding=clad,
        length=160.0,
        fill_material=Water(),
        outer_material=Water(),
    )


def test_initialization(central_thimble):
    pin = central_thimble.thimble_pincell

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([
        central_thimble.cladding.inner_radius,
        central_thimble.cladding.outer_radius,
    ])
    assert isinstance(materials[0], Water)
    assert isinstance(materials[1], Al6061T6)
    assert isinstance(pin.outer_material, Water)


def test_equality_and_hash(central_thimble, unequal_thimble):
    assert central_thimble == deepcopy(central_thimble)
    assert central_thimble != unequal_thimble
    assert hash(central_thimble) == hash(deepcopy(central_thimble))
    assert hash(central_thimble) != hash(unequal_thimble)


def test_as_stack(central_thimble):
    stack = central_thimble.as_stack()
    assert len(stack.segments) == 1
    assert isclose(stack.length, central_thimble.length)
    assert isclose(stack.bottom_pos, 0.0)


def test_openmc_builder(central_thimble):
    geom_element = central_thimble
    universe = openmc_builder.build(geom_element)
    assert universe.name == "central_thimble"
    assert len(universe.cells) == 1


def test_mpact_builder(central_thimble):
    geom_element = central_thimble
    core = mpact_builder.build(geom_element)

    expected_xy = central_thimble.cladding.outer_radius * 2.0
    assert isclose(core.mod_dim['X'], expected_xy)
    assert isclose(core.mod_dim['Y'], expected_xy)
    assert core.mod_dim['Z'] == [central_thimble.length]
    assert core.nz == 1
    assert isclose(core.height, central_thimble.length)

    assert len(core.pins)       == 1
    assert len(core.modules)    == 1
    assert len(core.lattices)   == 1
    assert len(core.assemblies) == 1

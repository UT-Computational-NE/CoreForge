import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose
from mpactpy import RectangularPinMesh, Pin

from coreforge.geometry_elements import InfiniteMedium
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from test.unit.test_materials import air, graphite

@pytest.fixture
def infinite_medium(air):
    return InfiniteMedium(material=air)

@pytest.fixture
def unequal_infinite_medium(graphite):
    return InfiniteMedium(material=graphite)

@pytest.fixture
def infinite_medium_mpact_specs():
    return mpact_builder.InfiniteMedium.Specs(thicknesses = {"X": 8.0, "Y": 8.0})

def test_initialization(infinite_medium):
    geom_element = infinite_medium
    assert geom_element.name == "infinite_medium"
    assert geom_element.material.name == "Air"

def test_equality(infinite_medium, unequal_infinite_medium):
    assert infinite_medium == deepcopy(infinite_medium)
    assert infinite_medium != unequal_infinite_medium

def test_hash(infinite_medium, unequal_infinite_medium):
    assert hash(infinite_medium) == hash(deepcopy(infinite_medium))
    assert hash(infinite_medium) != hash(unequal_infinite_medium)

def test_openmc_builder(infinite_medium):
    geom_element = infinite_medium
    universe = openmc_builder.build(geom_element)
    assert universe.name == "infinite_medium"
    assert len(universe.cells) == 1
    cell = next(iter(universe.cells.values()))
    assert cell.fill.name == "Air"
    assert cell.region is None

def test_mpact_builder(infinite_medium, infinite_medium_mpact_specs, air):

    geom_element = infinite_medium
    specs        = infinite_medium_mpact_specs
    core         = mpact_builder.build(geom_element, specs)
    air          = mpact_builder.build_material(air)

    assert len(core.materials) == 1
    assert air in core.materials

    assert isclose(core.mod_dim['X'], 8.0)
    assert isclose(core.mod_dim['Y'], 8.0)
    assert_allclose(core.mod_dim['Z'], [1.0])

    assert len(core.pins)       == 1
    assert len(core.modules)    == 1
    assert len(core.lattices)   == 1
    assert len(core.assemblies) == 1

    expected_xvals = [8.0]
    expected_yvals = [8.0]
    expected_mats  = [air]

    assert core.pins[0] == Pin(RectangularPinMesh(expected_xvals, expected_yvals, [1.0], [1], [1], [1]), expected_mats)

    specs.divide_into_quadrants = True
    core = mpact_builder.build(geom_element, specs)

    assert isclose(core.mod_dim['X'], 4.0)
    assert isclose(core.mod_dim['Y'], 4.0)
    assert core.lattices[0].nx == 2
    assert core.lattices[0].ny == 2

    pin = {"NW" : core.lattices[0].module_map[0][0].pin_map[0][0],
           "NE" : core.lattices[0].module_map[0][1].pin_map[0][0],
           "SW" : core.lattices[0].module_map[1][0].pin_map[0][0],
           "SE" : core.lattices[0].module_map[1][1].pin_map[0][0]}

    expected_xvals = [4.0]
    expected_yvals = [4.0]

    assert pin["NW"] == Pin(RectangularPinMesh(expected_xvals, expected_yvals, [1.0], [1], [1], [1]), expected_mats)
    assert pin["NE"] == Pin(RectangularPinMesh(expected_xvals, expected_yvals, [1.0], [1], [1], [1]), expected_mats)
    assert pin["SW"] == Pin(RectangularPinMesh(expected_xvals, expected_yvals, [1.0], [1], [1], [1]), expected_mats)
    assert pin["SE"] == Pin(RectangularPinMesh(expected_xvals, expected_yvals, [1.0], [1], [1], [1]), expected_mats)

import pytest
from copy import deepcopy

from coreforge.geometry_elements import InfiniteMedium
from test.unit.test_materials import air, graphite

@pytest.fixture
def infinite_medium(air):
    return InfiniteMedium(material=air)

@pytest.fixture
def unequal_infinite_medium(graphite):
    return InfiniteMedium(material=graphite)

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

def test_make_openmc_universe(infinite_medium):
    geom_element = infinite_medium
    universe = geom_element.make_openmc_universe()
    assert universe.name == "infinite_medium"
    assert len(universe.cells) == 1
    cell = universe.cells[1]
    assert cell.fill.name == "Air"
    assert cell.region is None

def test_make_mpact_core(infinite_medium):
    geom_element = infinite_medium
    with pytest.raises(NotImplementedError,
        match="Cannot make an MPACT Core for InfiniteMedium infinite_medium."):
        core = geom_element.make_mpact_core()
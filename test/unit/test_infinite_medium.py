import pytest
from copy import deepcopy

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

def test_mpact_builder(infinite_medium):
    geom_element = infinite_medium
    with pytest.raises(NotImplementedError,
        match="No MPACT builder registered for InfiniteMedium infinite_medium"):
        core = mpact_builder.build(geom_element)

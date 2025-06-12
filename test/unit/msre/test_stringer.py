import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose

from coreforge.geometry_elements.msre import Stringer, Block
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from test.unit.msre.test_block import block, stadium_fuel_chan, control_chan
from test.unit.test_materials import graphite
from test.unit.msre.test_materials import salt

@pytest.fixture
def stringer(block):
    return Stringer(block, length = 170)

@pytest.fixture
def unequal_stringer(block):
    return Stringer(block, length = 160.0)

@pytest.fixture
def stringer_mpact_specs():
    return mpact_builder.msre.Stringer.Specs()



def test_stringer_initialization(stringer, block):
    geom_element = stringer
    assert geom_element.name == "stringer"
    assert geom_element.block == block
    assert isclose(geom_element.length, stringer.length)

def test_equality(stringer, unequal_stringer):
    assert stringer == deepcopy(stringer)
    assert stringer != unequal_stringer

def test_hash(stringer, unequal_stringer):
    assert hash(stringer) == hash(deepcopy(stringer))
    assert hash(stringer) != hash(unequal_stringer)

def test_as_stack(stringer):
    stack = stringer.as_stack()
    assert len(stack.segments) == 1
    assert isclose(stack.length, stringer.length)
    assert isclose(stack.bottom_pos, 0.0)

def test_openmc_builder(stringer):
    geom_element = stringer
    universe = openmc_builder.build(geom_element)
    assert universe.name == "stringer"
    assert len(universe.cells) == 1
    for cell in universe.cells.values():
        assert cell.fill.name == "msre_block"

def test_mpact_builder(stringer, stringer_mpact_specs, block):
    geom_element  = stringer
    core          = mpact_builder.build(geom_element, stringer_mpact_specs)

    assert isclose(core.mod_dim['X'], block.pitch)
    assert isclose(core.mod_dim['Y'], block.pitch)
    assert_allclose(core.mod_dim['Z'], [stringer.length])
    assert core.nz == 1
    assert isclose(core.height, stringer.length)

    assert len(core.pins)       == 18
    assert len(core.modules)    == 1
    assert len(core.lattices)   == 1
    assert len(core.assemblies) == 1

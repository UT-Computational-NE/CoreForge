import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose

from coreforge.geometry_elements.msre import ControlChannel, Block
from coreforge.mpact_builder import CylindricalPinCell as PinCell
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from test.unit.msre.test_block import block, stadium_fuel_chan, control_chan
from test.unit.test_materials import inconel, graphite
from test.unit.msre.test_materials import salt, thimble_gas, control_rod_poison



cr_chan_length    = 170.0
thimble_length    = 150.0
thimble_or        = 2.5
thimble_thickness = 0.2
thimble_length    = 165.0
cr_radii          = [1.0]
cr_insertion      = 0.5

@pytest.fixture
def thimble(inconel, thimble_gas):
    return ControlChannel.Thimble(outer_radius  = thimble_or,
                                  thickness     = thimble_thickness,
                                  length        = thimble_length,
                                  wall_material = inconel,
                                  fill_material = thimble_gas)

@pytest.fixture
def control_rod(control_rod_poison):
    return ControlChannel.ControlRod(radii              = cr_radii,
                                     materials          = [control_rod_poison],
                                     insertion_fraction = cr_insertion)

@pytest.fixture
def control_channel(thimble, control_rod, salt):
    return ControlChannel(length        = cr_chan_length,
                          fill_material = salt,
                          thimble       = thimble,
                          control_rod   = control_rod)

@pytest.fixture
def unequal_control_channel(thimble, control_rod, salt):
    return ControlChannel(length        = cr_chan_length*0.98,
                          fill_material = salt,
                          thimble       = thimble,
                          control_rod   = control_rod)

@pytest.fixture
def control_channel_mpact_specs(block):
    hp = block.pitch * 0.5
    return mpact_builder.msre.ControlChannel.Specs(PinCell.Specs(bounds=(-hp, hp, -hp, hp)))



def test_control_channel_initialization(control_channel, salt, thimble, control_rod):
    geom_element = control_channel
    assert geom_element.name == "control_channel"
    assert isclose(geom_element.length, cr_chan_length)
    geom_element == salt
    geom_element == thimble
    geom_element == control_rod

def test_equality(control_channel, unequal_control_channel):
    assert control_channel == deepcopy(control_channel)
    assert control_channel != unequal_control_channel

def test_hash(control_channel, unequal_control_channel):
    assert hash(control_channel) == hash(deepcopy(control_channel))
    assert hash(control_channel) != hash(unequal_control_channel)

def test_as_stack(control_channel):
    stack = control_channel.as_stack()
    assert len(stack.segments) == 3
    assert isclose(stack.length, control_channel.length)
    assert isclose(stack.segments[0].length, cr_chan_length - thimble_length)
    assert isclose(stack.segments[1].length, thimble_length*0.5)
    assert isclose(stack.segments[2].length, thimble_length*0.5)
    assert isclose(stack.bottom_pos, 0.0)

def test_openmc_builder(control_channel):
    geom_element = control_channel
    universe = openmc_builder.build(geom_element)
    assert universe.name == "control_channel"
    assert len(universe.cells) == 3
    for cell in universe.cells.values():
        assert cell.fill.name == "pincell"

def test_mpact_builder(control_channel, control_channel_mpact_specs, block):
    geom_element  = control_channel
    core          = mpact_builder.build(geom_element, control_channel_mpact_specs)

    assert isclose(core.mod_dim['X'], block.pitch)
    assert isclose(core.mod_dim['Y'], block.pitch)
    assert_allclose(core.mod_dim['Z'], [cr_chan_length - thimble_length, thimble_length*0.5])
    assert core.nz == 3
    assert isclose(core.height, cr_chan_length)

    assert len(core.pins)       == 3
    assert len(core.modules)    == 3
    assert len(core.lattices)   == 3
    assert len(core.assemblies) == 1

    assembly = core.assemblies[0]
    assert len(assembly.lattice_map) == 3
    assert isclose(assembly.lattice_map[0].pitch['Z'], cr_chan_length - thimble_length)
    assert isclose(assembly.lattice_map[1].pitch['Z'], thimble_length*0.5)
    assert isclose(assembly.lattice_map[2].pitch['Z'], thimble_length*0.5)

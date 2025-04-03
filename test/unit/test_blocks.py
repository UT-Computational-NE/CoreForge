import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose

from coreforge.shapes import Circle, Square, Rectangle
from coreforge.geometry_elements import Block
from test.unit.test_materials import graphite
from test.unit.msre.test_materials import salt

@pytest.fixture
def circle_chan(salt):
    return Block.Channel(shape=Circle(r=3.0), material=salt, distance_from_block_center=5.0*0.5)

@pytest.fixture
def rect_chan(salt):
    return Block.Channel(shape=Rectangle(w=4.0, h=3.0), material=salt, distance_from_block_center=5.0*0.5, rotation_about_block_center = 90.0)

@pytest.fixture
def block(salt, graphite, circle_chan, rect_chan):
    return Block(shape=Square(length=5.0), prism_material=graphite, channels=[circle_chan, rect_chan], outer_material=salt)

@pytest.fixture
def unequal_block(salt, graphite, circle_chan, rect_chan):
    return Block(shape=Square(length=5.0), prism_material=graphite, channels=[rect_chan, circle_chan], outer_material=salt)


def test_block_initialization(block, salt, graphite):
    geom_element = block
    assert geom_element.name == "block"
    assert geom_element.shape == Square(length=5.0)
    assert geom_element.prism_material == graphite
    assert geom_element.outer_material == salt
    assert len(geom_element.channels) == 2

    channel = geom_element.channels[0]
    assert channel.shape == Circle(r=3.0)
    assert isclose(channel.shape_rotation, 0.0)
    assert isclose(channel.distance_from_block_center, 5.0*0.5)
    assert isclose(channel.rotation_about_block_center, 0.0)
    assert channel.material == salt

    channel = geom_element.channels[1]
    assert channel.shape == Rectangle(w=4.0, h=3.0)
    assert isclose(channel.shape_rotation, 0.0)
    assert isclose(channel.distance_from_block_center, 5.0*0.5)
    assert isclose(channel.rotation_about_block_center, 90.0)
    assert channel.material == salt

def test_equality(block, unequal_block):
    assert block == deepcopy(block)
    assert block != unequal_block

def test_hash(block, unequal_block):
    assert hash(block) == hash(deepcopy(block))
    assert hash(block) != hash(unequal_block)

def test_make_openmc_universe(block):
    geom_element = block
    universe = geom_element.make_openmc_universe()
    assert universe.name == "block"
    assert len(universe.cells) == 4
    print ([cell.fill.name for cell in universe.cells.values()])
    assert [cell.fill.name for cell in universe.cells.values()] == ["Graphite",
                                                                    "Salt",
                                                                    "Salt",
                                                                    "Salt"]

def test_make_mpact_core(block):
    geom_element = block
    with pytest.raises(NotImplementedError,
        match="Cannot make an MPACT Core for Block block."):
        core = geom_element.make_mpact_core()

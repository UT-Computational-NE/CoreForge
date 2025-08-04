import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose
from mpactpy import RectangularPinMesh, Pin

from coreforge.shapes import Circle, Square, Rectangle
from coreforge.geometry_elements import Block
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
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

@pytest.fixture
def mpact_voxel_specs(salt, graphite):
    mat_specs = mpact_builder.MaterialSpecs({
        salt:     mpact_builder.DEFAULT_MPACT_SPECS[type(salt)],
        graphite: mpact_builder.DEFAULT_MPACT_SPECS[type(graphite)],
    })

    return mpact_builder.VoxelBuildSpecs(
        xvals          = [2.5, 5.0],
        yvals          = [2.5, 5.0],
        zvals          = [1.0],
        material_specs = mat_specs
    )

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

def test_openmc_builder(block):
    geom_element = block
    universe = openmc_builder.build(geom_element)
    assert universe.name == "block"
    assert len(universe.cells) == 4
    assert [cell.fill.name for cell in universe.cells.values()] == ["Graphite",
                                                                    "Salt",
                                                                    "Salt",
                                                                    "Salt"]

def test_block_mpact_builder(block, mpact_voxel_specs, salt, graphite):
    geom_element = block
    specs = mpact_voxel_specs
    core = mpact_builder.build(geom_element, specs)
    salt = mpact_builder.build_material(salt)
    graphite = mpact_builder.build_material(graphite)

    assert len(core.materials) == 1
    assert salt in core.materials

    assert isclose(core.mod_dim['X'], 5.0)
    assert isclose(core.mod_dim['Y'], 5.0)
    assert_allclose(core.mod_dim['Z'], [1.0])

    assert len(core.pins) == 1
    assert len(core.modules) == 1
    assert len(core.lattices) == 1
    assert len(core.assemblies) == 1

    expected_xvals = [2.5, 5.0]
    expected_yvals = [2.5, 5.0]
    expected_mats = [salt, salt, salt, salt]

    assert core.pins[0] == Pin(RectangularPinMesh(expected_xvals, expected_yvals, [1.0], [1, 1], [1, 1], [1]), expected_mats)

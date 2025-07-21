import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose
from mpactpy import RectangularPinMesh, Pin
import mpactpy

from coreforge.geometry_elements import InfiniteMedium
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from test.unit.test_materials import air, graphite
from test.unit.msre.test_materials import salt

@pytest.fixture
def infinite_medium(air):
    return InfiniteMedium(material=air)

@pytest.fixture
def unequal_infinite_medium(graphite):
    return InfiniteMedium(material=graphite)

@pytest.fixture
def infinite_medium_mpact_specs():
    return mpact_builder.InfiniteMedium.Specs(thicknesses = {"X": 8.0, "Y": 8.0})

@pytest.fixture
def mpact_voxel_specs(salt, graphite):
    # Set up material specs mapping from OpenMC materials to MPACT specs
    mat_specs = {
        salt.openmc_material: mpact_builder.DEFAULT_MPACT_SPECS[type(salt)],
        graphite.openmc_material: mpact_builder.DEFAULT_MPACT_SPECS[type(graphite)]
    }
    
    overlay_policy = mpactpy.PinMesh.OverlayPolicy(
        method='centroid',
        mat_specs=mat_specs,
        mix_policy=None,
        num_procs=1
    )
    
    return mpact_builder.VoxelBuildSpecs(
        xvals=[4.0, 8.0],
        yvals=[4.0, 8.0], 
        zvals=[1.0],
        overlay_policy=overlay_policy
    )

@pytest.fixture
def mpact_voxel_thickness_specs():
    return mpact_builder.VoxelBuildSpecs(
        x_thicknesses=[4.0, 4.0],
        y_thicknesses=[4.0, 4.0], 
        z_thicknesses=[1.0]
    )

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

def test_mpacts_builder(infinite_medium, infinite_medium_mpact_specs, air):

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

def test_mpact_voxel_builder(infinite_medium, mpact_voxel_specs, air):
    geom_element = infinite_medium
    specs = mpact_voxel_specs
    core = mpact_builder.build(geom_element, specs)
    air_mpact = mpact_builder.build_material(air)

    assert len(core.materials) == 1
    assert air_mpact in core.materials

    assert isclose(core.mod_dim['X'], 8.0)
    assert isclose(core.mod_dim['Y'], 8.0)
    assert_allclose(core.mod_dim['Z'], [1.0])

    assert len(core.pins) == 1
    assert len(core.modules) == 1
    assert len(core.lattices) == 1
    assert len(core.assemblies) == 1

    expected_xvals = [4.0, 8.0]
    expected_yvals = [4.0, 8.0]
    expected_mats = [air_mpact] * 4  # 2x2 = 4 voxels

    assert core.pins[0] == Pin(RectangularPinMesh(expected_xvals, expected_yvals, [1.0], [1, 1], [1, 1], [1]), expected_mats)

def test_voxel_specs_equivalence(mpact_voxel_specs, mpact_voxel_thickness_specs):
    # Test that boundary values and thickness values produce equivalent specs
    assert_allclose(mpact_voxel_specs.xvals, mpact_voxel_thickness_specs.xvals)
    assert_allclose(mpact_voxel_specs.yvals, mpact_voxel_thickness_specs.yvals)
    assert_allclose(mpact_voxel_specs.zvals, mpact_voxel_thickness_specs.zvals)
    assert_allclose(mpact_voxel_specs.x_thicknesses, mpact_voxel_thickness_specs.x_thicknesses)
    assert_allclose(mpact_voxel_specs.y_thicknesses, mpact_voxel_thickness_specs.y_thicknesses)
    assert_allclose(mpact_voxel_specs.z_thicknesses, mpact_voxel_thickness_specs.z_thicknesses)

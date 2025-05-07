import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose
from mpactpy import GeneralCylindricalPinMesh, Pin

from coreforge.shapes import Circle, Square, Hexagon, Stadium
from coreforge.geometry_elements import PinCell, CylindricalPincell
from test.unit.test_materials import graphite
from test.unit.msre.test_materials import salt

@pytest.fixture
def pincell(salt, graphite):
    zones = [PinCell.Zone(shape = Circle(r=1.),             material = salt),
             PinCell.Zone(shape = Square(length=4.),        material = graphite, rotation = 45.),
             PinCell.Zone(shape = Hexagon(inner_radius=8.), material = salt),
             PinCell.Zone(shape = Stadium(r=12., a=20.),    material = graphite, rotation = 90.)]
    return PinCell(zones = zones, outer_material = salt, x0 = 1., y0 = -2.)

@pytest.fixture
def unequal_pincell(salt, graphite):
    zones = [PinCell.Zone(shape = Circle(r=1.),          material = salt),
             PinCell.Zone(shape = Stadium(r=12., a=20.), material = graphite, rotation = 90.)]
    return PinCell(zones = zones, outer_material = salt, x0 = 1., y0 = -2.)

@pytest.fixture
def cylindrical_pincell(salt, graphite):
    bounds                  = (-4.0, 4.0, -4.0, 4.0)

    return CylindricalPincell(radii             = [  1.,       2.,   3.          ],
                              materials         = [salt, graphite, salt, graphite],
                              mpact_build_specs = CylindricalPincell.MPACTBuildSpecs(bounds=bounds))

def test_pincell_initialization(pincell):
    geom_element = pincell
    assert geom_element.name == "pincell"
    assert len(geom_element.zones) == 4
    assert geom_element.zones[0].material.name == "Salt"
    assert geom_element.zones[1].material.name == "Graphite"
    assert geom_element.zones[2].material.name == "Salt"
    assert geom_element.zones[3].material.name == "Graphite"
    assert isinstance(geom_element.zones[0].shape, Circle)
    assert isinstance(geom_element.zones[1].shape, Square)
    assert isinstance(geom_element.zones[2].shape, Hexagon)
    assert isinstance(geom_element.zones[3].shape, Stadium)
    assert isclose(geom_element.zones[0].rotation, 0.)
    assert isclose(geom_element.zones[1].rotation, 45.)
    assert isclose(geom_element.zones[2].rotation, 0.)
    assert isclose(geom_element.zones[3].rotation, 90.)
    assert geom_element.outer_material.name == "Salt"
    assert isclose(geom_element.x0, 1.0)
    assert isclose(geom_element.y0, -2.0)

def test_equality(pincell, unequal_pincell):
    assert pincell == deepcopy(pincell)
    assert pincell != unequal_pincell

def test_hash(pincell, unequal_pincell):
    assert hash(pincell) == hash(deepcopy(pincell))
    assert hash(pincell) != hash(unequal_pincell)

def test_make_openmc_universe(pincell):
    geom_element = pincell
    universe = geom_element.make_openmc_universe()
    assert universe.name == "pincell"
    assert len(universe.cells) == 5
    assert [cell.fill.name for cell in universe.cells.values()] == ["Salt",
                                                                    "Graphite",
                                                                    "Salt",
                                                                    "Graphite",
                                                                    "Salt"]

def test_pincell_make_mpact_core(pincell):
    geom_element = pincell
    with pytest.raises(NotImplementedError,
        match="Cannot make an MPACT Core for PinCell pincell."):
        core = geom_element.make_mpact_core()

def test_cylindrical_pincell_initialization(cylindrical_pincell):
    geom_element = cylindrical_pincell
    assert geom_element.name == "pincell"
    assert len(geom_element.zones) == 3
    assert geom_element.zones[0].material.name == "Salt"
    assert geom_element.zones[1].material.name == "Graphite"
    assert geom_element.zones[2].material.name == "Salt"
    assert isinstance(geom_element.zones[0].shape, Circle)
    assert isinstance(geom_element.zones[1].shape, Circle)
    assert isinstance(geom_element.zones[2].shape, Circle)
    assert isclose(geom_element.zones[0].rotation, 0.)
    assert isclose(geom_element.zones[1].rotation, 0.)
    assert isclose(geom_element.zones[2].rotation, 0.)
    assert geom_element.outer_material.name == "Graphite"
    assert isclose(geom_element.x0, 0.0)
    assert isclose(geom_element.y0, 0.0)
    geom_element.mpact_build_specs = None
    assert isclose(geom_element.mpact_build_specs.bounds[0], -3)
    assert isclose(geom_element.mpact_build_specs.bounds[1],  3)
    assert isclose(geom_element.mpact_build_specs.bounds[2], -3)
    assert isclose(geom_element.mpact_build_specs.bounds[3],  3)

def test_cylindrical_pincell_make_mpact_core(cylindrical_pincell, salt, graphite):

    geom_element = cylindrical_pincell
    core         = geom_element.make_mpact_core()
    salt         = salt.mpact_material
    graphite     = graphite.mpact_material

    assert len(core.materials) == 2
    assert salt in core.materials
    assert graphite in core.materials

    assert isclose(core.mod_dim['X'], 8.0)
    assert isclose(core.mod_dim['Y'], 8.0)
    assert_allclose(core.mod_dim['Z'], [1.0])

    assert len(core.pins)       == 1
    assert len(core.modules)    == 1
    assert len(core.lattices)   == 1
    assert len(core.assemblies) == 1

    expected_radii = [1.0, 2.0, 3.0]
    expected_mats  = [salt, graphite, salt, graphite]

    assert core.pins[0] == Pin(GeneralCylindricalPinMesh(expected_radii, -4.0, 4.0, -4.0, 4.0, [1.0], [1, 1, 1], [1, 1, 1, 1], [1]), expected_mats)

    mpact_build_specs = deepcopy(geom_element.mpact_build_specs)
    mpact_build_specs.divide_into_quadrants = True
    geom_element.mpact_build_specs = mpact_build_specs
    core = geom_element.make_mpact_core()

    assert isclose(core.mod_dim['X'], 4.0)
    assert isclose(core.mod_dim['Y'], 4.0)
    assert core.lattices[0].nx == 2
    assert core.lattices[0].ny == 2

    pin = {"NW" : core.lattices[0].module_map[0][0].pin_map[0][0],
           "NE" : core.lattices[0].module_map[0][1].pin_map[0][0],
           "SW" : core.lattices[0].module_map[1][0].pin_map[0][0],
           "SE" : core.lattices[0].module_map[1][1].pin_map[0][0]}

    assert pin["NW"] == Pin(GeneralCylindricalPinMesh(expected_radii, -4.0, 0.0,  0.0, 4.0, [1.0], [1, 1, 1], [1, 1, 1, 1], [1]), expected_mats)
    assert pin["NE"] == Pin(GeneralCylindricalPinMesh(expected_radii,  0.0, 4.0,  0.0, 4.0, [1.0], [1, 1, 1], [1, 1, 1, 1], [1]), expected_mats)
    assert pin["SW"] == Pin(GeneralCylindricalPinMesh(expected_radii, -4.0, 0.0, -4.0, 0.0, [1.0], [1, 1, 1], [1, 1, 1, 1], [1]), expected_mats)
    assert pin["SE"] == Pin(GeneralCylindricalPinMesh(expected_radii,  0.0, 4.0, -4.0, 0.0, [1.0], [1, 1, 1], [1, 1, 1, 1], [1]), expected_mats)

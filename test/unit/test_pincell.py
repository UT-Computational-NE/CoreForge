import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose
from mpactpy import GeneralCylindricalPinMesh, RectangularPinMesh, Pin
import mpactpy

from coreforge.shapes import Circle, Square, Hexagon, Stadium
from coreforge.geometry_elements import PinCell, PinCells, CylindricalPinCell, CylindricalPinCells
from coreforge.materials import unique_materials
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from test.unit.test_materials import graphite, water
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
    return CylindricalPinCell(radii             = [  1.,       2.,   3.          ],
                              materials         = [salt, graphite, salt, graphite])

@pytest.fixture(params=[PinCells, CylindricalPinCells])
def pincells(request, salt, graphite, water):
    pin_type = CylindricalPinCell if request.param is CylindricalPinCells else PinCell
    lower_shape = Circle(r=2.) if pin_type is CylindricalPinCell else Square(length=4.)
    lower = pin_type(zones=[PinCell.Zone(shape=lower_shape, material=graphite)],
                     outer_material=water, x0=1., y0=-2.)
    upper = pin_type(zones=[PinCell.Zone(shape=Circle(r=1.), material=salt)],
                     outer_material=water, x0=3., y0=-2.)
    return request.param(pincells=[lower, upper], name="layered_pincells")

@pytest.fixture
def cylindrical_pincell_mpact_specs():
    return mpact_builder.CylindricalPinCell.Specs()

@pytest.fixture
def mpact_voxel_specs(salt, graphite):
    mat_specs = {
        salt:     mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS[type(salt)],
        graphite: mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS[type(graphite)],
    }

    return mpact_builder.VoxelBuilder.Specs(
        target_thicknesses = {"X": 16.0, "Y": 16.0, "Z": 1.0},
        material_specs     = mat_specs
    )


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
    expected = unique_materials([zone.material for zone in geom_element.zones] + [geom_element.outer_material])
    assert geom_element.get_materials() == expected

    unchanged = deepcopy(pincell)
    overlaid = pincell.overlay(None)
    assert overlaid == pincell
    assert overlaid is not pincell
    assert overlaid.zones[0] is not pincell.zones[0]
    assert overlaid.zones[0].shape is not pincell.zones[0].shape
    assert overlaid.zones[0].material is not pincell.zones[0].material
    overlaid.x0 += 1.
    overlaid.zones[0].rotation += 15.
    assert pincell == unchanged

def test_equality_and_hash(pincell, unequal_pincell):
    assert pincell == deepcopy(pincell)
    assert pincell != unequal_pincell
    assert hash(pincell) == hash(deepcopy(pincell))
    assert hash(pincell) != hash(unequal_pincell)

@pytest.mark.parametrize("fixture_name", ["pincell", "cylindrical_pincell"])
def test_pincell_translate(request, fixture_name):
    original = request.getfixturevalue(fixture_name)
    unchanged = deepcopy(original)
    translated = original.translate(dx=2., dy=-3.)

    assert type(translated) is type(original)
    assert translated.name == original.name
    assert isclose(translated.x0, original.x0 + 2.)
    assert isclose(translated.y0, original.y0 - 3.)
    assert translated.zones == original.zones
    assert translated.outer_material == original.outer_material
    assert translated.outer_material is not original.outer_material
    for translated_zone, original_zone in zip(translated.zones, original.zones):
        assert translated_zone is not original_zone
        assert translated_zone.shape is not original_zone.shape
        assert translated_zone.material is not original_zone.material
    translated.zones[0].rotation += 15.
    assert original == unchanged

def test_pincells_initialization(pincells):
    assert pincells.name == "layered_pincells"
    assert len(pincells.pincells) == 2
    assert pincells.pincells[0].zones[0].material.name == "Graphite"
    assert pincells.pincells[1].zones[0].material.name == "Salt"
    assert pincells.outer_material == pincells.pincells[0].outer_material
    expected = unique_materials([material for pin in pincells.pincells for material in pin.get_materials()])
    assert pincells.get_materials() == expected

    pins = list(pincells.pincells)
    copied_list = type(pincells)(pincells=pins)
    pins.reverse()
    assert copied_list.pincells == pincells.pincells
    with pytest.raises(AssertionError):
        type(pincells)(pincells=[])
    incompatible = deepcopy(pincells.pincells[1])
    incompatible.outer_material = incompatible.zones[0].material
    with pytest.raises(AssertionError):
        type(pincells)(pincells=[pincells.pincells[0], incompatible])
    with pytest.raises(AssertionError):
        type(pincells)(pincells=[object()])
    if isinstance(pincells, CylindricalPinCells):
        generic_pin = PinCell(zones=[PinCell.Zone(shape=Square(length=2.), material=pincells.outer_material)],
                              outer_material=pincells.outer_material)
        with pytest.raises(AssertionError):
            CylindricalPinCells(pincells=[generic_pin])

def test_pincells_equality_and_hash(pincells):
    equal = deepcopy(pincells)
    reversed_layers = type(pincells)(pincells=list(reversed(pincells.pincells)))
    assert pincells == equal
    assert hash(pincells) == hash(equal)
    assert pincells != reversed_layers
    assert hash(pincells) != hash(reversed_layers)
    unequal = deepcopy(pincells)
    unequal.pincells[0].x0 += 1.
    assert pincells != unequal
    assert hash(pincells) != hash(unequal)

def test_pincells_openmc_builder(pincells, salt, graphite, water):
    universe = openmc_builder.build(pincells)
    assert universe.name == pincells.name
    assert len(universe.cells) == 3
    for point, material in [((0., -2., 0.), graphite),
                            ((2.5, -2., 0.), salt),
                            ((3.5, -2., 0.), salt),
                            ((5., -2., 0.), water)]:
        cells = [cell for cell in universe.cells.values() if point in cell.region]
        assert len(cells) == 1
        assert cells[0].fill is material.openmc_material

    reversed_layers = type(pincells)(pincells=list(reversed(pincells.pincells)))
    reversed_universe = openmc_builder.build(reversed_layers)
    assert reversed_universe.find((2.5, -2., 0.))[-1].fill is graphite.openmc_material

def test_openmc_builder(pincell):
    geom_element = pincell
    universe = openmc_builder.build(geom_element)
    assert universe.name == "pincell"
    assert len(universe.cells) == 5
    assert [cell.fill.name for cell in universe.cells.values()] == ["Salt",
                                                                    "Graphite",
                                                                    "Salt",
                                                                    "Graphite",
                                                                    "Salt"]

def test_pincell_mpact_builder(pincell, mpact_voxel_specs, salt, graphite):
    geom_element = pincell
    specs = mpact_voxel_specs
    bounds = mpact_builder.Bounds(X=mpact_builder.AxisBounds(min=0.0, max=32.0),
                                  Y=mpact_builder.AxisBounds(min=0.0, max=32.0),
                                  Z=mpact_builder.AxisBounds(min=0.0, max=1.0))
    core = mpact_builder.build(geom_element, specs, bounds)
    salt = mpact_builder.build_material(salt)
    graphite = mpact_builder.build_material(graphite)

    assert len(core.materials) == 2
    assert salt in core.materials
    assert graphite in core.materials

    assert isclose(core.mod_dim['X'], 32.0)
    assert isclose(core.mod_dim['Y'], 32.0)
    assert_allclose(core.mod_dim['Z'], [1.0])

    assert len(core.pins) == 1
    assert len(core.modules) == 1
    assert len(core.lattices) == 1
    assert len(core.assemblies) == 1

    expected_xvals = [16.0, 32.0]
    expected_yvals = [16.0, 32.0]
    expected_mats = [salt, salt, graphite, salt]

    assert core.pins[0] == Pin(RectangularPinMesh(expected_xvals, expected_yvals, [1.0], [1, 1], [1, 1], [1]), expected_mats)


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
    expected = unique_materials([zone.material for zone in geom_element.zones] + [geom_element.outer_material])
    assert geom_element.get_materials() == expected


def test_cylindrical_pincell_meshing_factory():
    zone_specs = mpact_builder.CylindricalPinCell.meshing(ndivr_fsr      = 2,
                                                          ndivr_mat      = 3,
                                                          ndiva          = 4,
                                                          ndivr_mat_type = "equal_volume")

    assert len(zone_specs) == 1
    assert zone_specs[0] == mpact_builder.CylindricalPinCell.ZoneSpecs(ndivr_fsr      = 2,
                                                                       ndivr_mat      = 3,
                                                                       ndiva          = 4,
                                                                       ndivr_mat_type = "equal_volume")

    zone_specs = mpact_builder.CylindricalPinCell.meshing(
        ndivr_fsr      = [1, 2, 3],
        ndivr_mat      = 4,
        ndiva          = [5, 6, 7],
        ndivr_mat_type = ["equal_thickness", "equal_volume", "equal_thickness"]
    )

    assert [(spec.ndivr_fsr, spec.ndivr_mat, spec.ndiva, spec.ndivr_mat_type)
            for spec in zone_specs] == [(1, 4, 5, "equal_thickness"),
                                        (2, 4, 6, "equal_volume"),
                                        (3, 4, 7, "equal_thickness")]

    with pytest.raises(AssertionError):
        mpact_builder.CylindricalPinCell.meshing(ndivr_fsr = [1, 2],
                                                 ndivr_mat = [1],
                                                 ndiva     = 4)


def test_cylindrical_pincell_mpact_builder(cylindrical_pincell, cylindrical_pincell_mpact_specs, salt, graphite):

    geom_element = cylindrical_pincell
    specs        = cylindrical_pincell_mpact_specs
    bounds       = mpact_builder.Bounds(X=mpact_builder.AxisBounds(min=-4.0, max=4.0),
                                        Y=mpact_builder.AxisBounds(min=-4.0, max=4.0))
    core         = mpact_builder.build(geom_element, specs, bounds)
    salt         = mpact_builder.build_material(salt)
    graphite     = mpact_builder.build_material(graphite)

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

    specs.divide_into_quadrants = True
    core = mpact_builder.build(geom_element, specs, bounds)

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


def test_cylindrical_pincell_min_zone_thickness(salt, graphite):
    radii = [1.0, 1.001, 3.0]  # tiny gap between 1.0 and 1.001
    materials = [salt, graphite, salt, graphite]
    pin = CylindricalPinCell(radii=radii, materials=materials, min_zone_thickness=0.01)

    # The tiny graphite zone should be removed; remaining radii/materials collapse accordingly.
    assert [zone.shape.outer_radius for zone in pin.zones] == pytest.approx([1.0, 3.0])
    assert [zone.material for zone in pin.zones] == [salt, salt]
    assert pin.outer_material == graphite

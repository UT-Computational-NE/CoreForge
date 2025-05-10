import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose
from mpactpy import Pin, RectangularPinMesh as RectMesh, GeneralCylindricalPinMesh as GCylMesh

from coreforge.shapes import Circle, Stadium, Rectangle, Square
from coreforge.geometry_elements.msre import Block
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from test.unit.test_materials import graphite
from test.unit.msre.test_materials import salt

fuel_chan_r    = 0.508
fuel_chan_a    = 2.032
control_chan_r = 3.01625
block_pitch    = 5.08

@pytest.fixture
def stadium_fuel_chan(salt):
    return Block.FuelChannel(shape=Stadium(r=fuel_chan_r, a=fuel_chan_a), material=salt)

@pytest.fixture
def rectangle_fuel_chan(salt):
    return Block.FuelChannel(shape=Rectangle(h=fuel_chan_r*2.0, w=fuel_chan_a + fuel_chan_r*2.0), material=salt)

@pytest.fixture
def circle_fuel_chan(salt):
    return Block.FuelChannel(shape=Circle(r=fuel_chan_r), material=salt)

@pytest.fixture
def control_chan(salt):
    return Block.ControlChannel(shape=Circle(r=control_chan_r), material=salt)


@pytest.fixture
def block(salt, graphite, stadium_fuel_chan, control_chan):
    return Block(pitch          = block_pitch,
                 prism_material = graphite,
                 outer_material = salt,
                 channels       = {"N": stadium_fuel_chan,
                                   "S": stadium_fuel_chan,
                                   "E": control_chan,
                                   "W": control_chan})

@pytest.fixture
def unequal_block(salt, graphite, stadium_fuel_chan, control_chan):
    return Block(pitch          = block_pitch,
                 prism_material = graphite,
                 outer_material = salt,
                 channels       = {"N": control_chan,
                                   "S": control_chan,
                                   "E": stadium_fuel_chan,
                                   "W": stadium_fuel_chan})

@pytest.fixture
def stadium_fuel_chan_block(salt, graphite, stadium_fuel_chan):
    return Block(pitch          = block_pitch,
                 prism_material = graphite,
                 outer_material = salt,
                 channels       = {"N": stadium_fuel_chan,
                                   "S": stadium_fuel_chan,
                                   "E": stadium_fuel_chan,
                                   "W": stadium_fuel_chan})

@pytest.fixture
def rectangle_fuel_chan_block(salt, graphite, rectangle_fuel_chan):
    return Block(pitch          = block_pitch,
                 prism_material = graphite,
                 outer_material = salt,
                 channels       = {"N": rectangle_fuel_chan,
                                   "S": rectangle_fuel_chan,
                                   "E": rectangle_fuel_chan,
                                   "W": rectangle_fuel_chan})

@pytest.fixture
def circle_fuel_chan_block(salt, graphite, circle_fuel_chan):
    return Block(pitch          = block_pitch,
                 prism_material = graphite,
                 outer_material = salt,
                 channels       = {"N": circle_fuel_chan,
                                   "S": circle_fuel_chan,
                                   "E": circle_fuel_chan,
                                   "W": circle_fuel_chan})

@pytest.fixture
def control_chan_block(salt, graphite, control_chan):
    return Block(pitch          = block_pitch,
                 prism_material = graphite,
                 outer_material = salt,
                 channels       = {"N": control_chan,
                                   "S": control_chan,
                                   "E": control_chan,
                                   "W": control_chan})

@pytest.fixture
def no_chan_block(salt, graphite):
    return Block(pitch          = block_pitch,
                 prism_material = graphite,
                 outer_material = salt,
                 channels       = {"N": None,
                                   "S": None,
                                   "E": None,
                                   "W": None})


def test_block_initialization(block, salt, graphite):
    geom_element = block
    assert geom_element.name == "msre_block"
    assert isclose(geom_element.pitch, block_pitch)
    assert geom_element.shape == Square(length=block_pitch)
    assert geom_element.prism_material == graphite
    assert geom_element.outer_material == salt
    assert geom_element.has_fuel_channels
    assert geom_element.fuel_channels_have_equal_shapes
    assert geom_element.has_control_channels
    assert geom_element.control_channels
    assert geom_element.control_channels_have_equal_shapes
    assert len(geom_element.channels) == 4
    assert len(geom_element.fuel_channels) == 2
    assert len(geom_element.control_channels) == 2

    for i, channel in enumerate(geom_element.fuel_channels):
        assert channel.shape == Stadium(r=fuel_chan_r, a=fuel_chan_a)
        assert isclose(channel.shape_rotation, 0.0)
        assert isclose(channel.distance_from_block_center, block_pitch*0.5)
        assert isclose(channel.rotation_about_block_center, (1-i)*180.0)
        assert channel.material == salt

    for i, channel in enumerate(geom_element.control_channels):
        assert channel.shape == Circle(r=control_chan_r)
        assert isclose(channel.shape_rotation, 0.0)
        assert isclose(channel.distance_from_block_center, block_pitch)
        assert isclose(channel.rotation_about_block_center, 90+i*180.0)
        assert channel.material == salt


def test_equality(block, unequal_block):
    assert block == deepcopy(block)
    assert block != unequal_block

def test_hash(block, unequal_block):
    assert hash(block) == hash(deepcopy(block))
    assert hash(block) != hash(unequal_block)

def test_make_openmc_universe(block):
    geom_element = block
    universe = openmc_builder.build(geom_element)
    assert universe.name == "msre_block"
    assert len(universe.cells) == 6
    assert [cell.fill.name for cell in universe.cells.values()] == ["Graphite",
                                                                    "Salt",
                                                                    "Salt",
                                                                    "Salt",
                                                                    "Salt",
                                                                    "Salt"]

def test_mpact_builder(stadium_fuel_chan_block, rectangle_fuel_chan_block,
                       circle_fuel_chan_block,  control_chan_block,
                       no_chan_block, salt, graphite):

    salt     = mpact_builder.build_material(salt)
    graphite = mpact_builder.build_material(graphite)

    # Stadium Fuel Channels
    core = mpact_builder.build(stadium_fuel_chan_block)

    assert len(core.materials) == 2
    assert salt in core.materials
    assert graphite in core.materials

    assert isclose(core.mod_dim['X'], block_pitch)
    assert isclose(core.mod_dim['Y'], block_pitch)
    assert_allclose(core.mod_dim['Z'], [1.0])

    assert len(core.modules)    == 1
    assert len(core.lattices)   == 1
    assert len(core.assemblies) == 1

    half_block_pitch = block_pitch * 0.5
    half_flat_length = fuel_chan_a * 0.5
    cap_cell_length  = (half_block_pitch - half_flat_length)*0.5

    zval             = [1.0]
    divz             = [1]
    divr             = [1, 1]
    diva             = [1, 1, 1]
    radii            = [fuel_chan_r, cap_cell_length]
    fcr              = fuel_chan_r
    ccl              = cap_cell_length
    hfl              = half_flat_length

    corner        = Pin(RectMesh([ccl], [ccl], zval, [1], [1], divz), [graphite])
    center        = Pin(RectMesh([hfl], [hfl], zval, [1], [1], divz), [graphite])
    H_spacer      = Pin(RectMesh([hfl], [ccl], zval, [1], [1], divz), [graphite])
    V_spacer      = Pin(RectMesh([ccl], [hfl], zval, [1], [1], divz), [graphite])

    N_chan_E_cap  = Pin(GCylMesh(radii,  0.0, ccl, -ccl,  0.0, zval, divr, diva, divz), [salt, graphite, graphite])
    N_chan_W_cap  = Pin(GCylMesh(radii, -ccl, 0.0, -ccl,  0.0, zval, divr, diva, divz), [salt, graphite, graphite])
    S_chan_E_cap  = Pin(GCylMesh(radii,  0.0, ccl,  0.0,  ccl, zval, divr, diva, divz), [salt, graphite, graphite])
    S_chan_W_cap  = Pin(GCylMesh(radii, -ccl, 0.0,  0.0,  ccl, zval, divr, diva, divz), [salt, graphite, graphite])
    E_chan_N_cap  = Pin(GCylMesh(radii, -ccl, 0.0,  0.0,  ccl, zval, divr, diva, divz), [salt, graphite, graphite])
    E_chan_S_cap  = Pin(GCylMesh(radii, -ccl, 0.0, -ccl,  0.0, zval, divr, diva, divz), [salt, graphite, graphite])
    W_chan_N_cap  = Pin(GCylMesh(radii,  0.0, ccl,  0.0,  ccl, zval, divr, diva, divz), [salt, graphite, graphite])
    W_chan_S_cap  = Pin(GCylMesh(radii,  0.0, ccl, -ccl,  0.0, zval, divr, diva, divz), [salt, graphite, graphite])

    N_chan_E_flat = Pin(RectMesh([         hfl], [ccl-fcr, ccl], zval, [1], [1,1], divz), [salt, graphite])
    N_chan_W_flat = Pin(RectMesh([         hfl], [ccl-fcr, ccl], zval, [1], [1,1], divz), [salt, graphite])
    S_chan_E_flat = Pin(RectMesh([         hfl], [    fcr, ccl], zval, [1], [1,1], divz), [graphite, salt])
    S_chan_W_flat = Pin(RectMesh([         hfl], [    fcr, ccl], zval, [1], [1,1], divz), [graphite, salt])
    E_chan_N_flat = Pin(RectMesh([ccl-fcr, ccl], [         hfl], zval, [1,1], [1], divz), [graphite, salt])
    E_chan_S_flat = Pin(RectMesh([ccl-fcr, ccl], [         hfl], zval, [1,1], [1], divz), [graphite, salt])
    W_chan_N_flat = Pin(RectMesh([    fcr, ccl], [         hfl], zval, [1,1], [1], divz), [salt, graphite])
    W_chan_S_flat = Pin(RectMesh([    fcr, ccl], [         hfl], zval, [1,1], [1], divz), [salt, graphite])

    expected_map  = [[corner       , N_chan_W_cap, N_chan_W_flat, N_chan_E_flat, N_chan_E_cap, corner       ],
                     [W_chan_N_cap , corner      , H_spacer     , H_spacer     , corner      , E_chan_N_cap ],
                     [W_chan_N_flat, V_spacer    , center       , center       , V_spacer    , E_chan_N_flat],
                     [W_chan_S_flat, V_spacer    , center       , center       , V_spacer    , E_chan_S_flat],
                     [W_chan_S_cap , corner      , H_spacer     , H_spacer     , corner      , E_chan_S_cap ],
                     [corner       , S_chan_W_cap, S_chan_W_flat, S_chan_E_flat, S_chan_E_cap, corner       ]]

    assert core.modules[0].pin_map == expected_map



    # Stadium Fuel Channels (Divided into Quadrants)
    mpact_build_specs = mpact_builder.msre.Block.Specs(divide_into_quadrants = True)
    core = mpact_builder.build(stadium_fuel_chan_block, mpact_build_specs)

    assert len(core.modules) == 4
    assert isclose(core.mod_dim['X'], block_pitch*0.5)
    assert isclose(core.mod_dim['Y'], block_pitch*0.5)
    assert core.lattices[0].nx == 2
    assert core.lattices[0].ny == 2

    expected_maps = [[[corner       , N_chan_W_cap, N_chan_W_flat],
                      [W_chan_N_cap , corner      , H_spacer     ],
                      [W_chan_N_flat, V_spacer    , center       ]],

                     [[N_chan_E_flat, N_chan_E_cap, corner       ],
                      [H_spacer     , corner      , E_chan_N_cap ],
                      [center       , V_spacer    , E_chan_N_flat]],

                     [[W_chan_S_flat, V_spacer    , center       ],
                      [W_chan_S_cap , corner      , H_spacer     ],
                      [corner       , S_chan_W_cap, S_chan_W_flat]],

                     [[center       , V_spacer    , E_chan_S_flat],
                      [H_spacer     , corner      , E_chan_S_cap ],
                      [S_chan_E_flat, S_chan_E_cap, corner       ]]]

    module_map = core.lattices[0].module_map
    assert module_map[0][0].pin_map == expected_maps[0]
    assert module_map[0][1].pin_map == expected_maps[1]
    assert module_map[1][0].pin_map == expected_maps[2]
    assert module_map[1][1].pin_map == expected_maps[3]


    # Rectangular Fuel Channels
    core = mpact_builder.build(rectangle_fuel_chan_block)

    N_chan_E_cap  = Pin(RectMesh([    fcr, ccl], [ccl-fcr, ccl], zval, [1,1], [1,1], divz), [salt, graphite, graphite, graphite])
    N_chan_W_cap  = Pin(RectMesh([ccl-fcr, ccl], [ccl-fcr, ccl], zval, [1,1], [1,1], divz), [graphite, salt, graphite, graphite])
    S_chan_E_cap  = Pin(RectMesh([    fcr, ccl], [    fcr, ccl], zval, [1,1], [1,1], divz), [graphite, graphite, salt, graphite])
    S_chan_W_cap  = Pin(RectMesh([ccl-fcr, ccl], [    fcr, ccl], zval, [1,1], [1,1], divz), [graphite, graphite,graphite, salt])
    E_chan_N_cap  = Pin(RectMesh([ccl-fcr, ccl], [    fcr, ccl], zval, [1,1], [1,1], divz), [graphite, graphite,graphite, salt])
    E_chan_S_cap  = Pin(RectMesh([ccl-fcr, ccl], [ccl-fcr, ccl], zval, [1,1], [1,1], divz), [graphite, salt, graphite, graphite])
    W_chan_N_cap  = Pin(RectMesh([    fcr, ccl], [    fcr, ccl], zval, [1,1], [1,1], divz), [graphite, graphite, salt, graphite])
    W_chan_S_cap  = Pin(RectMesh([    fcr, ccl], [ccl-fcr, ccl], zval, [1,1], [1,1], divz), [salt, graphite, graphite, graphite])

    expected_map  = [[corner       , N_chan_W_cap, N_chan_W_flat, N_chan_E_flat, N_chan_E_cap, corner       ],
                     [W_chan_N_cap , corner      , H_spacer     , H_spacer     , corner      , E_chan_N_cap ],
                     [W_chan_N_flat, V_spacer    , center       , center       , V_spacer    , E_chan_N_flat],
                     [W_chan_S_flat, V_spacer    , center       , center       , V_spacer    , E_chan_S_flat],
                     [W_chan_S_cap , corner      , H_spacer     , H_spacer     , corner      , E_chan_S_cap ],
                     [corner       , S_chan_W_cap, S_chan_W_flat, S_chan_E_flat, S_chan_E_cap, corner       ]]

    assert core.modules[0].pin_map == expected_map


    # Circular Fuel Channels
    core             = mpact_builder.build(circle_fuel_chan_block)

    cap_cell_length  = (half_block_pitch)*0.5
    radii            = [fuel_chan_r, cap_cell_length]
    ccl              = cap_cell_length

    prism            = Pin(RectMesh([ccl], [ccl], zval, [1], [1], divz), [graphite])
    N_chan_E_cap     = Pin(GCylMesh(radii,  0.0,  ccl, -ccl, 0.0, zval, divr, diva, divz), [salt, graphite, graphite])
    N_chan_W_cap     = Pin(GCylMesh(radii, -ccl,  0.0, -ccl, 0.0, zval, divr, diva, divz), [salt, graphite, graphite])
    S_chan_E_cap     = Pin(GCylMesh(radii,  0.0,  ccl,  0.0, ccl, zval, divr, diva, divz), [salt, graphite, graphite])
    S_chan_W_cap     = Pin(GCylMesh(radii, -ccl,  0.0,  0.0, ccl, zval, divr, diva, divz), [salt, graphite, graphite])
    E_chan_N_cap     = Pin(GCylMesh(radii, -ccl,  0.0,  0.0, ccl, zval, divr, diva, divz), [salt, graphite, graphite])
    E_chan_S_cap     = Pin(GCylMesh(radii, -ccl,  0.0, -ccl, 0.0, zval, divr, diva, divz), [salt, graphite, graphite])
    W_chan_N_cap     = Pin(GCylMesh(radii,  0.0,  ccl,  0.0, ccl, zval, divr, diva, divz), [salt, graphite, graphite])
    W_chan_S_cap     = Pin(GCylMesh(radii,  0.0,  ccl, -ccl, 0.0, zval, divr, diva, divz), [salt, graphite, graphite])

    expected_map     = [[prism       , N_chan_W_cap, N_chan_E_cap, prism       ],
                        [W_chan_N_cap, prism       , prism       , E_chan_N_cap],
                        [W_chan_S_cap, prism       , prism       , E_chan_S_cap],
                        [prism       , S_chan_W_cap, S_chan_E_cap, prism       ]]

    assert core.modules[0].pin_map == expected_map


    # No Channels
    core         = mpact_builder.build(no_chan_block)

    expected_map = [[prism , prism, prism, prism],
                    [prism , prism, prism, prism],
                    [prism , prism, prism, prism],
                    [prism , prism, prism, prism]]

    assert core.modules[0].pin_map == expected_map


    # Control Rod Channels
    core             = mpact_builder.build(control_chan_block)

    cap_cell_length  = control_chan_r - block_pitch*0.5
    half_flat_length = (block_pitch - cap_cell_length*4.0)*0.5
    radii            = [control_chan_r]
    divr             = [1]
    diva             = [1,1]
    ccl              = cap_cell_length
    hfl              = half_flat_length
    hbp              = half_block_pitch

    corner           = Pin(RectMesh([ccl], [ccl], zval, [1], [1], divz), [graphite])
    center           = Pin(RectMesh([hfl], [hfl], zval, [1], [1], divz), [graphite])
    H_spacer         = Pin(RectMesh([hfl], [ccl], zval, [1], [1], divz), [graphite])
    V_spacer         = Pin(RectMesh([ccl], [hfl], zval, [1], [1], divz), [graphite])

    N_chan_E_cap     = Pin(GCylMesh(radii,      hfl, hfl+ccl, -hbp-ccl,    -hbp, zval, divr, diva, divz), [salt, graphite])
    N_chan_W_cap     = Pin(GCylMesh(radii, -hfl-ccl,    -hfl, -hbp-ccl,    -hbp, zval, divr, diva, divz), [salt, graphite])
    S_chan_E_cap     = Pin(GCylMesh(radii,      hfl, hfl+ccl,      hbp, hbp+ccl, zval, divr, diva, divz), [salt, graphite])
    S_chan_W_cap     = Pin(GCylMesh(radii, -hfl-ccl,    -hfl,      hbp, hbp+ccl, zval, divr, diva, divz), [salt, graphite])
    E_chan_N_cap     = Pin(GCylMesh(radii, -hbp-ccl,    -hbp,      hfl, hfl+ccl, zval, divr, diva, divz), [salt, graphite])
    E_chan_S_cap     = Pin(GCylMesh(radii, -hbp-ccl,    -hbp, -hfl-ccl,    -hfl, zval, divr, diva, divz), [salt, graphite])
    W_chan_N_cap     = Pin(GCylMesh(radii,      hbp, hbp+ccl,      hfl, hfl+ccl, zval, divr, diva, divz), [salt, graphite])
    W_chan_S_cap     = Pin(GCylMesh(radii,      hbp, hbp+ccl, -hfl-ccl,    -hfl, zval, divr, diva, divz), [salt, graphite])

    N_chan_E_flat    = Pin(GCylMesh(radii,      0.0,      hfl, -hbp-ccl,    -hbp, zval, divr, diva, divz), [salt, graphite])
    N_chan_W_flat    = Pin(GCylMesh(radii,     -hfl,      0.0, -hbp-ccl,    -hbp, zval, divr, diva, divz), [salt, graphite])
    S_chan_E_flat    = Pin(GCylMesh(radii,      0.0,      hfl,      hbp, hbp+ccl, zval, divr, diva, divz), [salt, graphite])
    S_chan_W_flat    = Pin(GCylMesh(radii,     -hfl,      0.0,      hbp, hbp+ccl, zval, divr, diva, divz), [salt, graphite])
    E_chan_N_flat    = Pin(GCylMesh(radii, -hbp-ccl,     -hbp,      0.0,     hfl, zval, divr, diva, divz), [salt, graphite])
    E_chan_S_flat    = Pin(GCylMesh(radii, -hbp-ccl,     -hbp,     -hfl,     0.0, zval, divr, diva, divz), [salt, graphite])
    W_chan_N_flat    = Pin(GCylMesh(radii,      hbp,  hbp+ccl,      0.0,     hfl, zval, divr, diva, divz), [salt, graphite])
    W_chan_S_flat    = Pin(GCylMesh(radii,      hbp,  hbp+ccl,     -hfl,     0.0, zval, divr, diva, divz), [salt, graphite])

    expected_map     = [[corner       , N_chan_W_cap, N_chan_W_flat, N_chan_E_flat, N_chan_E_cap, corner       ],
                        [W_chan_N_cap , corner      , H_spacer     , H_spacer     , corner      , E_chan_N_cap ],
                        [W_chan_N_flat, V_spacer    , center       , center       , V_spacer    , E_chan_N_flat],
                        [W_chan_S_flat, V_spacer    , center       , center       , V_spacer    , E_chan_S_flat],
                        [W_chan_S_cap , corner      , H_spacer     , H_spacer     , corner      , E_chan_S_cap ],
                        [corner       , S_chan_W_cap, S_chan_W_flat, S_chan_E_flat, S_chan_E_cap, corner       ]]

    assert core.modules[0].pin_map == expected_map
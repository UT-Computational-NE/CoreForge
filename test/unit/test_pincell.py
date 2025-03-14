import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose

from mpactpy import Model
from coreforge.shapes import Circle, Square, Hexagon, Stadium
from coreforge.geometry_elements import PinCell, CylindricalPincell
from test.unit.test_materials import msre_salt as salt, graphite

@pytest.fixture
def pincell(salt, graphite):
    zones = [PinCell.Zone(shape = Circle(r=1.),          material = salt),
             PinCell.Zone(shape = Square(s=4.),          material = graphite, rotation = 45.),
             PinCell.Zone(shape = Hexagon(r=8.),         material = salt),
             PinCell.Zone(shape = Stadium(r=12., a=20.), material = graphite, rotation = 90.)]
    return PinCell(zones = zones, outer_material = salt, origin = (1., -2.))

@pytest.fixture
def unequal_pincell(salt, graphite):
    zones = [PinCell.Zone(shape = Circle(r=1.),          material = salt),
             PinCell.Zone(shape = Stadium(r=12., a=20.), material = graphite, rotation = 90.)]
    return PinCell(zones = zones, outer_material = salt, origin = (1., -2.))

@pytest.fixture
def cylindrical_pincell(salt, graphite):
    target_cell_thicknesses = {'radial': 0.5, 'azimuthal': 2.3}
    bounds                  = (-4.0, 4.0, -4.0, 4.0)

    mpact_build_specs = CylindricalPincell.MPACTBuildSpecs(target_cell_thicknesses = target_cell_thicknesses,
                                                           bounds                  = bounds)

    return CylindricalPincell(radii             = [  1.,       2.,   3.          ],
                              materials         = [salt, graphite, salt, graphite],
                              mpact_build_specs = mpact_build_specs)

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
    assert_allclose(geom_element.origin, [1., -2.])

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
    assert universe.cells[2].fill.name == "Salt"
    assert universe.cells[3].fill.name == "Graphite"
    assert universe.cells[4].fill.name == "Salt"
    assert universe.cells[5].fill.name == "Graphite"
    assert universe.cells[6].fill.name == "Salt"

def test_pincell_make_mpact_core(pincell):
    geom_element = pincell
    with pytest.raises(NotImplementedError,
        match="Cannot make an MPACT Core for a generic pincell"):
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
    assert_allclose(geom_element.origin, [0., 0.])

def test_cylindrical_pincell_make_mpact_core(cylindrical_pincell):

    geom_element = cylindrical_pincell
    model  = Model(core = geom_element.make_mpact_core(), states = [], xsec_settings = {}, options = {})
    output = model.write_to_string(caseid="test", indent=2)
    expected_output = \
"""CASEID test

MATERIAL
  mat 1 9 2.3275 g/cc 900.0 K \\
    4009 0.00898964129413786
    9019 0.05218107467967278
    3006 1.7431446223252428e-06
    3007 0.02988796955594127
    92234 4.115361955751947e-07
    92235 4.604270687345431e-05
    92236 2.1089771252934387e-07
    92238 9.891360788333172e-05
    40090 0.00047974094545786845
    40091 0.00010461989131267802
    40092 0.00015991364848595618
    40094 0.00016205826301375617
    40096 2.6108350773217338e-05
  mat 2 0 1.8599999999999999 g/cc 900.0 K \\
    5010 1.642700833205197e-08
    5011 6.645396206175213e-08
    6001 0.0932567267810358


GEOM
  mod_dim 8.0 8.0 1.0

  pinmesh 1 gcyl 0.5 1.0 1.5 2.0 2.5 3.0 / -4.0 4.0 -4.0 4.0 / 1.0 / 1 1 1 1 1 1 / 8 8 8 8 8 8 8 / 1

  pin 1 1 / 1 1 2 2 1 1 2

  module 1 1 1 1
    1

  lattice 1 1 1
    1

  assembly 1
    1

  core 360
    1

XSEC

OPTION

"""
    assert output == expected_output

    mpact_build_specs = deepcopy(geom_element.mpact_build_specs)
    mpact_build_specs.divide_into_quadrants = True
    geom_element.mpact_build_specs = mpact_build_specs

    model  = Model(core = geom_element.make_mpact_core(), states = [], xsec_settings = {}, options = {})
    output = model.write_to_string(caseid="test", indent=2)
    expected_output = \
"""CASEID test

MATERIAL
  mat 1 9 2.3275 g/cc 900.0 K \\
    4009 0.00898964129413786
    9019 0.05218107467967278
    3006 1.7431446223252428e-06
    3007 0.02988796955594127
    92234 4.115361955751947e-07
    92235 4.604270687345431e-05
    92236 2.1089771252934387e-07
    92238 9.891360788333172e-05
    40090 0.00047974094545786845
    40091 0.00010461989131267802
    40092 0.00015991364848595618
    40094 0.00016205826301375617
    40096 2.6108350773217338e-05
  mat 2 0 1.8599999999999999 g/cc 900.0 K \\
    5010 1.642700833205197e-08
    5011 6.645396206175213e-08
    6001 0.0932567267810358


GEOM
  mod_dim 4.0 4.0 1.0

  pinmesh 1 gcyl 0.5 1.0 1.5 2.0 2.5 3.0 / -4.0 0.0 0.0 4.0 / 1.0 / 1 1 1 1 1 1 / 8 8 8 8 8 8 8 / 1
  pinmesh 2 gcyl 0.5 1.0 1.5 2.0 2.5 3.0 / 0.0 4.0 0.0 4.0 / 1.0 / 1 1 1 1 1 1 / 8 8 8 8 8 8 8 / 1
  pinmesh 3 gcyl 0.5 1.0 1.5 2.0 2.5 3.0 / -4.0 0.0 -4.0 0.0 / 1.0 / 1 1 1 1 1 1 / 8 8 8 8 8 8 8 / 1
  pinmesh 4 gcyl 0.5 1.0 1.5 2.0 2.5 3.0 / 0.0 4.0 -4.0 0.0 / 1.0 / 1 1 1 1 1 1 / 8 8 8 8 8 8 8 / 1

  pin 1 1 / 1 1 2 2 1 1 2
  pin 2 2 / 1 1 2 2 1 1 2
  pin 3 3 / 1 1 2 2 1 1 2
  pin 4 4 / 1 1 2 2 1 1 2

  module 1 1 1 1
    1
  module 2 1 1 1
    2
  module 3 1 1 1
    3
  module 4 1 1 1
    4

  lattice 1 2 2
    1 2
    3 4

  assembly 1
    1

  core 360
    1

XSEC

OPTION

"""
    assert output == expected_output


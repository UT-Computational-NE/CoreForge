import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose

from coreforge.geometry_elements import Stack
from test.unit.test_materials import graphite
from test.unit.msre.test_materials import salt
from test.unit.test_pincell import cylindrical_pincell as pincell

@pytest.fixture
def stack(pincell):
    return Stack([Stack.Segment(element=pincell, length=3.0),
                  Stack.Segment(element=pincell, length=1.0),
                  Stack.Segment(element=pincell, length=4.0)])

@pytest.fixture
def unequal_stack(pincell):
    return Stack([Stack.Segment(element=pincell, length=4.0),
                  Stack.Segment(element=pincell, length=4.0)])

def test_stack_initialization(stack, pincell):
    geom_element = stack
    assert geom_element.name == "stack"
    assert isclose(geom_element.bottom_pos, 0.0)
    assert isclose(geom_element.length, 8.0)
    assert len(geom_element.segments) == 3
    assert isclose(geom_element.segments[0].length, 3.0)
    assert isclose(geom_element.segments[1].length, 1.0)
    assert isclose(geom_element.segments[2].length, 4.0)
    assert geom_element.segments[0].element == pincell
    assert geom_element.segments[1].element == pincell
    assert geom_element.segments[2].element == pincell

def test_equality(stack, unequal_stack):
    assert stack == deepcopy(stack)
    assert stack != unequal_stack

def test_hash(stack, unequal_stack):
    assert hash(stack) == hash(deepcopy(stack))
    assert hash(stack) != hash(unequal_stack)

def test_make_openmc_universe(stack):
    geom_element = stack
    universe = geom_element.make_openmc_universe()
    assert universe.name == "stack"
    assert len(universe.cells) == 3
    for cell in universe.cells.values():
        assert cell.fill.name == "pincell"

def test_make_mpact_core(stack):
    geom_element = stack
    core         = geom_element.make_mpact_core()

    assert isclose(core.mod_dim['X'], 8.0)
    assert isclose(core.mod_dim['Y'], 8.0)
    assert_allclose(core.mod_dim['Z'], [1.0, 3.0, 4.0])
    assert core.nz == 3
    assert isclose(core.height, 8.0)

    assert len(core.pins)       == 3
    assert len(core.modules)    == 3
    assert len(core.lattices)   == 3
    assert len(core.assemblies) == 1

    assembly = core.assemblies[0]
    assert len(assembly.lattice_map) == 3
    assert isclose(assembly.lattice_map[0].pitch['Z'], 3.0)
    assert isclose(assembly.lattice_map[1].pitch['Z'], 1.0)
    assert isclose(assembly.lattice_map[2].pitch['Z'], 4.0)

    geom_element = Stack(name = "bad_stack", segments = [Stack.Segment(element=stack, length=8.0)])
    expected_assertion = "Unsupported Geometry! Stack: bad_stack Segment 0: stack is not a 2D radial geometry"
    with pytest.raises(AssertionError, match=expected_assertion):
        core = geom_element.make_mpact_core()

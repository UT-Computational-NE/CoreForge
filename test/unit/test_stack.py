import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose

from coreforge.geometry_elements import Stack
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from test.unit.test_materials import graphite
from test.unit.msre.test_materials import salt
from test.unit.test_pincell import cylindrical_pincell as pincell, \
                                   cylindrical_pincell_mpact_specs as pincell_mpact_specs

@pytest.fixture
def stack(pincell):
    return Stack([Stack.Segment(element=pincell, length=3.0),
                  Stack.Segment(element=pincell, length=1.0),
                  Stack.Segment(element=pincell, length=4.0)])

@pytest.fixture
def unequal_stack(pincell):
    return Stack([Stack.Segment(element=pincell, length=4.0),
                  Stack.Segment(element=pincell, length=4.0)])

@pytest.fixture
def stack_mpact_specs(stack, unequal_stack, pincell_mpact_specs):
    segment_specs = mpact_builder.Stack.Segment.Specs(builder_specs=pincell_mpact_specs)
    return mpact_builder.Stack.Specs({stack.segments[0]:         segment_specs,
                                      stack.segments[1]:         segment_specs,
                                      stack.segments[2]:         segment_specs,
                                      unequal_stack.segments[0]: segment_specs})



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

def test_openmc_builder(stack):
    geom_element = stack
    universe = openmc_builder.build(geom_element)
    assert universe.name == "stack"
    assert len(universe.cells) == 3
    for cell in universe.cells.values():
        assert cell.fill.name == "pincell"

def test_mpact_builder(stack, stack_mpact_specs):
    geom_element  = stack
    bounds        = mpact_builder.Bounds(X={'min': -4.0, 'max': 4.0},
                                         Y={'min': -4.0, 'max': 4.0})
    core          = mpact_builder.build(geom_element, stack_mpact_specs, bounds)

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
        core = mpact_builder.build(geom_element)

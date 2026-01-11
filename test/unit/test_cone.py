import pytest
from copy import deepcopy
from math import isclose, sqrt

from coreforge.geometry_elements import CylindricalPinCell, OneSidedCone
from coreforge.shapes import OneSidedCone as OneSidedConeShape

import coreforge.openmc_builder as openmc_builder

from test.unit.test_materials import air, graphite, water


cone_r = 5.0
cone_h = 10.0


def _segment_radius(segment) -> float:
    assert isinstance(segment.element, CylindricalPinCell)
    assert len(segment.element.zones) == 1
    return segment.element.zones[0].shape.outer_radius


@pytest.fixture
def cone(graphite, air):
    return OneSidedCone(r=cone_r, h=cone_h, name="cone", fill_material=graphite, outer_material=air)


@pytest.fixture
def unequal_cone(graphite, water):
    return OneSidedCone(r=cone_r, h=cone_h, name="cone", fill_material=graphite, outer_material=water)


def test_initialization(cone, graphite, air):
    geom_element = cone
    assert geom_element.name == "cone"
    assert isclose(geom_element.r, cone_r)
    assert isclose(geom_element.h, cone_h)
    assert geom_element.fill_material == graphite
    assert geom_element.outer_material == air

    shape = OneSidedConeShape(r=2.0, h=3.0)
    geom_element = OneSidedCone(cone=shape, name="cone", fill_material=graphite, outer_material=air)
    assert isclose(geom_element.r, 2.0)
    assert isclose(geom_element.h, 3.0)


def test_equality_and_hash(cone, unequal_cone):
    assert cone == deepcopy(cone)
    assert cone != unequal_cone
    assert hash(cone) == hash(deepcopy(cone))
    assert hash(cone) != hash(unequal_cone)


def test_as_stack(cone):
    # n => equal-height segments
    stack = cone.as_stack(stack_options=OneSidedCone.StackOptions(n=4), direction="up")
    assert stack.name == "cone"
    assert isclose(stack.length, cone_h)
    assert len(stack.segments) == 4
    assert all(isclose(seg.length, cone_h / 4.0) for seg in stack.segments)

    radii = [_segment_radius(seg) for seg in stack.segments]
    assert radii[0] > radii[1] > radii[2] > radii[3]

    # target_axial_length => choose smallest n such that dz <= target
    stack = cone.as_stack(stack_options=OneSidedCone.StackOptions(target_axial_length=3.0))
    # ceil(10/3)=4 => dz=2.5
    assert len(stack.segments) == 4
    assert all(seg.length <= 3.0 + 1e-12 for seg in stack.segments)
    assert isclose(sum(seg.length for seg in stack.segments), cone_h)

    # segment_lengths => explicit thicknesses
    stack = cone.as_stack(stack_options=OneSidedCone.StackOptions(segment_lengths=[2.0, 3.0, 5.0]))
    assert [seg.length for seg in stack.segments] == [2.0, 3.0, 5.0]
    assert isclose(sum(seg.length for seg in stack.segments), cone_h)

    # direction ordering
    up = cone.as_stack(stack_options=OneSidedCone.StackOptions(n=4), direction="up")
    down = cone.as_stack(stack_options=OneSidedCone.StackOptions(n=4), direction="down")
    assert [_segment_radius(seg) for seg in down.segments] == list(
        reversed([_segment_radius(seg) for seg in up.segments])
    )

    # volume-preserving check (first slice)
    stack = cone.as_stack(stack_options=OneSidedCone.StackOptions(n=3))
    radii = [_segment_radius(seg) for seg in stack.segments]
    dz = cone_h / 3.0
    z0, z1 = 0.0, dz
    r0 = cone_r * (1.0 - z0 / cone_h)
    r1 = cone_r * (1.0 - z1 / cone_h)
    expected = sqrt((r0 * r0 + r0 * r1 + r1 * r1) / 3.0)
    assert isclose(radii[0], expected)


def test_openmc_builder(cone, graphite, air):
    universe = openmc_builder.build(cone)
    assert universe.name == "cone"
    assert len(universe.cells) == 2

    fills = sorted([cell.fill.name for cell in universe.cells.values()])
    assert fills == sorted([graphite.name, air.name])

from copy import deepcopy
from math import isclose

import pytest

from coreforge.geometry_elements import CylindricalPinCell, CylindricalStack, Stack
from coreforge.geometry_elements.triga.netl import PNT
from coreforge.materials import Air, Al6061T6, Cd, Water, unique_materials
import coreforge.mpact_builder as mpact_builder
import coreforge.openmc_builder as openmc_builder

CM_PER_INCH = 2.54
MODEL_TOP = 80.0
PNT_BOTTOM_POS = -13.06 * CM_PER_INCH - 1.25 * CM_PER_INCH
TUBE_BOTTOM_POS = -18.7182
UPPER_GRID_PLATE_TOP = 12.75 * CM_PER_INCH


@pytest.fixture
def pnt():
    aluminum = Al6061T6()
    cadmium = Cd()
    ignored_outer_material = Water()

    def solid_section(radius, material, name):
        return CylindricalPinCell(
            radii=[radius],
            materials=[material, ignored_outer_material],
            name=name,
        )

    narrow_radius = 0.5 * 1.250 * CM_PER_INCH
    wide_radius = 0.5 * 1.435 * CM_PER_INCH
    terminus = CylindricalStack(
        segments=[
            Stack.Segment(solid_section(wide_radius, aluminum, "lower_section"), 8.3259),
            Stack.Segment(solid_section(narrow_radius, aluminum, "terminus_connecting_tube"), 4.1725),
            Stack.Segment(solid_section(wide_radius, aluminum, "shock_absorber_lower"), 2.5400),
            Stack.Segment(solid_section(wide_radius, cadmium, "cadmium_disk"), 0.0508),
            Stack.Segment(solid_section(narrow_radius, aluminum, "shock_absorber_upper"), 2.5400),
        ],
        name="terminus",
    )

    tube = PNT.Tube(
        inner_radius=0.5 * 0.685 * CM_PER_INCH,
        outer_radius=0.5 * 0.875 * CM_PER_INCH,
        length=MODEL_TOP - TUBE_BOTTOM_POS,
    )

    cross_section = CylindricalPinCell(
        radii=[
            0.5 * 0.955 * CM_PER_INCH,
            0.5 * 1.120 * CM_PER_INCH,
            0.5 * 1.250 * CM_PER_INCH,
        ],
        materials=[Cd(), Air(), Al6061T6(), Water()],
        name="wrapper_cross_section",
    )
    wrapper = PNT.Wrapper(
        length=UPPER_GRID_PLATE_TOP - TUBE_BOTTOM_POS,
        cross_section=cross_section,
    )

    return PNT(tube=tube, terminus=terminus, bottom_pos=PNT_BOTTOM_POS, wrapper=wrapper)


def test_initialization(pnt):
    pincell = pnt.pincell
    assert pnt.length == pytest.approx(MODEL_TOP - PNT_BOTTOM_POS)
    assert pnt.bottom_pos == pytest.approx(PNT_BOTTOM_POS)
    assert pnt.tube.length == pytest.approx(MODEL_TOP - TUBE_BOTTOM_POS)
    assert pnt.wrapper is not None
    assert pnt.wrapper.length == pytest.approx(UPPER_GRID_PLATE_TOP - TUBE_BOTTOM_POS)
    assert isinstance(pnt.outer_material, Water)
    assert all(isinstance(segment.element.outer_material, Water)
               for segment in pnt.terminus.segments)

    tube_radii = [zone.shape.outer_radius for zone in pincell["tube"].zones]
    tube_materials = [zone.material for zone in pincell["tube"].zones]
    assert tube_radii == pytest.approx([0.5 * 0.685 * CM_PER_INCH,
                                        0.5 * 0.875 * CM_PER_INCH])
    assert isinstance(tube_materials[0], Air)
    assert isinstance(tube_materials[1], Al6061T6)
    assert isinstance(pincell["tube"].outer_material, Water)

    wrapped_tube = pincell["wrapped_tube"]
    assert wrapped_tube is not None
    wrapped_radii = [zone.shape.outer_radius for zone in wrapped_tube.zones]
    wrapped_materials = [zone.material for zone in wrapped_tube.zones]
    assert wrapped_radii == pytest.approx([
        0.5 * 0.685 * CM_PER_INCH,
        0.5 * 0.875 * CM_PER_INCH,
        0.5 * 0.955 * CM_PER_INCH,
        0.5 * 1.120 * CM_PER_INCH,
        0.5 * 1.250 * CM_PER_INCH,
    ])
    assert wrapped_materials == [
        pnt.tube.fill_material,
        pnt.tube.material,
        *[zone.material for zone in pnt.wrapper.cross_section.zones],
    ]
    assert isinstance(wrapped_tube.outer_material, Water)

    expected_materials = list(pnt.terminus.get_materials())
    expected_materials.extend([
        pnt.tube.fill_material,
        pnt.tube.material,
        *[zone.material for zone in pnt.wrapper.cross_section.zones],
        pnt.outer_material,
    ])
    assert pnt.get_materials() == unique_materials(expected_materials)


def test_equality_and_hash(pnt):
    assert pnt.wrapper is not None
    unequal_wrapper = PNT.Wrapper(
        length=pnt.wrapper.length * 0.9,
        cross_section=pnt.wrapper.cross_section,
    )
    unequal_pnt = PNT(
        tube=pnt.tube,
        terminus=pnt.terminus,
        bottom_pos=pnt.bottom_pos,
        wrapper=unequal_wrapper,
    )
    relocated_pnt = PNT(
        tube=pnt.tube,
        terminus=pnt.terminus,
        bottom_pos=pnt.bottom_pos - 1.0,
        wrapper=pnt.wrapper,
    )

    assert pnt == deepcopy(pnt)
    assert pnt != unequal_pnt
    assert pnt != relocated_pnt
    assert hash(pnt) == hash(deepcopy(pnt))
    assert hash(pnt) != hash(unequal_pnt)
    assert hash(pnt) != hash(relocated_pnt)


def test_as_stack(pnt):
    stack = pnt.as_stack()

    assert stack.bottom_pos == pytest.approx(PNT_BOTTOM_POS)
    assert stack.length == pytest.approx(pnt.length)
    assert len(stack.segments) == len(pnt.terminus.segments) + 2
    assert [segment.length for segment in stack.segments] == pytest.approx([
        8.3259,
        4.1725,
        2.5400,
        0.0508,
        2.5400,
        UPPER_GRID_PLATE_TOP - TUBE_BOTTOM_POS,
        MODEL_TOP - UPPER_GRID_PLATE_TOP,
    ])
    assert stack.segments[-2].element == pnt.pincell["wrapped_tube"]
    assert stack.segments[-1].element == pnt.pincell["tube"]


def test_as_stack_without_wrapper(pnt):
    unwrapped_pnt = PNT(tube=pnt.tube, terminus=pnt.terminus)
    stack = unwrapped_pnt.as_stack()

    assert unwrapped_pnt.pincell["wrapped_tube"] is None
    assert len(stack.segments) == len(pnt.terminus.segments) + 1
    assert isclose(stack.segments[-1].length, pnt.tube.length)
    assert stack.segments[-1].element == unwrapped_pnt.pincell["tube"]


def test_as_stack_with_full_length_wrapper(pnt):
    assert pnt.wrapper is not None
    full_wrapper = PNT.Wrapper(
        length=pnt.tube.length,
        cross_section=pnt.wrapper.cross_section,
    )
    fully_wrapped_pnt = PNT(
        tube=pnt.tube,
        terminus=pnt.terminus,
        wrapper=full_wrapper,
    )
    stack = fully_wrapped_pnt.as_stack()

    assert len(stack.segments) == len(pnt.terminus.segments) + 1
    assert stack.segments[-1].element == fully_wrapped_pnt.pincell["wrapped_tube"]
    assert stack.segments[-1].length == pytest.approx(pnt.tube.length)


def test_openmc_builder(pnt):
    universe = openmc_builder.build(pnt)
    assert universe.name == pnt.name
    assert len(universe.cells) == len(pnt.as_stack().segments)


def test_mpact_builder(pnt):
    stack = pnt.as_stack()
    builder_cls = mpact_builder.get_builder(pnt)

    assert builder_cls is mpact_builder.triga.netl.PNT

    built_stack, stack_specs = builder_cls().build_stack_and_specs(pnt)
    assert built_stack == stack
    assert set(stack_specs.segment_specs) == set(stack.segments)

    core = mpact_builder.build(pnt)
    assert core.nz == len(stack.segments)
    assert isclose(core.height, pnt.length)


def test_invalid_geometry(pnt):
    assert pnt.wrapper is not None
    with pytest.raises(AssertionError, match="must not exceed"):
        too_long = PNT.Wrapper(
            length=pnt.tube.length + 1.0,
            cross_section=pnt.wrapper.cross_section,
        )
        PNT(tube=pnt.tube, terminus=pnt.terminus, wrapper=too_long)

    too_narrow_cross_section = CylindricalPinCell(
        radii=[pnt.tube.outer_radius, 0.5 * 1.120 * CM_PER_INCH],
        materials=[Cd(), Al6061T6(), Water()],
    )
    with pytest.raises(AssertionError, match="innermost radius must exceed"):
        too_narrow = PNT.Wrapper(
            length=pnt.wrapper.length,
            cross_section=too_narrow_cross_section,
        )
        PNT(tube=pnt.tube, terminus=pnt.terminus, wrapper=too_narrow)

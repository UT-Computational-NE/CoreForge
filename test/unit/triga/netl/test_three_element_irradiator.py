from copy import deepcopy
from math import isclose

import pytest

from coreforge.geometry_elements.triga.netl import ThreeElementIrradiator
from coreforge.materials import Air, Al6061T6, Cd, Water, unique_materials
import coreforge.mpact_builder as mpact_builder
import coreforge.openmc_builder as openmc_builder


@pytest.fixture
def three_element_irradiator():
    outer_casing = ThreeElementIrradiator.OuterCasing(
        inner_radius=2.23393,
        outer_radius=2.38125,
        length=127.9524,
        solid_upper_end_thickness=3.1750,
        solid_lower_end_thickness=2.5399,
    )
    inner_sleeve = ThreeElementIrradiator.InnerSleeve(
        inner_radius=1.93929,
        outer_radius=2.06375,
        sidewall_length=119.6975,
        bottom_thickness=0.3175,
    )
    liner = ThreeElementIrradiator.Liner(
        thickness=0.10160,
        sidewall_length=118.1100,
        bottom_thickness=0.1016,
        material=Cd(),
    )
    return ThreeElementIrradiator(
        outer_casing=outer_casing,
        inner_sleeve=inner_sleeve,
        liner=liner,
        fill_material=Air(),
        outer_material=Water(),
    )


@pytest.fixture
def unequal_three_element_irradiator(three_element_irradiator):
    liner = ThreeElementIrradiator.Liner(
        thickness=0.0508,
        sidewall_length=three_element_irradiator.liner.sidewall_length,
        bottom_thickness=three_element_irradiator.liner.bottom_thickness,
        material=three_element_irradiator.liner.material,
    )
    return ThreeElementIrradiator(
        outer_casing=three_element_irradiator.outer_casing,
        inner_sleeve=three_element_irradiator.inner_sleeve,
        liner=liner,
        fill_material=three_element_irradiator.fill_material,
        outer_material=three_element_irradiator.outer_material,
    )


def assert_pincell(pincell, radii, material_types):
    assert [zone.shape.outer_radius for zone in pincell.zones] == pytest.approx(radii)
    assert [type(zone.material) for zone in pincell.zones] == material_types
    assert isinstance(pincell.outer_material, Water)


def test_initialization(three_element_irradiator):
    irradiator = three_element_irradiator
    pincell = irradiator.pincell
    casing = irradiator.outer_casing
    sleeve = irradiator.inner_sleeve
    liner = irradiator.liner
    liner_outer_radius = sleeve.outer_radius + liner.thickness

    assert irradiator.length == pytest.approx(casing.length)
    assert isinstance(casing.material, Al6061T6)
    assert isinstance(sleeve.material, Al6061T6)
    assert isinstance(liner.material, Cd)
    assert isinstance(irradiator.fill_material, Air)
    assert isinstance(irradiator.outer_material, Water)

    assert_pincell(
        pincell["solid_end"],
        [casing.outer_radius],
        [Al6061T6],
    )
    assert_pincell(
        pincell["liner_bottom"],
        [liner_outer_radius, casing.inner_radius, casing.outer_radius],
        [Cd, Air, Al6061T6],
    )
    assert_pincell(
        pincell["inner_sleeve_bottom"],
        [sleeve.outer_radius, liner_outer_radius, casing.inner_radius, casing.outer_radius],
        [Al6061T6, Cd, Air, Al6061T6],
    )
    assert_pincell(
        pincell["lined"],
        [sleeve.inner_radius, sleeve.outer_radius, liner_outer_radius,
         casing.inner_radius, casing.outer_radius],
        [Air, Al6061T6, Cd, Air, Al6061T6],
    )
    assert_pincell(
        pincell["inner_sleeve"],
        [sleeve.inner_radius, sleeve.outer_radius, casing.inner_radius, casing.outer_radius],
        [Air, Al6061T6, Air, Al6061T6],
    )
    assert_pincell(
        pincell["outer_casing"],
        [casing.inner_radius, casing.outer_radius],
        [Air, Al6061T6],
    )

    expected_materials = unique_materials([
        casing.material,
        sleeve.material,
        liner.material,
        irradiator.fill_material,
        irradiator.outer_material,
    ])
    assert irradiator.get_materials() == expected_materials


def test_equality_and_hash(three_element_irradiator, unequal_three_element_irradiator):
    assert three_element_irradiator == deepcopy(three_element_irradiator)
    assert three_element_irradiator != unequal_three_element_irradiator
    assert hash(three_element_irradiator) == hash(deepcopy(three_element_irradiator))
    assert hash(three_element_irradiator) != hash(unequal_three_element_irradiator)


def test_as_stack(three_element_irradiator):
    irradiator = three_element_irradiator
    pincell = irradiator.pincell
    stack = irradiator.as_stack()

    assert stack.bottom_pos == pytest.approx(0.0)
    assert stack.length == pytest.approx(irradiator.length)
    assert len(stack.segments) == 7
    assert [segment.length for segment in stack.segments] == pytest.approx([
        2.5399,
        0.1016,
        0.3175,
        117.7925,
        1.9050,
        2.1209,
        3.1750,
    ])
    assert [segment.element for segment in stack.segments] == [
        pincell["solid_end"],
        pincell["liner_bottom"],
        pincell["inner_sleeve_bottom"],
        pincell["lined"],
        pincell["inner_sleeve"],
        pincell["outer_casing"],
        pincell["solid_end"],
    ]


def test_openmc_builder(three_element_irradiator):
    universe = openmc_builder.build(three_element_irradiator)
    assert universe.name == three_element_irradiator.name
    assert len(universe.cells) == len(three_element_irradiator.as_stack().segments)


def test_mpact_builder(three_element_irradiator):
    stack = three_element_irradiator.as_stack()
    builder_cls = mpact_builder.get_builder(three_element_irradiator)

    assert builder_cls is mpact_builder.triga.netl.ThreeElementIrradiator

    built_stack, stack_specs = builder_cls().build_stack_and_specs(three_element_irradiator)
    assert built_stack == stack
    assert set(stack_specs.segment_specs) == set(stack.segments)

    core = mpact_builder.build(three_element_irradiator)
    expected_xy = 2.0 * three_element_irradiator.outer_casing.outer_radius
    assert isclose(core.mod_dim["X"], expected_xy)
    assert isclose(core.mod_dim["Y"], expected_xy)
    assert core.nz == len(stack.segments)
    assert isclose(core.height, three_element_irradiator.length)


def test_invalid_geometry(three_element_irradiator):
    thick_liner = ThreeElementIrradiator.Liner(
        thickness=1.0,
        sidewall_length=three_element_irradiator.liner.sidewall_length,
        bottom_thickness=three_element_irradiator.liner.bottom_thickness,
        material=three_element_irradiator.liner.material,
    )
    with pytest.raises(AssertionError, match="inside the outer casing"):
        ThreeElementIrradiator(
            outer_casing=three_element_irradiator.outer_casing,
            inner_sleeve=three_element_irradiator.inner_sleeve,
            liner=thick_liner,
        )

    short_liner = ThreeElementIrradiator.Liner(
        thickness=three_element_irradiator.liner.thickness,
        sidewall_length=0.1,
        bottom_thickness=three_element_irradiator.liner.bottom_thickness,
        material=three_element_irradiator.liner.material,
    )
    with pytest.raises(AssertionError, match="extend above the inner sleeve bottom"):
        ThreeElementIrradiator(
            outer_casing=three_element_irradiator.outer_casing,
            inner_sleeve=three_element_irradiator.inner_sleeve,
            liner=short_liner,
        )

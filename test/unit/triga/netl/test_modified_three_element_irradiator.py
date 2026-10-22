from copy import deepcopy
from dataclasses import replace

import openmc
import pytest

from coreforge.geometry_elements.triga.netl import ModifiedThreeElementIrradiator
from coreforge.materials import Air, Al6061T6, B4C, Cd, Material, Water, unique_materials
import coreforge.mpact_builder as mpact_builder
import coreforge.openmc_builder as openmc_builder


def make_elemental_material(name, nuclide):
    openmc_material = openmc.Material(name=name)
    openmc_material.set_density("g/cm3", 1.0)
    openmc_material.add_nuclide(nuclide, 1.0)
    return Material(openmc_material)


@pytest.fixture
def modified_three_element_irradiator():
    outer_casing = ModifiedThreeElementIrradiator.OuterCasing(
        tube_1_inner_radius=2.23393,
        tube_1_outer_radius=2.30759,
        tube_1_length=124.77400,
        tube_2_outer_radius=2.38125,
        tube_2_annulus_length=81.27660,
        tube_2_end_cap_thickness=3.39830,
    )
    pneumatic_system = ModifiedThreeElementIrradiator.PneumaticSystem(
        tube_inner_radius=0.67000,
        tube_outer_radius=0.79400,
        sleeve_inner_radius=0.86350,
        sleeve_outer_radius=0.95250,
        open_tube_length=109.73188,
        tube_lower_end_cap_thickness=0.12400,
        sleeve_lower_end_cap_thickness=0.12850,
    )
    b4c_canister = ModifiedThreeElementIrradiator.B4CCanister(
        b4c_region_inner_radius=1.11125,
        b4c_region_outer_radius=1.89230,
        canister_outer_radius=2.19009,
        top_cap_thickness=0.19660,
        b4c_region_thickness=52.00278,
        bottom_cap_thickness=0.20000,
        b4c_material=B4C(name="natural_b4c"),
    )
    b10_canister = ModifiedThreeElementIrradiator.B10Canister(
        b10_annulus_inner_radius=1.03759,
        upper_b10_outer_radius=2.00660,
        lower_b10_outer_radius=2.04724,
        canister_exterior_wall_radius=2.12090,
        cadmium_sleeve_outer_radius=2.17090,
        gap_to_b4c_canister=0.10000,
        top_cap_thickness=2.54000,
        upper_b10_region_thickness=22.86000,
        lower_b10_region_thickness=34.92500,
        exterior_wall_lower_end_cap_thickness=0.63500,
        lower_b10_solid_section_thickness=2.54000,
        b10_material=make_elemental_material("enriched_boron", "B10"),
    )
    return ModifiedThreeElementIrradiator(
        outer_casing=outer_casing,
        pneumatic_system=pneumatic_system,
        b4c_canister=b4c_canister,
        b10_canister=b10_canister,
        silver_disk=ModifiedThreeElementIrradiator.Disk(
            thickness=0.10000,
            material=make_elemental_material("silver", "Ag107"),
        ),
        cadmium_disk=ModifiedThreeElementIrradiator.Disk(
            thickness=0.10000,
            material=Cd(),
        ),
        hollow_spacer=ModifiedThreeElementIrradiator.HollowSpacer(
            hollow_section_radius=2.03393,
            hollow_section_thickness=3.00000,
            solid_upper_cap_thickness=0.49472,
        ),
        solid_spacer=ModifiedThreeElementIrradiator.SolidSpacer(
            thickness=5.08000,
        ),
        fill_material=Air(),
        outer_material=Water(),
    )


@pytest.fixture
def unequal_modified_three_element_irradiator(modified_three_element_irradiator):
    irradiator = modified_three_element_irradiator
    return ModifiedThreeElementIrradiator(
        outer_casing=irradiator.outer_casing,
        pneumatic_system=irradiator.pneumatic_system,
        b4c_canister=irradiator.b4c_canister,
        b10_canister=irradiator.b10_canister,
        silver_disk=irradiator.silver_disk,
        cadmium_disk=irradiator.cadmium_disk,
        hollow_spacer=irradiator.hollow_spacer,
        solid_spacer=replace(irradiator.solid_spacer, thickness=4.0),
        fill_material=irradiator.fill_material,
        outer_material=irradiator.outer_material,
    )


def make_simplified(irradiator):
    return ModifiedThreeElementIrradiator(
        outer_casing=irradiator.outer_casing,
        pneumatic_system=irradiator.pneumatic_system,
        b4c_canister=irradiator.b4c_canister,
        b10_canister=irradiator.b10_canister,
        silver_disk=irradiator.silver_disk,
        cadmium_disk=irradiator.cadmium_disk,
        hollow_spacer=irradiator.hollow_spacer,
        solid_spacer=irradiator.solid_spacer,
        fill_material=irradiator.fill_material,
        outer_material=irradiator.outer_material,
        gap_tolerance=irradiator.gap_tolerance,
        simplified=True,
    )


def test_initialization(modified_three_element_irradiator):
    irradiator = modified_three_element_irradiator
    casing = irradiator.outer_casing
    pneumatic = irradiator.pneumatic_system
    b4c = irradiator.b4c_canister
    b10 = irradiator.b10_canister
    pincell = irradiator.pincell
    lengths = irradiator.axial_region_lengths

    expected_region_lengths = {
        "bottom_air": [2.53990],
        "solid_spacer": [5.08000],
        "hollow_spacer": [3.00000],
        "hollow_spacer_upper_cap": [0.49472],
        "cadmium_disk": [0.10000],
        "silver_disk": [0.10000],
        "b10_canister_lower_end_cap": [0.63500],
        "lower_b10_solid_section": [2.54000],
        "b10_interior_wall_lower_cap": [0.30000],
        "pneumatic_sleeve_lower_cap": [0.12850],
        "pneumatic_tube_lower_cap": [0.12400],
        "lower_b10_region": [28.45528, 3.37722],
        "upper_b10_region": [22.86000],
        "b10_canister_top_cap": [2.54000],
        "inter_canister_gap": [0.10000],
        "b4c_canister_bottom_cap": [0.20000],
        "b4c_region": [52.00278],
        "b4c_canister_top_cap": [0.19660],
        "outer_casing_solid_upper_end": [3.39830],
    }

    assert irradiator.length == pytest.approx(128.17230)
    assert list(pincell) == list(expected_region_lengths)
    assert list(lengths) == list(expected_region_lengths)
    for name, expected_lengths in expected_region_lengths.items():
        assert lengths[name] == pytest.approx(expected_lengths)
        assert len(pincell[name]) == len(expected_lengths)

    tube_1 = [casing.tube_1_inner_radius, casing.tube_1_outer_radius]
    tube_2 = [*tube_1, casing.tube_2_outer_radius]
    open_pneumatic = [
        pneumatic.tube_inner_radius,
        pneumatic.tube_outer_radius,
        pneumatic.sleeve_inner_radius,
        pneumatic.sleeve_outer_radius,
    ]
    lower_b10 = [
        *open_pneumatic,
        b10.b10_annulus_inner_radius,
        b10.lower_b10_outer_radius,
        b10.canister_exterior_wall_radius,
        b10.cadmium_sleeve_outer_radius,
    ]
    upper_b10 = [
        *open_pneumatic,
        b10.b10_annulus_inner_radius,
        b10.upper_b10_outer_radius,
        b10.canister_exterior_wall_radius,
        b10.cadmium_sleeve_outer_radius,
    ]
    expected_radii = {
        "bottom_air": [tube_1],
        "solid_spacer": [tube_1],
        "hollow_spacer": [[
            irradiator.hollow_spacer.hollow_section_radius,
            *tube_1,
        ]],
        "hollow_spacer_upper_cap": [tube_1],
        "cadmium_disk": [tube_1],
        "silver_disk": [tube_1],
        "b10_canister_lower_end_cap": [[
            b10.canister_exterior_wall_radius,
            *tube_1,
        ]],
        "lower_b10_solid_section": [[
            b10.lower_b10_outer_radius,
            b10.canister_exterior_wall_radius,
            b10.cadmium_sleeve_outer_radius,
            *tube_1,
        ]],
        "b10_interior_wall_lower_cap": [[
            b10.b10_annulus_inner_radius,
            b10.lower_b10_outer_radius,
            b10.canister_exterior_wall_radius,
            b10.cadmium_sleeve_outer_radius,
            *tube_1,
        ]],
        "pneumatic_sleeve_lower_cap": [[
            pneumatic.sleeve_outer_radius,
            b10.b10_annulus_inner_radius,
            b10.lower_b10_outer_radius,
            b10.canister_exterior_wall_radius,
            b10.cadmium_sleeve_outer_radius,
            *tube_1,
        ]],
        "pneumatic_tube_lower_cap": [[
            pneumatic.tube_outer_radius,
            pneumatic.sleeve_inner_radius,
            pneumatic.sleeve_outer_radius,
            b10.b10_annulus_inner_radius,
            b10.lower_b10_outer_radius,
            b10.canister_exterior_wall_radius,
            b10.cadmium_sleeve_outer_radius,
            *tube_1,
        ]],
        "lower_b10_region": [[*lower_b10, *tube_1], [*lower_b10, *tube_2]],
        "upper_b10_region": [[*upper_b10, *tube_2]],
        "b10_canister_top_cap": [[
            *open_pneumatic,
            b10.canister_exterior_wall_radius,
            b10.cadmium_sleeve_outer_radius,
            *tube_2,
        ]],
        "inter_canister_gap": [[*open_pneumatic, *tube_2]],
        "b4c_canister_bottom_cap": [[
            *open_pneumatic,
            b4c.canister_outer_radius,
            *tube_2,
        ]],
        "b4c_region": [[
            *open_pneumatic,
            b4c.b4c_region_inner_radius,
            b4c.b4c_region_outer_radius,
            b4c.canister_outer_radius,
            *tube_2,
        ]],
        "b4c_canister_top_cap": [[
            *open_pneumatic,
            b4c.canister_outer_radius,
            *tube_2,
        ]],
        "outer_casing_solid_upper_end": [[casing.tube_2_outer_radius]],
    }
    for name, region_expected_radii in expected_radii.items():
        assert len(pincell[name]) == len(region_expected_radii)
        for pin, expected_pin_radii in zip(pincell[name], region_expected_radii):
            assert [zone.shape.outer_radius for zone in pin.zones] == pytest.approx(
                expected_pin_radii
            )
            assert isinstance(pin.outer_material, Water)

    assert isinstance(casing.material, Al6061T6)
    assert isinstance(pneumatic.material, Al6061T6)
    assert isinstance(pneumatic.fill_material, Air)
    assert isinstance(b10.cadmium_sleeve_material, Cd)
    assert isinstance(irradiator.fill_material, Air)
    assert isinstance(irradiator.outer_material, Water)

    expected_materials = unique_materials([
        casing.material,
        irradiator.pneumatic_system.material,
        irradiator.pneumatic_system.fill_material,
        irradiator.b4c_canister.b4c_material,
        irradiator.b4c_canister.canister_material,
        irradiator.b10_canister.b10_material,
        irradiator.b10_canister.canister_material,
        irradiator.b10_canister.cadmium_sleeve_material,
        irradiator.silver_disk.material,
        irradiator.cadmium_disk.material,
        irradiator.hollow_spacer.material,
        irradiator.hollow_spacer.fill_material,
        irradiator.solid_spacer.material,
        irradiator.fill_material,
        irradiator.outer_material,
    ])
    assert irradiator.get_materials() == expected_materials


def test_equality_and_hash(
    modified_three_element_irradiator,
    unequal_modified_three_element_irradiator,
):
    irradiator = modified_three_element_irradiator
    unequal_irradiator = unequal_modified_three_element_irradiator

    assert irradiator == deepcopy(irradiator)
    assert irradiator != unequal_irradiator
    assert hash(irradiator) == hash(deepcopy(irradiator))
    assert hash(irradiator) != hash(unequal_irradiator)


def test_as_stack(modified_three_element_irradiator):
    irradiator = modified_three_element_irradiator
    stack = irradiator.as_stack(bottom_pos=-10.0)
    expected_pincells = [
        pin
        for region_pincells in irradiator.pincell.values()
        for pin in region_pincells
    ]
    expected_lengths = [
        length
        for region_lengths in irradiator.axial_region_lengths.values()
        for length in region_lengths
    ]

    assert stack.bottom_pos == pytest.approx(-10.0)
    assert stack.length == pytest.approx(irradiator.length)
    assert len(stack.segments) == 20
    assert [segment.length for segment in stack.segments] == pytest.approx(expected_lengths)
    assert [segment.element for segment in stack.segments] == expected_pincells


def test_simplified_geometry(modified_three_element_irradiator):
    detailed = modified_three_element_irradiator
    irradiator = make_simplified(detailed)
    stack = irradiator.as_stack(bottom_pos=-10.0)

    expected_lengths = {
        "bottom_air": [2.53990],
        "solid_spacer": [5.08000],
        "hollow_spacer": [3.49472],
        "cadmium_disk": [0.10000],
        "silver_disk": [0.10000],
        "lower_b10_solid_section": [3.17500],
        "lower_b10_region": [55.24500],
        "b10_canister_top_cap": [2.64000],
        "b4c_region": [52.39938],
        "outer_casing_solid_upper_end": [3.39830],
    }
    assert irradiator.simplified
    assert irradiator != detailed
    assert list(irradiator.pincell) == list(expected_lengths)
    for name, expected_region_lengths in expected_lengths.items():
        assert irradiator.axial_region_lengths[name] == pytest.approx(
            expected_region_lengths
        )
    assert stack.bottom_pos == pytest.approx(-10.0)
    assert stack.length == pytest.approx(irradiator.length)
    assert len(stack.segments) == 10
    assert len(irradiator.as_detailed_stack().segments) == 20
    assert len(irradiator.as_simplified_stack().segments) == 10

    expected_radii = {
        "bottom_air": [2.23393, 2.35651],
        "solid_spacer": [2.23393, 2.35651],
        "hollow_spacer": [1.88448, 2.23393, 2.35651],
        "cadmium_disk": [2.23393, 2.35651],
        "silver_disk": [2.23393, 2.35651],
        "lower_b10_solid_section": [
            2.02019, 2.11951, 2.16895, 2.23393, 2.35651,
        ],
        "lower_b10_region": [
            0.67015, 0.79400, 0.86182, 0.95250, 1.03759,
            2.02019, 2.11951, 2.16895, 2.23393, 2.35651,
        ],
        "b10_canister_top_cap": [
            0.67015, 0.79400, 0.86182, 0.95250,
            2.11951, 2.16895, 2.23393, 2.35651,
        ],
        "b4c_region": [
            0.67015, 0.79400, 0.86182, 0.95250,
            1.11125, 1.88760, 2.19009, 2.23393, 2.35651,
        ],
        "outer_casing_solid_upper_end": [2.35651],
    }
    for name, expected_region_radii in expected_radii.items():
        pincell = irradiator.pincell[name][0]
        radii = [zone.shape.outer_radius for zone in pincell.zones]
        assert radii == pytest.approx(expected_region_radii, abs=5.0e-6)

    universe = openmc_builder.build(irradiator)
    assert len(universe.cells) == 10
    built_stack, stack_specs = mpact_builder.get_builder(irradiator)().build_stack_and_specs(
        irradiator
    )
    assert len(built_stack.segments) == 10
    assert set(stack_specs.segment_specs) == set(built_stack.segments)


def test_openmc_builder(modified_three_element_irradiator):
    universe = openmc_builder.build(modified_three_element_irradiator)
    assert universe.name == modified_three_element_irradiator.name
    assert len(universe.cells) == len(modified_three_element_irradiator.as_stack().segments)


def test_mpact_builder(modified_three_element_irradiator):
    irradiator = modified_three_element_irradiator
    stack = irradiator.as_stack()
    builder_cls = mpact_builder.get_builder(irradiator)

    assert builder_cls is mpact_builder.triga.netl.ModifiedThreeElementIrradiator

    built_stack, stack_specs = builder_cls().build_stack_and_specs(irradiator)
    assert built_stack == stack
    assert set(stack_specs.segment_specs) == set(stack.segments)

    core = mpact_builder.build(irradiator)
    expected_xy = 2.0 * irradiator.outer_casing.tube_2_outer_radius
    assert core.mod_dim["X"] == pytest.approx(expected_xy)
    assert core.mod_dim["Y"] == pytest.approx(expected_xy)
    assert core.nz == len(stack.segments)
    assert core.height == pytest.approx(irradiator.length)


def test_tube_2_can_split_an_arbitrary_axial_feature(modified_three_element_irradiator):
    irradiator = modified_three_element_irradiator
    casing = replace(
        irradiator.outer_casing,
        tube_2_annulus_length=irradiator.outer_casing.tube_1_length - 1.0,
    )
    split_bottom_air_irradiator = ModifiedThreeElementIrradiator(
        outer_casing=casing,
        pneumatic_system=irradiator.pneumatic_system,
        b4c_canister=irradiator.b4c_canister,
        b10_canister=irradiator.b10_canister,
        silver_disk=irradiator.silver_disk,
        cadmium_disk=irradiator.cadmium_disk,
        hollow_spacer=irradiator.hollow_spacer,
        solid_spacer=irradiator.solid_spacer,
        fill_material=irradiator.fill_material,
        outer_material=irradiator.outer_material,
    )

    assert split_bottom_air_irradiator.axial_region_lengths["bottom_air"] == pytest.approx([
        1.0,
        1.5399,
    ])
    assert len(split_bottom_air_irradiator.pincell["bottom_air"]) == 2
    assert len(split_bottom_air_irradiator.pincell["lower_b10_region"]) == 1


def test_invalid_geometry(modified_three_element_irradiator):
    irradiator = modified_three_element_irradiator
    oversized_b4c_canister = replace(
        irradiator.b4c_canister,
        canister_outer_radius=irradiator.outer_casing.tube_1_inner_radius + 0.1,
    )

    with pytest.raises(AssertionError, match="fit inside Tube #1"):
        ModifiedThreeElementIrradiator(
            outer_casing=irradiator.outer_casing,
            pneumatic_system=irradiator.pneumatic_system,
            b4c_canister=oversized_b4c_canister,
            b10_canister=irradiator.b10_canister,
            silver_disk=irradiator.silver_disk,
            cadmium_disk=irradiator.cadmium_disk,
            hollow_spacer=irradiator.hollow_spacer,
            solid_spacer=irradiator.solid_spacer,
        )

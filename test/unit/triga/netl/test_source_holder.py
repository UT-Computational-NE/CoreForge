import pytest
from copy import deepcopy
from math import isclose

from coreforge.geometry_elements.triga.netl import SourceHolder
from coreforge.materials import Al6061T6, Air, Water, unique_materials
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder


CM_PER_INCH = 2.54


@pytest.fixture
def source_holder():
    upper_grid_plate_distance = 12.75 * CM_PER_INCH
    lower_grid_plate_distance = 13.06 * CM_PER_INCH
    distance_from_lower_plate = 1.1934
    upper_plate_thickness = 0.62 * CM_PER_INCH

    length = (
        upper_grid_plate_distance
        + lower_grid_plate_distance
        - distance_from_lower_plate
        + upper_plate_thickness
    )
    cavity = SourceHolder.Cavity(
        radius=0.981 * 0.5 * CM_PER_INCH,
        length=3.0 * CM_PER_INCH,
        axial_offset=-distance_from_lower_plate,
    )
    cladding = SourceHolder.Cladding(outer_radius=1.435 * 0.5 * CM_PER_INCH)
    return SourceHolder(
        length=length,
        cavity=cavity,
        cladding=cladding,
        outer_material=Water(),
        gap_tolerance=None,
    )


@pytest.fixture
def unequal_source_holder(source_holder):
    cavity = SourceHolder.Cavity(radius=source_holder.cavity.radius * 1.05,
                                 length=source_holder.cavity.length)
    cladding = source_holder.cladding
    return SourceHolder(length=source_holder.length,
                        cavity=cavity,
                        cladding=cladding,
                        outer_material=source_holder.outer_material)


def test_initialization(source_holder):
    cavity_pin = source_holder.cavity_pincell
    cavity_radii = [zone.shape.outer_radius for zone in cavity_pin.zones]
    cavity_mats = [zone.material for zone in cavity_pin.zones]

    assert cavity_radii == pytest.approx([
        source_holder.cavity.radius,
        source_holder.cladding.outer_radius,
    ])
    assert isinstance(cavity_mats[0], Air)
    assert isinstance(cavity_mats[1], Al6061T6)
    assert isinstance(cavity_pin.outer_material, Water)
    assert source_holder.cavity.axial_offset == pytest.approx(-1.1934)

    solid_pin = source_holder.solid_pincell
    solid_radii = [zone.shape.outer_radius for zone in solid_pin.zones]
    solid_mats = [zone.material for zone in solid_pin.zones]

    assert solid_radii == pytest.approx([source_holder.cladding.outer_radius])
    assert isinstance(solid_mats[0], Al6061T6)
    assert isinstance(solid_pin.outer_material, Water)
    expected = unique_materials([
        source_holder.cavity.material,
        source_holder.cladding.material,
        source_holder.outer_material,
    ])
    assert source_holder.get_materials() == expected


def test_equality_and_hash(source_holder, unequal_source_holder):
    assert source_holder == deepcopy(source_holder)
    assert source_holder != unequal_source_holder
    assert hash(source_holder) == hash(deepcopy(source_holder))
    assert hash(source_holder) != hash(unequal_source_holder)


def test_as_stack(source_holder):
    stack = source_holder.as_stack()
    assert len(stack.segments) == 3
    assert isclose(stack.length, source_holder.length)
    assert isclose(stack.bottom_pos, 0.0)


def test_openmc_builder(source_holder):
    geom_element = source_holder
    universe = openmc_builder.build(geom_element)
    assert universe.name == "source_holder"
    assert len(universe.cells) == 3


def test_mpact_builder(source_holder):
    geom_element = source_holder
    core = mpact_builder.build(geom_element)

    below_cavity_length = (source_holder.length / 2.0) + source_holder.cavity.axial_offset - (source_holder.cavity.length / 2.0)
    above_cavity_length = (source_holder.length / 2.0) - source_holder.cavity.axial_offset - (source_holder.cavity.length / 2.0)

    expected_xy = source_holder.cladding.outer_radius * 2.0
    assert isclose(core.mod_dim['X'], expected_xy)
    assert isclose(core.mod_dim['Y'], expected_xy)
    assert core.mod_dim['Z'] == [source_holder.cavity.length, below_cavity_length, above_cavity_length]
    assert core.nz == 3
    assert isclose(core.height, source_holder.length)

    assert len(core.pins)       == 3
    assert len(core.modules)    == 3
    assert len(core.lattices)   == 3
    assert len(core.assemblies) == 1

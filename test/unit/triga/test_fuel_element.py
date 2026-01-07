import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose

from coreforge.geometry_elements.triga import FuelElement
from coreforge.materials import Air, Graphite, SS304, UZrH, Water, Zr
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder

CM_PER_INCH = 2.54


@pytest.fixture
def fuel_element():
    zr = FuelElement.ZrFillRod(radius=0.25 * 0.5 * CM_PER_INCH)
    fuel = FuelElement.FuelMeat(
        inner_radius=0.25 * 0.5 * CM_PER_INCH,
        outer_radius=1.435 * 0.5 * CM_PER_INCH,
        length=15.0 * CM_PER_INCH,
    )
    clad = FuelElement.Cladding(
        thickness=0.020 * CM_PER_INCH,
        outer_radius=1.475 * 0.5 * CM_PER_INCH,
    )
    upper_reflector = FuelElement.GraphiteReflector(
        radius=1.430 * 0.5 * CM_PER_INCH,
        thickness=2.56 * CM_PER_INCH,
    )
    lower_reflector = FuelElement.GraphiteReflector(
        radius=1.430 * 0.5 * CM_PER_INCH,
        thickness=3.72 * CM_PER_INCH,
    )
    moly = FuelElement.MolyDisc(
        radius=1.431 * 0.5 * CM_PER_INCH,
        thickness=0.031 * CM_PER_INCH,
    )
    gap = FuelElement.AirGap(thickness=0.5 * CM_PER_INCH)
    upper_end = FuelElement.EndFitting(length=7.3552, r2=0.25, direction="up")
    lower_end = FuelElement.EndFitting(length=7.6209, r2=0.25, direction="down")

    return FuelElement(
        cladding=clad,
        fill_gas=Air(),
        outer_material=Water(),
        gap_tolerance=1e-8,
        upper_end_fitting=upper_end,
        upper_air_gap=gap,
        upper_graphite_reflector=upper_reflector,
        zr_fill_rod=zr,
        fuel_meat=fuel,
        moly_disc=moly,
        lower_graphite_reflector=lower_reflector,
        lower_end_fitting=lower_end,
    )


@pytest.fixture
def unequal_fuel_element(fuel_element):
    base = fuel_element
    return FuelElement(
        cladding=base.cladding,
        fill_gas=base.fill_gas,
        outer_material=base.outer_material,
        gap_tolerance=0.05,
        upper_end_fitting=base.upper_end_fitting,
        upper_air_gap=base.upper_air_gap,
        upper_graphite_reflector=base.upper_graphite_reflector,
        zr_fill_rod=base.zr_fill_rod,
        fuel_meat=base.fuel_meat,
        moly_disc=base.moly_disc,
        lower_graphite_reflector=base.lower_graphite_reflector,
        lower_end_fitting=base.lower_end_fitting,
    )


def test_initialization(fuel_element):
    pin = fuel_element.fuel_pincell
    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]
    assert radii == pytest.approx([
        fuel_element.zr_fill_rod.radius,
        fuel_element.fuel_meat.outer_radius,
        fuel_element.cladding.outer_radius,
    ])
    assert isinstance(materials[0], Zr)
    assert isinstance(materials[1], UZrH)
    assert isinstance(materials[2], SS304)
    assert isinstance(pin.outer_material, Water)

    moly_pin = fuel_element.moly_disc_pincell
    assert [z.shape.outer_radius for z in moly_pin.zones] == pytest.approx([
        fuel_element.moly_disc.radius,
        fuel_element.cladding.inner_radius,
        fuel_element.cladding.outer_radius,
    ])
    assert isinstance(moly_pin.zones[0].material, type(fuel_element.moly_disc.material))

    refl_pin = fuel_element.upper_reflector_pincell
    assert [z.shape.outer_radius for z in refl_pin.zones] == pytest.approx([
        fuel_element.upper_graphite_reflector.radius,
        fuel_element.cladding.inner_radius,
        fuel_element.cladding.outer_radius,
    ])
    assert isinstance(refl_pin.zones[0].material, Graphite)

    air_pin = fuel_element.air_gap_pincell
    assert [z.shape.outer_radius for z in air_pin.zones] == pytest.approx([
        fuel_element.cladding.inner_radius,
        fuel_element.cladding.outer_radius,
    ])
    assert isinstance(air_pin.zones[0].material, Air)

def test_equality_and_hash(fuel_element, unequal_fuel_element):
    assert fuel_element == deepcopy(fuel_element)
    assert fuel_element != unequal_fuel_element
    assert hash(fuel_element) == hash(deepcopy(fuel_element))
    assert hash(fuel_element) != hash(unequal_fuel_element)

def test_openmc_builder(fuel_element):
    geom_element = fuel_element
    universe = openmc_builder.build(geom_element)
    assert universe.name == "fuel_element"
    assert len(universe.cells) == 9

def test_mpact_builder(fuel_element):
    geom_element = fuel_element
    core = mpact_builder.build(geom_element)

    expected_xy = fuel_element.cladding.outer_radius * 2.0
    expected_z = sorted([fuel_element.lower_end_fitting.length,
                         fuel_element.lower_graphite_reflector.thickness,
                         fuel_element.moly_disc.thickness,
                         fuel_element.fuel_meat.length,
                         fuel_element.upper_graphite_reflector.thickness,
                         fuel_element.upper_air_gap.thickness,
                         fuel_element.upper_end_fitting.length,])
    expected_nz = len(expected_z)
    expected_height = sum(expected_z)

    assert isclose(core.mod_dim['X'], expected_xy)
    assert isclose(core.mod_dim['Y'], expected_xy)
    assert_allclose(core.mod_dim['Z'], expected_z)
    assert core.nz == expected_nz
    assert isclose(core.height, expected_height)

    assert len(core.pins)       == expected_nz
    assert len(core.modules)    == expected_nz
    assert len(core.lattices)   == expected_nz
    assert len(core.assemblies) == 1

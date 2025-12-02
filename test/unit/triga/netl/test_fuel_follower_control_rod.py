import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import FuelFollowerControlRod
from coreforge.materials import Air, B4C, SS304, UZrH, Water, Zr


@pytest.fixture
def control_rod():
    clad = FuelFollowerControlRod.Cladding(thickness=0.02, outer_radius=0.675)
    absorber = FuelFollowerControlRod.Absorber(radius=0.655)
    follower = FuelFollowerControlRod.FuelFollower(
        inner_radius=0.125,
        outer_radius=clad.inner_radius,
    )
    zr_fill = FuelFollowerControlRod.ZrFillRod(radius=0.125)
    plug = FuelFollowerControlRod.ElementPlug(thickness=1.0)
    mag = FuelFollowerControlRod.MagneformFitting(thickness=0.5)
    air_gap = FuelFollowerControlRod.AirGap(thickness=1.0)

    return FuelFollowerControlRod(
        cladding=clad,
        absorber=absorber,
        fuel_follower=follower,
        zr_fill_rod=zr_fill,
        upper_element_plug=plug,
        upper_air_gap=air_gap,
        upper_magneform_fitting=mag,
        above_absorber_air_gap=air_gap,
        middle_magneform_fitting=mag,
        above_fuel_follower_air_gap=air_gap,
        lower_magneform_fitting=mag,
        lower_air_gap=air_gap,
        lower_element_plug=plug,
        fill_gas=Air(),
        outer_material=Water(),
    )


@pytest.fixture
def unequal_control_rod(control_rod):
    clad = FuelFollowerControlRod.Cladding(thickness=0.03, outer_radius=0.70)
    absorber = FuelFollowerControlRod.Absorber(radius=0.50)
    follower = FuelFollowerControlRod.FuelFollower(
        inner_radius=0.20,
        outer_radius=clad.inner_radius,
    )
    zr_fill = FuelFollowerControlRod.ZrFillRod(radius=0.10)
    plug = FuelFollowerControlRod.ElementPlug(thickness=0.8)
    mag = FuelFollowerControlRod.MagneformFitting(thickness=0.4)
    air_gap = FuelFollowerControlRod.AirGap(thickness=0.8)

    return FuelFollowerControlRod(
        cladding=clad,
        absorber=absorber,
        fuel_follower=follower,
        zr_fill_rod=zr_fill,
        upper_element_plug=plug,
        upper_air_gap=air_gap,
        upper_magneform_fitting=mag,
        above_absorber_air_gap=air_gap,
        middle_magneform_fitting=mag,
        above_fuel_follower_air_gap=air_gap,
        lower_magneform_fitting=mag,
        lower_air_gap=air_gap,
        lower_element_plug=plug,
        fill_gas=Air(),
        outer_material=Water(),
        gap_tolerance=1e-8,
    )


def test_initialization(control_rod):
    abs_pin = control_rod.absorber_pincell
    abs_radii = [z.shape.outer_radius for z in abs_pin.zones]
    abs_mats = [z.material for z in abs_pin.zones]

    assert abs_radii == pytest.approx([control_rod.absorber.radius, control_rod.cladding.outer_radius])
    assert isinstance(abs_mats[0], B4C)
    assert isinstance(abs_mats[1], SS304)
    assert isinstance(abs_pin.outer_material, Water)

    follower_pin = control_rod.fuel_follower_pincell
    follower_radii = [z.shape.outer_radius for z in follower_pin.zones]
    follower_mats = [z.material for z in follower_pin.zones]

    assert follower_radii == pytest.approx([
        control_rod.zr_fill_rod.radius,
        control_rod.fuel_follower.outer_radius,
        control_rod.cladding.outer_radius,
    ])
    assert isinstance(follower_mats[0], Zr)
    assert isinstance(follower_mats[1], UZrH)
    assert isinstance(follower_mats[2], SS304)
    assert isinstance(follower_pin.outer_material, Water)

    upper_plug_pin = control_rod.upper_element_plug_pincell
    lower_plug_pin = control_rod.lower_element_plug_pincell
    for pin in (upper_plug_pin, lower_plug_pin):
        assert [z.shape.outer_radius for z in pin.zones] == pytest.approx([
            control_rod.cladding.inner_radius,
            control_rod.cladding.outer_radius,
        ])
        assert all(isinstance(m, SS304) for m in [pin.zones[0].material, pin.zones[1].material])

    upper_mag_pin = control_rod.upper_magneform_fitting_pincell
    middle_mag_pin = control_rod.middle_magneform_fitting_pincell
    lower_mag_pin = control_rod.lower_magneform_fitting_pincell
    for pin in (upper_mag_pin, middle_mag_pin, lower_mag_pin):
        assert [z.shape.outer_radius for z in pin.zones] == pytest.approx([
            control_rod.cladding.inner_radius,
            control_rod.cladding.outer_radius,
        ])
        assert all(isinstance(m, SS304) for m in [pin.zones[0].material, pin.zones[1].material])

    air_pin = control_rod.air_gap_pincell
    assert [z.shape.outer_radius for z in air_pin.zones] == pytest.approx([
        control_rod.cladding.inner_radius,
        control_rod.cladding.outer_radius,
    ])
    assert isinstance(air_pin.zones[0].material, Air)
    assert isinstance(air_pin.zones[1].material, SS304)
    assert isinstance(air_pin.outer_material, Water)


def test_equality_and_hash(control_rod, unequal_control_rod):
    assert control_rod == deepcopy(control_rod)
    assert control_rod != unequal_control_rod
    assert hash(control_rod) == hash(deepcopy(control_rod))
    assert hash(control_rod) != hash(unequal_control_rod)

import pytest

from coreforge.geometry_elements.triga.netl import FuelFollowerControlRod
from coreforge.materials import Air, B4C, SS304, UZrH, Water, Zr


@pytest.fixture
def default_cladding():
    return FuelFollowerControlRod.Cladding(thickness=0.02, outer_radius=0.675)


@pytest.fixture
def default_absorber():
    return FuelFollowerControlRod.Absorber(radius=0.655)


@pytest.fixture
def default_follower():
    clad = default_cladding()
    return FuelFollowerControlRod.FuelFollower(
        inner_radius=0.125,
        outer_radius=clad.outer_radius - clad.thickness
    )


@pytest.fixture
def default_zr_fill():
    return FuelFollowerControlRod.ZrFillRod(radius=0.10)


def test_absorber_zero_gap(default_cladding, default_absorber):
    pin = FuelFollowerControlRod.AbsorberPincell(
        cladding=default_cladding,
        absorber=default_absorber,
        fill_gas=Air(),
        outer_material=Water(),
    )

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([default_absorber.radius, default_cladding.outer_radius])
    assert isinstance(materials[0], B4C)
    assert isinstance(materials[1], SS304)
    assert isinstance(pin.outer_material, Water)


def test_absorber_with_gap():
    cladding = FuelFollowerControlRod.Cladding(thickness=0.05, outer_radius=1.0)
    absorber = FuelFollowerControlRod.Absorber(radius=0.5)

    pin = FuelFollowerControlRod.AbsorberPincell(
        cladding=cladding,
        absorber=absorber,
        fill_gas=Air(),
    )

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([0.5, 0.95, 1.0])
    assert isinstance(materials[0], B4C)
    assert isinstance(materials[1], Air)
    assert isinstance(materials[2], SS304)


def test_follower_with_gap():
    cladding = FuelFollowerControlRod.Cladding(thickness=0.05, outer_radius=1.0)
    follower = FuelFollowerControlRod.FuelFollower(inner_radius=0.6, outer_radius=0.8)
    zr_fill = FuelFollowerControlRod.ZrFillRod(radius=0.5)

    pin = FuelFollowerControlRod.FuelFollowerPincell(
        cladding=cladding,
        fuel_follower=follower,
        zr_fill_rod=zr_fill,
        fill_gas=Air(),
        outer_material=Water(),
    )

    cladding_inner = cladding.outer_radius - cladding.thickness
    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([0.5, 0.6, 0.8, cladding_inner, cladding.outer_radius])
    assert isinstance(materials[0], Zr)
    assert isinstance(materials[1], Air)
    assert isinstance(materials[2], UZrH)
    assert isinstance(materials[3], Air)
    assert isinstance(materials[4], SS304)
    assert isinstance(pin.outer_material, Water)


def test_follower_no_gap():
    cladding = FuelFollowerControlRod.Cladding(thickness=0.5, outer_radius=1.0)  # inner radius = 0.5
    zr_fill = FuelFollowerControlRod.ZrFillRod(radius=0.49)
    follower = FuelFollowerControlRod.FuelFollower(inner_radius=0.49, outer_radius=0.5)

    pin = FuelFollowerControlRod.FuelFollowerPincell(
        cladding=cladding,
        fuel_follower=follower,
        zr_fill_rod=zr_fill,
        fill_gas=Air(),
    )

    cladding_inner = cladding.outer_radius - cladding.thickness
    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert cladding_inner == pytest.approx(0.5)
    assert radii == pytest.approx([0.49, 0.5, cladding.outer_radius])
    assert isinstance(materials[0], Zr)
    assert isinstance(materials[1], UZrH)
    assert isinstance(materials[2], SS304)

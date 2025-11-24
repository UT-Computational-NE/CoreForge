import pytest

from coreforge.geometry_elements.triga import FuelElementPincell
from coreforge.materials import Air, SS304, UZrH, Water, Zr


CM_PER_INCH = 2.54


@pytest.fixture
def default_features():
    zr   = FuelElementPincell.ZrFillRod(radius = 0.25 * 0.5 * CM_PER_INCH)
    fuel = FuelElementPincell.FuelMeat(inner_radius = 0.25 * 0.5 * CM_PER_INCH,
                                       outer_radius = 1.435 * 0.5 * CM_PER_INCH)
    clad = FuelElementPincell.Cladding(thickness    = 0.020 * CM_PER_INCH,
                                       outer_radius = 1.475 * 0.5 * CM_PER_INCH,)
    return zr, fuel, clad


def test_zero_gap_profile(default_features):
    zr, fuel, clad = default_features
    pin = FuelElementPincell(cladding       = clad,
                             fuel_meat      = fuel,
                             zr_fill_rod    = zr,
                             fill_gas       = Air(),
                             outer_material = Water())

    expected_radii = [zr.radius,
                      fuel.outer_radius,
                      clad.outer_radius]

    assert len(pin.zones) == 3
    assert [zone.shape.outer_radius for zone in pin.zones] == pytest.approx(expected_radii)
    assert isinstance(pin.zones[0].material, Zr)
    assert isinstance(pin.zones[1].material, UZrH)
    assert isinstance(pin.zones[2].material, SS304)
    assert isinstance(pin.outer_material, Water)


def test_gaps_included_when_above_tol():
    zr   = FuelElementPincell.ZrFillRod(radius=0.10)
    fuel = FuelElementPincell.FuelMeat(inner_radius=0.15, outer_radius=0.50)
    clad = FuelElementPincell.Cladding(thickness=0.10, outer_radius=0.80)

    pin = FuelElementPincell(cladding       = clad,
                             fuel_meat      = fuel,
                             zr_fill_rod    = zr,
                             fill_gas       = Air(),
                             outer_material = Water())

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([0.10, 0.15, 0.50, 0.70, 0.80])
    assert isinstance(materials[0], Zr)
    assert isinstance(materials[1], Air)
    assert isinstance(materials[2], UZrH)
    assert isinstance(materials[3], Air)
    assert isinstance(materials[4], SS304)
    assert isinstance(pin.outer_material, Water)

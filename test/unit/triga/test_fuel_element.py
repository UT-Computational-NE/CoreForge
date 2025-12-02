import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga import FuelElement
from coreforge.materials import Air, Graphite, SS304, UZrH, Water, Zr


@pytest.fixture
def fuel_element():
    """Fuel element with gaps retained (very small tolerance)."""
    zr = FuelElement.ZrFillRod(radius=0.10)
    fuel = FuelElement.FuelMeat(inner_radius=0.12, outer_radius=0.50, length=10.0)
    clad = FuelElement.Cladding(thickness=0.10, outer_radius=0.70)
    upper_reflector = FuelElement.GraphiteReflector(radius=0.50, thickness=5.0)
    lower_reflector = FuelElement.GraphiteReflector(radius=0.50, thickness=5.0)
    moly = FuelElement.MolyDisc(radius=0.40, thickness=0.20)
    gap = FuelElement.AirGap(thickness=0.50)
    upper_end = FuelElement.EndFitting(length=3.0, direction="up")
    lower_end = FuelElement.EndFitting(length=3.0, direction="down")

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
    """Fuel element with higher tolerance to collapse small gaps."""
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


def test_fuel_element_initialization(fuel_element):
    pin = fuel_element.fuel_pincell
    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]
    assert radii == pytest.approx([0.10, 0.12, 0.50, 0.60, 0.70])
    assert isinstance(materials[0], Zr)
    assert isinstance(materials[1], Air)
    assert isinstance(materials[2], UZrH)
    assert isinstance(materials[3], Air)
    assert isinstance(materials[4], SS304)
    assert isinstance(pin.outer_material, Water)

    moly_pin = fuel_element.moly_disc_pincell
    assert [z.shape.outer_radius for z in moly_pin.zones] == pytest.approx([0.40, 0.60, 0.70])
    assert isinstance(moly_pin.zones[0].material, type(fuel_element.moly_disc.material))

    refl_pin = fuel_element.upper_reflector_pincell
    assert [z.shape.outer_radius for z in refl_pin.zones] == pytest.approx([0.50, 0.60, 0.70])
    assert isinstance(refl_pin.zones[0].material, Graphite)

    air_pin = fuel_element.air_gap_pincell
    assert [z.shape.outer_radius for z in air_pin.zones] == pytest.approx([0.60, 0.70])
    assert isinstance(air_pin.zones[0].material, Air)

def test_equality_and_hash(fuel_element, unequal_fuel_element):
    assert fuel_element == deepcopy(fuel_element)
    assert fuel_element != unequal_fuel_element
    assert hash(fuel_element) == hash(deepcopy(fuel_element))
    assert hash(fuel_element) != hash(unequal_fuel_element)

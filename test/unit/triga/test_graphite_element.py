import pytest

from coreforge.geometry_elements.triga import GraphiteElement
from coreforge.materials import Air, Al6061T6, Graphite, Water


CM_PER_INCH = 2.54


@pytest.fixture
def default_features():
    meat = GraphiteElement.GraphiteMeat(
        outer_radius=1.435 * 0.5 * CM_PER_INCH,
    )
    clad = GraphiteElement.Cladding(
        thickness=0.020 * CM_PER_INCH,
        outer_radius=1.475 * 0.5 * CM_PER_INCH,
    )
    return meat, clad


def test_zero_gap_profile(default_features):
    meat, clad = default_features
    pin = GraphiteElement.Pincell(
        cladding=clad,
        graphite_meat=meat,
        fill_gas=Air(),
        outer_material=Water(),
    )

    expected_radii = [
        meat.outer_radius,
        clad.outer_radius,
    ]
    expected_materials = [
        isinstance(pin.zones[0].material, Graphite),
        isinstance(pin.zones[1].material, Al6061T6),
    ]

    assert len(pin.zones) == 2
    assert [zone.shape.outer_radius for zone in pin.zones] == expected_radii
    assert all(expected_materials)
    assert isinstance(pin.outer_material, Water)


def test_gaps_included_when_above_tol():
    meat = GraphiteElement.GraphiteMeat(outer_radius=0.50)
    clad = GraphiteElement.Cladding(thickness=0.05, outer_radius=0.80)

    pin = GraphiteElement.Pincell(
        cladding=clad,
        graphite_meat=meat,
        fill_gas=Air(),
        outer_material=Water(),
    )

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([0.50, 0.75, 0.80])
    assert isinstance(materials[0], Graphite)
    assert isinstance(materials[1], Air)
    assert isinstance(materials[2], Al6061T6)
    assert isinstance(pin.outer_material, Water)

import pytest

from coreforge.geometry_elements.triga.netl import TransientRod
from coreforge.materials import Air, Al6061T6, B4C, Water


@pytest.fixture
def default_cladding():
    # 0.028 in, 0.625 in -> inner radius ~0.597 in; values here are arbitrary test units.
    return TransientRod.Cladding(thickness=0.028, outer_radius=0.625)


@pytest.fixture
def default_absorber():
    # Match the cladding inner radius (0.625 - 0.028) to avoid a gap.
    return TransientRod.Absorber(radius=0.597)


def test_absorber_zero_gap(default_cladding, default_absorber):
    cladding = default_cladding
    absorber = default_absorber
    pin = TransientRod.AbsorberPincell(
        cladding=cladding,
        absorber=absorber,
        fill_gas=Air(),
        outer_material=Water(),
    )

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([absorber.radius, cladding.outer_radius])
    assert isinstance(materials[0], B4C)
    assert isinstance(materials[1], Al6061T6)
    assert isinstance(pin.outer_material, Water)


def test_absorber_with_gap(default_cladding):
    cladding = TransientRod.Cladding(thickness=0.05, outer_radius=1.0)
    absorber = TransientRod.Absorber(radius=0.5)

    pin = TransientRod.AbsorberPincell(cladding=cladding, absorber=absorber, fill_gas=Air())

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([0.5, 0.95, 1.0])
    assert isinstance(materials[0], B4C)
    assert isinstance(materials[1], Air)
    assert isinstance(materials[2], Al6061T6)


def test_air_follower(default_cladding):
    cladding = default_cladding
    pin = TransientRod.AirFollowerPincell(
        cladding=cladding,
        fill_gas=Air(),
        outer_material=Water(),
    )

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    cladding_inner = cladding.outer_radius - cladding.thickness
    assert radii == pytest.approx([cladding_inner, cladding.outer_radius])
    assert isinstance(materials[0], Air)
    assert isinstance(materials[1], Al6061T6)
    assert isinstance(pin.outer_material, Water)

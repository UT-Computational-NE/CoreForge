import pytest

from coreforge.geometry_elements.triga.netl import SourceHolder
from coreforge.materials import Al6061T6, Air, Water


CM_PER_INCH = 2.54


@pytest.fixture
def default_features():
    cavity = SourceHolder.Cavity(radius=0.981 * 0.5 * CM_PER_INCH)
    cladding = SourceHolder.Cladding(outer_radius=1.435 * 0.5 * CM_PER_INCH)
    return cavity, cladding


def test_zero_gap_profile(default_features):
    cavity, cladding = default_features
    pin = SourceHolder.Pincell(
        cavity=cavity,
        cladding=cladding,
        outer_material=Water(),
    )

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([
        cavity.radius,
        cladding.outer_radius,
    ])
    assert isinstance(materials[0], Air)
    assert isinstance(materials[1], Al6061T6)
    assert isinstance(pin.outer_material, Water)

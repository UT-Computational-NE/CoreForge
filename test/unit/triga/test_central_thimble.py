import pytest

from coreforge.geometry_elements.triga.netl import CentralThimble
from coreforge.materials import Al6061T6, Water


@pytest.fixture
def default_cladding():
    return CentralThimble.Cladding(inner_radius=1.0, outer_radius=1.5)


def test_thimble_profile(default_cladding):
    pin = CentralThimble.Pincell(
        cladding=default_cladding,
        fill_material=Water(),
        outer_material=Water(),
    )

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([1.0, 1.5])
    assert isinstance(materials[0], Water)
    assert isinstance(materials[1], Al6061T6)
    assert isinstance(pin.outer_material, Water)

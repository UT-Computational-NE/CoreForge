import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import CentralThimble
from coreforge.materials import Al6061T6, Water


@pytest.fixture
def central_thimble():
    clad = CentralThimble.Cladding(thickness=0.20, outer_radius=1.50)
    return CentralThimble(cladding=clad, fill_material=Water(), outer_material=Water())


@pytest.fixture
def unequal_thimble():
    clad = CentralThimble.Cladding(thickness=0.25, outer_radius=1.55)
    return CentralThimble(cladding=clad, fill_material=Water(), outer_material=Water())


def test_initialization(central_thimble):
    pin = central_thimble.thimble_pincell

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([1.30, 1.50])
    assert isinstance(materials[0], Water)
    assert isinstance(materials[1], Al6061T6)
    assert isinstance(pin.outer_material, Water)


def test_equality_and_hash(central_thimble, unequal_thimble):
    assert central_thimble == deepcopy(central_thimble)
    assert central_thimble != unequal_thimble
    assert hash(central_thimble) == hash(deepcopy(central_thimble))
    assert hash(central_thimble) != hash(unequal_thimble)

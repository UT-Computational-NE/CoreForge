import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import SourceHolder
from coreforge.materials import Al6061T6, Air, Water


CM_PER_INCH = 2.54


@pytest.fixture
def source_holder():
    cavity = SourceHolder.Cavity(radius=0.981 * 0.5 * CM_PER_INCH)
    cladding = SourceHolder.Cladding(outer_radius=1.435 * 0.5 * CM_PER_INCH)
    return SourceHolder(cavity=cavity, cladding=cladding, outer_material=Water())


@pytest.fixture
def unequal_source_holder(source_holder):
    cavity = SourceHolder.Cavity(radius=source_holder.cavity.radius * 1.05)
    cladding = source_holder.cladding
    return SourceHolder(cavity=cavity, cladding=cladding, outer_material=source_holder.outer_material)


def test_cavity_pincell(source_holder):
    pin = source_holder.cavity_pincell

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([
        source_holder.cavity.radius,
        source_holder.cladding.outer_radius,
    ])
    assert isinstance(materials[0], Air)
    assert isinstance(materials[1], Al6061T6)
    assert isinstance(pin.outer_material, Water)


def test_solid_pincell(source_holder):
    pin = source_holder.solid_pincell

    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([source_holder.cladding.outer_radius])
    assert isinstance(materials[0], Al6061T6)
    assert isinstance(pin.outer_material, Water)


def test_equality_and_hash(source_holder, unequal_source_holder):
    assert source_holder == deepcopy(source_holder)
    assert source_holder != unequal_source_holder
    assert hash(source_holder) == hash(deepcopy(source_holder))
    assert hash(source_holder) != hash(unequal_source_holder)

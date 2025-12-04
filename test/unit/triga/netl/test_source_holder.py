import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import SourceHolder
from coreforge.materials import Al6061T6, Air, Water


CM_PER_INCH = 2.54


@pytest.fixture
def source_holder():
    cavity = SourceHolder.Cavity(radius=0.981 * 0.5 * CM_PER_INCH,
                                 length=3.0 * CM_PER_INCH)
    cladding = SourceHolder.Cladding(outer_radius=1.435 * 0.5 * CM_PER_INCH)
    return SourceHolder(length=20.0 * CM_PER_INCH,
                        cavity=cavity,
                        cladding=cladding,
                        outer_material=Water())


@pytest.fixture
def unequal_source_holder(source_holder):
    cavity = SourceHolder.Cavity(radius=source_holder.cavity.radius * 1.05,
                                 length=source_holder.cavity.length)
    cladding = source_holder.cladding
    return SourceHolder(length=source_holder.length,
                        cavity=cavity,
                        cladding=cladding,
                        outer_material=source_holder.outer_material)


def test_initialization(source_holder):
    cavity_pin = source_holder.cavity_pincell
    cavity_radii = [zone.shape.outer_radius for zone in cavity_pin.zones]
    cavity_mats = [zone.material for zone in cavity_pin.zones]

    assert cavity_radii == pytest.approx([
        source_holder.cavity.radius,
        source_holder.cladding.outer_radius,
    ])
    assert isinstance(cavity_mats[0], Air)
    assert isinstance(cavity_mats[1], Al6061T6)
    assert isinstance(cavity_pin.outer_material, Water)

    solid_pin = source_holder.solid_pincell
    solid_radii = [zone.shape.outer_radius for zone in solid_pin.zones]
    solid_mats = [zone.material for zone in solid_pin.zones]

    assert solid_radii == pytest.approx([source_holder.cladding.outer_radius])
    assert isinstance(solid_mats[0], Al6061T6)
    assert isinstance(solid_pin.outer_material, Water)


def test_equality_and_hash(source_holder, unequal_source_holder):
    assert source_holder == deepcopy(source_holder)
    assert source_holder != unequal_source_holder
    assert hash(source_holder) == hash(deepcopy(source_holder))
    assert hash(source_holder) != hash(unequal_source_holder)

import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import TransientRod
from coreforge.materials import Air, Al6061T6, B4C, Water


@pytest.fixture
def transient_rod():
    cladding = TransientRod.Cladding(thickness=0.028, outer_radius=0.625)
    absorber = TransientRod.Absorber(radius=0.595)
    air_follower = TransientRod.AirFollower(thickness=1.0)
    element_plug = TransientRod.ElementPlug(thickness=0.50)
    magneform = TransientRod.MagneformFitting(thickness=1.0)
    return TransientRod(
        cladding=cladding,
        absorber=absorber,
        air_follower=air_follower,
        upper_element_plug=element_plug,
        upper_magneform_fitting=magneform,
        lower_magneform_fitting=magneform,
        lower_element_plug=element_plug,
        fill_gas=Air(),
        outer_material=Water()
    )


@pytest.fixture
def unequal_transient_rod(transient_rod):
    cladding = TransientRod.Cladding(thickness=0.05, outer_radius=1.0)
    absorber = TransientRod.Absorber(radius=0.5)
    air_follower = TransientRod.AirFollower(thickness=2.0)
    element_plug = TransientRod.ElementPlug(thickness=0.75)
    magneform = TransientRod.MagneformFitting(thickness=1.25)
    return TransientRod(
        cladding=cladding,
        absorber=absorber,
        air_follower=air_follower,
        upper_element_plug=element_plug,
        upper_magneform_fitting=magneform,
        lower_magneform_fitting=magneform,
        lower_element_plug=element_plug,
        fill_gas=Air(),
        outer_material=Water(),
    )


def test_initialization(transient_rod):
    absorber_pin = transient_rod.absorber_pincell
    radii = [zone.shape.outer_radius for zone in absorber_pin.zones]
    materials = [zone.material for zone in absorber_pin.zones]

    assert radii == pytest.approx([transient_rod.absorber.radius,
                                   transient_rod.cladding.inner_radius,
                                   transient_rod.cladding.outer_radius])
    assert isinstance(materials[0], B4C)
    assert isinstance(materials[1], Air)
    assert isinstance(materials[2], Al6061T6)
    assert isinstance(absorber_pin.outer_material, Water)

    air_pin = transient_rod.air_follower_pincell
    air_radii = [zone.shape.outer_radius for zone in air_pin.zones]
    air_materials = [zone.material for zone in air_pin.zones]

    assert air_radii == pytest.approx([transient_rod.cladding.inner_radius,
                                       transient_rod.cladding.outer_radius])
    assert isinstance(air_materials[0], Air)
    assert isinstance(air_materials[1], Al6061T6)
    assert isinstance(air_pin.outer_material, Water)

    for plug_pin in (transient_rod.upper_element_plug_pincell,
                     transient_rod.lower_element_plug_pincell):
        plug_radii = [zone.shape.outer_radius for zone in plug_pin.zones]
        plug_materials = [zone.material for zone in plug_pin.zones]
        assert plug_radii == pytest.approx([transient_rod.cladding.inner_radius,
                                            transient_rod.cladding.outer_radius])
        assert isinstance(plug_materials[0], Al6061T6)
        assert isinstance(plug_materials[1], Al6061T6)
        assert isinstance(plug_pin.outer_material, Water)

    for mag_pin in (transient_rod.upper_magneform_fitting_pincell,
                    transient_rod.lower_magneform_fitting_pincell):
        mag_radii = [zone.shape.outer_radius for zone in mag_pin.zones]
        mag_materials = [zone.material for zone in mag_pin.zones]
        assert mag_radii == pytest.approx([transient_rod.cladding.inner_radius,
                                           transient_rod.cladding.outer_radius])
        assert isinstance(mag_materials[0], Al6061T6)
        assert isinstance(mag_materials[1], Al6061T6)
        assert isinstance(mag_pin.outer_material, Water)


def test_equality_and_hash(transient_rod, unequal_transient_rod):
    assert transient_rod == deepcopy(transient_rod)
    assert transient_rod != unequal_transient_rod
    assert hash(transient_rod) == hash(deepcopy(transient_rod))
    assert hash(transient_rod) != hash(unequal_transient_rod)

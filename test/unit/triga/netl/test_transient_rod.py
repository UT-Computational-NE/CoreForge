from math import isclose
import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import TransientRod
from coreforge.materials import Air, Al6061T6, B4C, Water
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder

CM_PER_INCH = 2.54


@pytest.fixture
def transient_rod():
    cladding = TransientRod.Cladding(
        thickness=0.028 * CM_PER_INCH,
        outer_radius=1.25 * 0.5 * CM_PER_INCH,
    )
    absorber = TransientRod.Absorber(
        radius=1.187 * 0.5 * CM_PER_INCH,
        length=15.0 * CM_PER_INCH,
    )
    air_follower = TransientRod.AirFollower(thickness=19.75 * CM_PER_INCH)
    element_plug = TransientRod.ElementPlug(thickness=0.50 * CM_PER_INCH)
    magneform = TransientRod.MagneformFitting(thickness=1.0 * CM_PER_INCH)
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
def unequal_transient_rod():
    cladding = TransientRod.Cladding(thickness=0.05, outer_radius=1.0)
    absorber = TransientRod.Absorber(radius=0.5, length=10.0)
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

    expected_length = (
        transient_rod.lower_element_plug.thickness
        + transient_rod.air_follower.thickness
        + transient_rod.lower_magneform_fitting.thickness
        + transient_rod.absorber.length
        + transient_rod.upper_magneform_fitting.thickness
        + transient_rod.upper_element_plug.thickness
    )
    assert isclose(transient_rod.length, expected_length)


def test_equality_and_hash(transient_rod, unequal_transient_rod):
    assert transient_rod == deepcopy(transient_rod)
    assert transient_rod != unequal_transient_rod
    assert hash(transient_rod) == hash(deepcopy(transient_rod))
    assert hash(transient_rod) != hash(unequal_transient_rod)


def test_as_stack(transient_rod):
    stack = transient_rod.as_stack()
    assert len(stack.segments) == 6
    assert isclose(stack.length, transient_rod.length)
    assert isclose(stack.bottom_pos, 0.0)


def test_openmc_builder(transient_rod):
    geom_element = transient_rod
    universe = openmc_builder.build(geom_element)
    assert universe.name == "transient_rod"
    assert len(universe.cells) == 6


def test_mpact_builder(transient_rod):
    geom_element = transient_rod
    core = mpact_builder.build(geom_element)

    expected_xy = transient_rod.cladding.outer_radius * 2.0
    expected_z = sorted([transient_rod.lower_element_plug.thickness,
                         transient_rod.air_follower.thickness,
                         transient_rod.lower_magneform_fitting.thickness,
                         transient_rod.absorber.length,
                         transient_rod.upper_magneform_fitting.thickness,
                         transient_rod.upper_element_plug.thickness])
    expected_nz        = len(expected_z)
    expected_mod_dim_z = sorted(list(set(expected_z)))
    expected_height    = sum(expected_z)

    assert isclose(core.mod_dim['X'], expected_xy)
    assert isclose(core.mod_dim['Y'], expected_xy)
    assert core.mod_dim['Z'] == expected_mod_dim_z
    assert core.nz == expected_nz
    assert isclose(core.height, expected_height)

    stack = geom_element.as_stack().unionize_radial_mesh()
    expected_unique_segments = len({segment for segment in stack.segments})

    assert len(core.pins)       == expected_unique_segments
    assert len(core.modules)    == expected_unique_segments
    assert len(core.lattices)   == expected_unique_segments
    assert len(core.assemblies) == 1

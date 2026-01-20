import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import RSRCavity
from coreforge.materials import Air, Al6061T6, unique_materials

CM_PER_INCH = 2.54


@pytest.fixture
def specimen_tube():
    return RSRCavity.SpecimenTube(
        outer_radius=1.0 * 0.5 * CM_PER_INCH,
        thickness=0.058 * CM_PER_INCH,
        material=Al6061T6(),
    )


@pytest.fixture
def rsr_cavity(specimen_tube):
    return RSRCavity(
        outer_radius=28.625 * 0.5 * CM_PER_INCH,
        height=10.8174 * CM_PER_INCH,
        number_of_tubes=40,
        tube_to_center_distance=26.312 * 0.5 * CM_PER_INCH,
        tube_specs=specimen_tube,
    )


@pytest.fixture
def unequal_rsr_cavity(rsr_cavity):
    return RSRCavity(
        outer_radius=rsr_cavity.outer_radius * 1.1,
        height=rsr_cavity.height,
        number_of_tubes=rsr_cavity.number_of_tubes,
        tube_to_center_distance=rsr_cavity.tube_to_center_distance,
        tube_specs=rsr_cavity.tube_specs,
        material=rsr_cavity.material,
    )


def test_initialization_defaults(rsr_cavity):
    assert rsr_cavity.outer_radius == pytest.approx(28.625 * 0.5 * CM_PER_INCH)
    assert rsr_cavity.height == pytest.approx(10.8174 * CM_PER_INCH)
    assert rsr_cavity.number_of_tubes == 40
    assert rsr_cavity.tube_to_center_distance == pytest.approx(26.312 * 0.5 * CM_PER_INCH)
    assert isinstance(rsr_cavity.tube_specs.material, Al6061T6)
    assert isinstance(rsr_cavity.material, Air)
    expected = unique_materials([rsr_cavity.material, rsr_cavity.tube_specs.material])
    assert rsr_cavity.get_materials() == expected


def test_equality_and_hash(rsr_cavity, unequal_rsr_cavity):
    assert rsr_cavity == deepcopy(rsr_cavity)
    assert rsr_cavity != unequal_rsr_cavity
    assert hash(rsr_cavity) == hash(deepcopy(rsr_cavity))
    assert hash(rsr_cavity) != hash(unequal_rsr_cavity)

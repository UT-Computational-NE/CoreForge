import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import GridPlate
from coreforge.materials import Al6061T6

CM_PER_INCH = 2.54


@pytest.fixture
def grid_plate():
    return GridPlate(
        thickness=0.62 * CM_PER_INCH,
        fuel_penetration_radius=1.505 * 0.5 * CM_PER_INCH,
        control_rod_penetration_radius=1.505 * 0.5 * CM_PER_INCH,
        material=Al6061T6(),
    )


@pytest.fixture
def unequal_grid_plate(grid_plate):
    return GridPlate(
        thickness=grid_plate.thickness * 1.1,
        fuel_penetration_radius=grid_plate.fuel_penetration_radius,
        control_rod_penetration_radius=grid_plate.control_rod_penetration_radius,
        material=grid_plate.material,
    )


def test_initialization(grid_plate):
    assert grid_plate.thickness == pytest.approx(0.62 * CM_PER_INCH)
    assert grid_plate.fuel_penetration_radius == pytest.approx(1.505 * 0.5 * CM_PER_INCH)
    assert grid_plate.control_rod_penetration_radius == pytest.approx(1.505 * 0.5 * CM_PER_INCH)
    assert isinstance(grid_plate.material, Al6061T6)


def test_equality_and_hash(grid_plate, unequal_grid_plate):
    assert grid_plate == deepcopy(grid_plate)
    assert grid_plate != unequal_grid_plate
    assert hash(grid_plate) == hash(deepcopy(grid_plate))
    assert hash(grid_plate) != hash(unequal_grid_plate)

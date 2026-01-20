import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import GridPlate
from coreforge.geometry_elements.triga.netl.grid_plate import grid_plate_penetration_map
from coreforge.materials import Al6061T6, unique_materials

CM_PER_INCH = 2.54


@pytest.fixture
def grid_plate():
    fuel_radius = 1.505 * 0.5 * CM_PER_INCH
    control_radius = 1.505 * 0.5 * CM_PER_INCH
    central_thimble_radius = 1.5 * 0.5 * CM_PER_INCH
    penetration_map = grid_plate_penetration_map(fuel_radius, control_radius, central_thimble_radius)
    return GridPlate(
        thickness=0.62 * CM_PER_INCH,
        penetration_map=penetration_map,
        material=Al6061T6(),
    )


@pytest.fixture
def unequal_grid_plate(grid_plate):
    penetration_map = dict(grid_plate.penetration_map)
    penetration_map["B-01"] = grid_plate.penetration_map["B-01"] * 1.1
    return GridPlate(
        thickness=grid_plate.thickness * 1.1,
        penetration_map=penetration_map,
        material=grid_plate.material,
    )


def test_initialization(grid_plate):
    assert grid_plate.thickness == pytest.approx(0.62 * CM_PER_INCH)
    assert grid_plate.penetration_map["B-01"] == pytest.approx(1.505 * 0.5 * CM_PER_INCH)
    assert grid_plate.penetration_map["C-01"] == pytest.approx(1.505 * 0.5 * CM_PER_INCH)
    assert grid_plate.penetration_map["A-01"] == pytest.approx(1.5   * 0.5 * CM_PER_INCH)
    assert isinstance(grid_plate.material, Al6061T6)
    assert grid_plate.get_materials() == unique_materials([grid_plate.material])


def test_equality_and_hash(grid_plate, unequal_grid_plate):
    assert grid_plate == deepcopy(grid_plate)
    assert grid_plate != unequal_grid_plate
    assert hash(grid_plate) == hash(deepcopy(grid_plate))
    assert hash(grid_plate) != hash(unequal_grid_plate)

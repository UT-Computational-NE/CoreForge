import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import GridPlate
from coreforge.geometry_elements.triga.netl.grid_plate import grid_plate_penetration_map
from coreforge.materials import Al6061T6, unique_materials
from coreforge.shapes import Circle
from .test_core import (core, central_thimble, transient_rod, control_rod,
                        source_holder, pnt, three_element_irradiator,
                        fuel_element, graphite_element)

CM_PER_INCH = 2.54


@pytest.fixture
def grid_plate():
    fuel_radius = 1.505 * 0.5 * CM_PER_INCH
    control_radius = 1.505 * 0.5 * CM_PER_INCH
    pnt_radius = 1.505 * 0.5 * CM_PER_INCH
    central_thimble_radius = 1.5 * 0.5 * CM_PER_INCH
    penetration_map = grid_plate_penetration_map(fuel_radius, control_radius, central_thimble_radius, pnt_radius)
    return GridPlate(
        thickness=0.62 * CM_PER_INCH,
        penetration_map=penetration_map,
        material=Al6061T6(),
    )


@pytest.fixture
def unequal_grid_plate(grid_plate):
    penetration_map = dict(grid_plate.penetration_map)
    penetration_map["B-01"] = [(radius * 1.1, x0, y0)
                               for radius, x0, y0 in grid_plate.penetration_map["B-01"]]
    return GridPlate(
        thickness=grid_plate.thickness * 1.1,
        penetration_map=penetration_map,
        material=grid_plate.material,
    )


def test_initialization(grid_plate, core):
    assert grid_plate.thickness == pytest.approx(0.62 * CM_PER_INCH)
    assert grid_plate.penetration_map["B-01"][0] == pytest.approx((1.505 * 0.5 * CM_PER_INCH, 0., 0.))
    assert grid_plate.penetration_map["C-01"][0] == pytest.approx((1.505 * 0.5 * CM_PER_INCH, 0., 0.))
    assert grid_plate.penetration_map["A-01"][0] == pytest.approx((1.5   * 0.5 * CM_PER_INCH, 0., 0.))
    assert grid_plate.penetration_map["G-34"][0] == pytest.approx((1.505 * 0.5 * CM_PER_INCH, 0., 0.))
    assert isinstance(grid_plate.material, Al6061T6)
    assert grid_plate.get_materials() == unique_materials([grid_plate.material])

    radii = dict(fuel_location_radius=1.9, control_rod_location_radius=1.9,
                 central_thimble_radius=1.8, pnt_location_radius=1.7)
    offsets = {core.RING_MAP[i][j]: offset for (i, j), offset in
               core.lattice.cells_intersecting(Circle(2.4), core.three_element_center).items()}
    penetrations = grid_plate_penetration_map(
        **radii, three_element_location_radius=2.4, core=core,
    )
    for location in core.THREE_ELEMENT_LOCATIONS:
        assert penetrations[location] == [(2.4, *offsets[location])]

    # A wider opening also reaches ordinary and otherwise solid locations.
    radius = 10. * core.pitch
    wide_penetrations = grid_plate_penetration_map(
        **radii, three_element_location_radius=radius, core=core,
    )
    for location in ("B-01", "G-01"):
        i, j = next((i, ring.index(location)) for i, ring in enumerate(core.RING_MAP) if location in ring)
        center = core.lattice.cell_centers[i][j]
        opening = (radius, core.three_element_center[0] - center[0], core.three_element_center[1] - center[1])
        ordinary = [(1.9, 0., 0.)] if location == "B-01" else []
        assert wide_penetrations[location] == ordinary + [opening]
    assert grid_plate.penetration_map["G-01"] == []
    with pytest.raises(AssertionError, match="core is required"):
        grid_plate_penetration_map(**radii, three_element_location_radius=2.4)


def test_equality_and_hash(grid_plate, unequal_grid_plate):
    assert grid_plate == deepcopy(grid_plate)
    assert grid_plate != unequal_grid_plate
    assert hash(grid_plate) == hash(deepcopy(grid_plate))
    assert hash(grid_plate) != hash(unequal_grid_plate)

    shifted = deepcopy(grid_plate)
    radius, _, _ = shifted.penetration_map["B-01"][0]
    shifted.penetration_map["B-01"][0] = (radius, 1., 0.)
    assert grid_plate != shifted
    assert hash(grid_plate) != hash(shifted)

from copy import deepcopy
from math import cos, radians, sin

import pytest

from coreforge.geometry_elements.triga.netl import Reactor
from coreforge.materials import unique_materials
from coreforge.shapes import Rectangle
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder

from .test_pool import pool
from .test_reflector import reflector
from .test_shroud import shroud
from .test_rsr_cavity import rsr_cavity, specimen_tube
from .test_beam_port import beam_port
from .test_grid_plate import grid_plate
from .test_core import core
from .test_central_thimble import central_thimble
from .test_transient_rod import transient_rod
from .test_fuel_follower_control_rod import control_rod
from .test_source_holder import source_holder
from ..test_fuel_element import fuel_element
from ..test_graphite_element import graphite_element

CM_PER_INCH = 2.54
TRANSIENT_ROD_FULLY_INSERTED_POSITION = -73.0250
FFCR_FULLY_INSERTED_POSITION = -76.5180
UPPER_GRID_PLATE_TOP_TO_CORE_CENTERLINE_DISTANCE = 12.75 * CM_PER_INCH
LOWER_GRID_PLATE_TOP_TO_CORE_CENTERLINE_DISTANCE = 13.06 * CM_PER_INCH
REFLECTOR_CORE_CENTERLINE_OFFSET = 0.565 * CM_PER_INCH
BEAMPORT_AXIAL_OFFSET = -6.985


def cosd(deg: float) -> float:
    return cos(radians(deg))


def sind(deg: float) -> float:
    return sin(radians(deg))


@pytest.fixture
def reactor(pool, reflector, shroud, rsr_cavity, beam_port, grid_plate, core):
    reflector_wrap = Reactor.Reflector(geometry=reflector,
                                       core_centerline_offset=REFLECTOR_CORE_CENTERLINE_OFFSET)
    upper_grid = Reactor.GridPlate(geometry=grid_plate,
                                   top_to_core_centerline_distance=UPPER_GRID_PLATE_TOP_TO_CORE_CENTERLINE_DISTANCE)
    lower_grid = Reactor.GridPlate(geometry=grid_plate,
                                   top_to_core_centerline_distance=LOWER_GRID_PLATE_TOP_TO_CORE_CENTERLINE_DISTANCE)

    bp_length = beam_port.length
    beam_port_1_5 = Reactor.BeamPort(geometry=beam_port,
                                     translation=(35.2425, 0.0, BEAMPORT_AXIAL_OFFSET),
                                     rotation=90.0)
    beam_port_2 = Reactor.BeamPort(
        geometry=beam_port,
        translation=(6.222 + cosd(150.0) * bp_length * 0.5,
                     35.255 + sind(150.0) * bp_length * 0.5,
                     BEAMPORT_AXIAL_OFFSET),
        rotation=150.0,
    )
    beam_port_3 = Reactor.BeamPort(geometry=beam_port,
                                   translation=(-bp_length * 0.5 - 26.43188, 0.0, BEAMPORT_AXIAL_OFFSET),
                                   rotation=0.0)
    beam_port_4 = Reactor.BeamPort(
        geometry=beam_port,
        translation=(-13.216 - cosd(60.0) * bp_length * 0.5,
                     -22.871 - sind(60.0) * bp_length * 0.5,
                     BEAMPORT_AXIAL_OFFSET),
        rotation=60.0,
    )

    return Reactor(pool=pool,
                   reflector=reflector_wrap,
                   shroud=shroud,
                   beam_port_1_5=beam_port_1_5,
                   beam_port_2=beam_port_2,
                   beam_port_3=beam_port_3,
                   beam_port_4=beam_port_4,
                   rotary_specimen_rack_cavity=rsr_cavity,
                   core=core,
                   upper_grid_plate=upper_grid,
                   lower_grid_plate=lower_grid,
                   transient_rod_position=TRANSIENT_ROD_FULLY_INSERTED_POSITION,
                   regulating_rod_position=FFCR_FULLY_INSERTED_POSITION,
                   shim_1_rod_position=FFCR_FULLY_INSERTED_POSITION,
                   shim_2_rod_position=FFCR_FULLY_INSERTED_POSITION)


@pytest.fixture
def unequal_reactor(reactor):
    other = deepcopy(reactor)
    other.transient_rod_position = reactor.transient_rod_position - 1.0
    return other


def _beamport_expected_bounds(beamport: Reactor.BeamPort):
    z_center = beamport.translation[2]
    radius = beamport.geometry.outer_radius
    return (z_center - radius, z_center + radius)


def test_initialization(reactor, pool, reflector, rsr_cavity):
    expected_pool = (-0.5 * pool.height, 0.5 * pool.height)
    reflector_center = reactor.reflector.core_centerline_offset
    reflector_half = 0.5 * reflector.height
    expected_reflector = (reflector_center - reflector_half, reflector_center + reflector_half)
    expected_rsr = (expected_reflector[1] - rsr_cavity.height, expected_reflector[1])

    assert reactor.pool_axial_bounds == pytest.approx(expected_pool)
    assert reactor.reflector_axial_bounds == pytest.approx(expected_reflector)
    assert reactor.shroud_axial_bounds == pytest.approx(expected_reflector)
    assert reactor.rsr_axial_bounds == pytest.approx(expected_rsr)
    assert reactor.beamport_axial_bounds[5] == reactor.beamport_axial_bounds[1]
    expected = []
    expected.extend(reactor.pool.get_materials())
    expected.extend(reactor.reflector.geometry.get_materials())
    expected.extend(reactor.shroud.get_materials())
    expected.extend(reactor.rotary_specimen_rack_cavity.get_materials())
    expected.extend(reactor.core.get_materials())
    expected.extend(reactor.upper_grid_plate.geometry.get_materials())
    expected.extend(reactor.lower_grid_plate.geometry.get_materials())
    for beam_port in (reactor.beam_port_1_5, reactor.beam_port_2, reactor.beam_port_3, reactor.beam_port_4):
        expected.extend(beam_port.geometry.get_materials())
    assert reactor.get_materials() == unique_materials(expected)


def test_equality_and_hash(reactor, unequal_reactor):
    assert reactor == deepcopy(reactor)
    assert reactor != unequal_reactor
    assert hash(reactor) == hash(deepcopy(reactor))
    assert hash(reactor) != hash(unequal_reactor)


def test_axial_bounds_properties(reactor):
    expected = {
        1: _beamport_expected_bounds(reactor.beam_port_1_5),
        2: _beamport_expected_bounds(reactor.beam_port_2),
        3: _beamport_expected_bounds(reactor.beam_port_3),
        4: _beamport_expected_bounds(reactor.beam_port_4),
        5: _beamport_expected_bounds(reactor.beam_port_1_5),
    }

    assert set(reactor.beamport_axial_bounds.keys()) == {1, 2, 3, 4, 5}
    for beamport_id, bounds in expected.items():
        assert reactor.beamport_axial_bounds[beamport_id] == pytest.approx(bounds)


def test_axial_intersection_filters(reactor):
    rect = Rectangle(w=1.0, h=1.0)
    cell_center = (0.0, 0.0)

    out_reflector = (reactor.reflector_axial_bounds[1] + 1.0,
                     reactor.reflector_axial_bounds[1] + 2.0)
    assert reactor.reflector_intersects(rect, cell_center, reactor.reflector_axial_bounds)
    assert not reactor.reflector_intersects(rect, cell_center, out_reflector)

    out_rsr = (reactor.rsr_axial_bounds[1] + 1.0,
               reactor.rsr_axial_bounds[1] + 2.0)
    assert reactor.rsr_intersects(rect, cell_center, reactor.rsr_axial_bounds)
    assert not reactor.rsr_intersects(rect, cell_center, out_rsr)

    cell_center = (reactor.beam_port_1_5.translation[0], reactor.beam_port_1_5.translation[1])
    out_beamport = (reactor.beamport_axial_bounds[1][1] + 1.0,
                    reactor.beamport_axial_bounds[1][1] + 2.0)
    assert reactor.beamport_intersects(rect, cell_center, 1, reactor.beamport_axial_bounds[1])
    assert not reactor.beamport_intersects(rect, cell_center, 1, out_beamport)
    out_pool = (reactor.pool_axial_bounds[1] + 1.0,
                reactor.pool_axial_bounds[1] + 2.0)
    assert reactor.pool_contains(rect, cell_center, reactor.pool_axial_bounds)
    assert not reactor.pool_contains(rect, cell_center, out_pool)

    thickness = reactor.shroud.thickness
    cell_side = thickness * 0.1
    shroud_rect = Rectangle(w=cell_side, h=cell_side)
    cell_center = (reactor.shroud.primary_hex_inner_radius + 0.25 * cell_side, 0.0)
    out_shroud = (reactor.shroud_axial_bounds[1] + 1.0,
                  reactor.shroud_axial_bounds[1] + 2.0)
    assert reactor.shroud_intersects(shroud_rect, cell_center, reactor.shroud_axial_bounds)
    assert not reactor.shroud_intersects(shroud_rect, cell_center, out_shroud)

def test_openmc_builder(reactor):
    universe = openmc_builder.build(reactor)
    assert universe.name == "reactor"
    assert len(universe.cells) == 9


def test_mpact_builder_without_excore(reactor, num_procs):
    specs = mpact_builder.triga.netl.Reactor.Specs(exclude_excore=True, num_procs=num_procs)
    core = mpact_builder.build(reactor, specs)
    assert core.nx > 0
    assert core.ny > 0
    assert core.nz > 0
    assert core.height > 0.0
    assert core.width["X"] > 0.0
    assert core.width["Y"] > 0.0


def test_mpact_builder_with_excore(reactor, num_procs):
    specs = mpact_builder.triga.netl.Reactor.Specs(num_procs=num_procs)
    core = mpact_builder.build(reactor, specs)
    assert core.nx > 0
    assert core.ny > 0
    assert core.nz > 0
    assert core.height > 0.0
    assert core.width["X"] > 0.0
    assert core.width["Y"] > 0.0

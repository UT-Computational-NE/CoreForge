from copy import deepcopy
from math import cos, radians, sin, sqrt

import openmc
import pytest

from coreforge.geometry_elements.triga.netl import Reactor
from coreforge.materials import unique_materials
from coreforge.shapes import Interval, Rectangle
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from coreforge.openmc_builder.triga.netl.reactor import build_core_lattice

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


def _beamport_expected_interior_bounds(beamport: Reactor.BeamPort):
    z_center = beamport.translation[2]
    half_width = beamport.geometry.inner_radius / sqrt(2.0)
    return (z_center - half_width, z_center + half_width)


def test_component_owned_axial_bounds(pool, reflector, beam_port):
    pool_wrap = Reactor.Pool(pool)
    reflector_wrap = Reactor.Reflector(reflector, REFLECTOR_CORE_CENTERLINE_OFFSET)
    beamport_wrap = Reactor.BeamPort(beam_port, translation=(0.0, 0.0, BEAMPORT_AXIAL_OFFSET))

    assert pool_wrap.axial_bounds.bounds == pytest.approx((-0.5 * pool.height, 0.5 * pool.height))
    assert reflector_wrap.axial_bounds.bounds == pytest.approx(
        (REFLECTOR_CORE_CENTERLINE_OFFSET - 0.5 * reflector.height,
         REFLECTOR_CORE_CENTERLINE_OFFSET + 0.5 * reflector.height)
    )
    assert beamport_wrap.axial_bounds.bounds == pytest.approx(_beamport_expected_bounds(beamport_wrap))


def test_initialization(reactor, pool, reflector, shroud, rsr_cavity):
    expected_pool = (-0.5 * pool.height, 0.5 * pool.height)
    reflector_center = reactor.reflector.core_centerline_offset
    reflector_half = 0.5 * reflector.height
    expected_reflector = (reflector_center - reflector_half, reflector_center + reflector_half)
    expected_rsr = (expected_reflector[1] - rsr_cavity.height, expected_reflector[1])
    expected_upper_grid = (
        reactor.upper_grid_plate.top_to_core_centerline_distance - reactor.upper_grid_plate.geometry.thickness,
        reactor.upper_grid_plate.top_to_core_centerline_distance,
    )
    expected_lower_grid = (
        -reactor.lower_grid_plate.top_to_core_centerline_distance - reactor.lower_grid_plate.geometry.thickness,
        -reactor.lower_grid_plate.top_to_core_centerline_distance,
    )

    assert reactor.pool.axial_bounds.bounds == pytest.approx(expected_pool)
    assert reactor.reflector.axial_bounds.bounds == pytest.approx(expected_reflector)
    assert reactor.shroud.axial_bounds.bounds == pytest.approx(expected_reflector)
    assert reactor.rotary_specimen_rack_cavity.axial_bounds.bounds == pytest.approx(expected_rsr)
    assert reactor.upper_grid_plate.axial_bounds.bounds == pytest.approx(expected_upper_grid)
    assert reactor.lower_grid_plate.axial_bounds.bounds == pytest.approx(expected_lower_grid)
    assert reactor.pool.geometry is pool
    assert reactor.reflector.geometry is reflector
    assert reactor.shroud.geometry is shroud
    assert reactor.rotary_specimen_rack_cavity.geometry is rsr_cavity
    assert set(reactor.beam_port.keys()) == {1, 2, 3, 4, 5}
    assert reactor.beam_port[5] is reactor.beam_port[1]
    expected = []
    expected.extend(reactor.pool.get_materials())
    expected.extend(reactor.reflector.geometry.get_materials())
    expected.extend(reactor.shroud.get_materials())
    expected.extend(reactor.rotary_specimen_rack_cavity.get_materials())
    expected.extend(reactor.core.get_materials())
    expected.extend(reactor.upper_grid_plate.geometry.get_materials())
    expected.extend(reactor.lower_grid_plate.geometry.get_materials())
    for beam_port in (reactor.beam_port[1], reactor.beam_port[2], reactor.beam_port[3], reactor.beam_port[4]):
        expected.extend(beam_port.geometry.get_materials())
    assert reactor.get_materials() == unique_materials(expected)


def test_equality_and_hash(reactor, unequal_reactor):
    assert reactor == deepcopy(reactor)
    assert reactor != unequal_reactor
    assert hash(reactor) == hash(deepcopy(reactor))
    assert hash(reactor) != hash(unequal_reactor)


def test_axial_bounds_properties(reactor):
    expected = {1: _beamport_expected_bounds(reactor.beam_port[1]),
                2: _beamport_expected_bounds(reactor.beam_port[2]),
                3: _beamport_expected_bounds(reactor.beam_port[3]),
                4: _beamport_expected_bounds(reactor.beam_port[4]),
                5: _beamport_expected_bounds(reactor.beam_port[5])}

    assert set(reactor.beam_port.keys()) == {1, 2, 3, 4, 5}
    for beamport_id, bounds in expected.items():
        assert reactor.beam_port[beamport_id].axial_bounds.bounds == pytest.approx(bounds)
    assert reactor.beam_port[5] is reactor.beam_port[1]
    assert reactor.beam_port[5].axial_bounds is reactor.beam_port[1].axial_bounds


def test_beam_port_interior_properties(reactor):
    beamport = reactor.beam_port[1]
    interior_side = beamport.geometry.inner_radius * sqrt(2.0)

    assert beamport.interior_box.w == pytest.approx(beamport.geometry.length)
    assert beamport.interior_box.h == pytest.approx(interior_side)
    assert beamport.interior_axial_bounds.bounds == pytest.approx(_beamport_expected_interior_bounds(beamport))


def test_rsr_tube_properties(reactor):
    rsr = reactor.rotary_specimen_rack_cavity
    tube_radius = rsr.tube_specs.outer_radius
    tube_distance = rsr.tube_to_center_distance

    assert len(rsr.tube_centers) == rsr.number_of_tubes
    assert rsr.tube_centers[0] == pytest.approx((0.0, tube_distance))
    assert rsr.tube_centers[1] == pytest.approx(
        (tube_distance * cosd(90.0 - 360.0 / rsr.number_of_tubes),
         tube_distance * sind(90.0 - 360.0 / rsr.number_of_tubes))
    )
    assert rsr.tube_outer_boundary.r == pytest.approx(tube_radius)


def test_axial_intersection_filters(reactor):
    rect = Rectangle(w=1.0, h=1.0)
    cell_center = (0.0, 0.0)

    out_reflector = Interval(reactor.reflector.axial_bounds.upper + 1.0,
                             reactor.reflector.axial_bounds.upper + 2.0)
    shroud_outer_x = reactor.shroud.primary_hex_inner_radius + reactor.shroud.thickness
    rsr_center = ((shroud_outer_x + reactor.rotary_specimen_rack_cavity.outer_radius) * 0.5, 0.0)
    reflector_center = ((reactor.rotary_specimen_rack_cavity.outer_radius +
                         reactor.reflector.geometry.radius) * 0.5, 0.0)
    assert not reactor.reflector_intersects(rect, cell_center, reactor.reflector.axial_bounds)
    assert reactor.reflector_intersects(rect, reflector_center, reactor.reflector.axial_bounds)
    assert not reactor.reflector_intersects(rect, cell_center, out_reflector)

    out_rsr = Interval(reactor.rotary_specimen_rack_cavity.axial_bounds.upper + 1.0,
                       reactor.rotary_specimen_rack_cavity.axial_bounds.upper + 2.0)
    assert not reactor.rsr_cavity_intersects(rect, cell_center, reactor.rotary_specimen_rack_cavity.axial_bounds)
    assert reactor.rsr_cavity_intersects(rect, rsr_center, reactor.rotary_specimen_rack_cavity.axial_bounds)
    assert not reactor.rsr_cavity_intersects(rect, rsr_center, out_rsr)

    tube_center = reactor.rotary_specimen_rack_cavity.tube_centers[0]
    assert reactor.rsr_tube_intersects(rect, tube_center, reactor.rotary_specimen_rack_cavity.axial_bounds)
    assert not reactor.rsr_tube_intersects(rect, tube_center, out_rsr)
    assert not reactor.rsr_tube_intersects(rect, cell_center, reactor.rotary_specimen_rack_cavity.axial_bounds)

    cell_center = (reactor.beam_port[1].translation[0], reactor.beam_port[1].translation[1])
    out_beamport = Interval(reactor.beam_port[1].axial_bounds.upper + 1.0,
                            reactor.beam_port[1].axial_bounds.upper + 2.0)
    assert reactor.beam_port[1].intersects(rect, cell_center, reactor.beam_port[1].axial_bounds)
    assert not reactor.beam_port[1].intersects(rect, cell_center, out_beamport)
    out_pool = Interval(reactor.pool.axial_bounds.upper + 1.0,
                        reactor.pool.axial_bounds.upper + 2.0)
    assert reactor.pool.contains(rect, cell_center, reactor.pool.axial_bounds)
    assert not reactor.pool.contains(rect, cell_center, out_pool)

    thickness = reactor.shroud.thickness
    cell_side = thickness * 0.1
    shroud_rect = Rectangle(w=cell_side, h=cell_side)
    cell_center = (reactor.shroud.primary_hex_inner_radius + 0.25 * cell_side, 0.0)
    out_shroud = Interval(reactor.shroud.axial_bounds.upper + 1.0,
                          reactor.shroud.axial_bounds.upper + 2.0)
    assert reactor.shroud.intersects(shroud_rect, cell_center, reactor.shroud.axial_bounds)
    assert not reactor.shroud.intersects(shroud_rect, cell_center, out_shroud)


def test_excore_region_contains(reactor):
    rect = Rectangle(w=0.1, h=0.1)
    rsr = reactor.rotary_specimen_rack_cavity
    axial_bounds = Interval(rsr.axial_bounds.center - 0.05, rsr.axial_bounds.center + 0.05)
    shroud_outer_x = reactor.shroud.primary_hex_inner_radius + reactor.shroud.thickness
    rsr_center = ((shroud_outer_x + rsr.outer_radius) * 0.5, 0.0)

    assert reactor.rsr_cavity_contains(rect, rsr_center, axial_bounds)
    assert not reactor.rsr_cavity_contains(rect, rsr.tube_centers[0], axial_bounds)

    reflector_axial_bounds = Interval(reactor.reflector.axial_bounds.center - 0.05,
                                      reactor.reflector.axial_bounds.center + 0.05)
    reflector_radius = (rsr.outer_radius + reactor.reflector.geometry.radius) * 0.5
    reflector_centers = [(reflector_radius * cosd(angle), reflector_radius * sind(angle))
                         for angle in (270.0, 315.0, 225.0, 90.0, 45.0, 135.0)]
    reflector_center = next(center for center in reflector_centers
                            if not reactor.any_beamport_intersects(rect, center, reflector_axial_bounds))

    assert reactor.reflector_contains(rect, reflector_center, reflector_axial_bounds)
    assert not reactor.reflector_contains(rect, rsr_center, axial_bounds)


def test_beam_port_contains(reactor):
    beamport = reactor.beam_port[3]
    rect = Rectangle(w=1.0, h=1.0)
    center = (beamport.translation[0], beamport.translation[1])
    axial_center = beamport.interior_axial_bounds.center
    axial_bounds = Interval(axial_center - 0.5, axial_center + 0.5)

    assert beamport.contains(rect, center, axial_bounds)
    assert not beamport.contains(rect, center, beamport.axial_bounds)

    edge_center = (center[0], center[1] + 0.5 * beamport.interior_box.h)
    assert beamport.intersects(rect, edge_center, axial_bounds)
    assert not beamport.contains(rect, edge_center, axial_bounds)


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

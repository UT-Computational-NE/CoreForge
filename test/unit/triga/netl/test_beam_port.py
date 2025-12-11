import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import BeamPort
from coreforge.materials import Air, Al6061T6


@pytest.fixture
def beam_port():
    return BeamPort(inner_radius=6.065 * 0.5 * 2.54,
                    outer_radius=6.625 * 2.54,
                    length=100.0)


@pytest.fixture
def unequal_beam_port(beam_port):
    return BeamPort(
        inner_radius=beam_port.inner_radius * 1.1,
        outer_radius=beam_port.outer_radius,
        length=beam_port.length,
        tube_material=beam_port.tube_material,
        fill_material=beam_port.fill_material,
    )


def test_initialization(beam_port):
    assert beam_port.inner_radius == pytest.approx(6.065 * 0.5 * 2.54)
    assert beam_port.outer_radius == pytest.approx(6.625 * 2.54)
    assert beam_port.length == pytest.approx(100.0)
    assert isinstance(beam_port.tube_material, Al6061T6)
    assert isinstance(beam_port.fill_material, Air)


def test_equality_and_hash(beam_port, unequal_beam_port):
    assert beam_port == deepcopy(beam_port)
    assert beam_port != unequal_beam_port
    assert hash(beam_port) == hash(deepcopy(beam_port))
    assert hash(beam_port) != hash(unequal_beam_port)

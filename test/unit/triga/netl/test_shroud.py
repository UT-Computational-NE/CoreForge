import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import Shroud
from coreforge.materials import Al6061T6

CM_PER_INCH = 2.54


@pytest.fixture
def shroud():
    return Shroud(
        thickness=0.1875 * CM_PER_INCH,
        primary_hex_inner_radius=10.21875 * CM_PER_INCH,
        rotated_hex_inner_radius=10.75 * CM_PER_INCH,
    )


@pytest.fixture
def unequal_shroud(shroud):
    return Shroud(
        thickness=shroud.thickness * 1.1,
        primary_hex_inner_radius=shroud.primary_hex_inner_radius,
        rotated_hex_inner_radius=shroud.rotated_hex_inner_radius,
        material=shroud.material,
    )


def test_initialization(shroud):
    assert shroud.thickness == pytest.approx(0.1875 * CM_PER_INCH)
    assert shroud.primary_hex_inner_radius == pytest.approx(10.21875 * CM_PER_INCH)
    assert shroud.rotated_hex_inner_radius == pytest.approx(10.75 * CM_PER_INCH)
    assert isinstance(shroud.material, Al6061T6)


def test_equality_and_hash(shroud, unequal_shroud):
    assert shroud == deepcopy(shroud)
    assert shroud != unequal_shroud
    assert hash(shroud) == hash(deepcopy(shroud))
    assert hash(shroud) != hash(unequal_shroud)

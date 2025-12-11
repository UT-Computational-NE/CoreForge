import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import Shroud
from coreforge.materials import Al6061T6

CM_PER_INCH = 2.54


@pytest.fixture
def shroud():
    return Shroud(
        thickness=0.1875 * CM_PER_INCH,
        height=23.13 * CM_PER_INCH,
        large_hex_inradius=10.75 * CM_PER_INCH,
        small_hex_inradius=10.21875 * CM_PER_INCH,
    )


@pytest.fixture
def unequal_shroud(shroud):
    return Shroud(
        thickness=shroud.thickness * 1.1,
        height=shroud.height,
        large_hex_inradius=shroud.large_hex_inradius,
        small_hex_inradius=shroud.small_hex_inradius,
        material=shroud.material,
    )


def test_initialization(shroud):
    assert shroud.thickness == pytest.approx(0.1875 * CM_PER_INCH)
    assert shroud.height == pytest.approx(23.13 * CM_PER_INCH)
    assert shroud.large_hex_inradius == pytest.approx(10.75 * CM_PER_INCH)
    assert shroud.small_hex_inradius == pytest.approx(10.21875 * CM_PER_INCH)
    assert isinstance(shroud.material, Al6061T6)


def test_equality_and_hash(shroud, unequal_shroud):
    assert shroud == deepcopy(shroud)
    assert shroud != unequal_shroud
    assert hash(shroud) == hash(deepcopy(shroud))
    assert hash(shroud) != hash(unequal_shroud)

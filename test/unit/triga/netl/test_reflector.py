import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import Reflector
from coreforge.materials import Graphite, unique_materials

CM_PER_INCH = 2.54


@pytest.fixture
def reflector():
    return Reflector(
        radius=42.0 * 0.5 * CM_PER_INCH,
        height=23.13 * CM_PER_INCH,
    )


@pytest.fixture
def unequal_reflector(reflector):
    return Reflector(
        radius=reflector.radius * 1.1,
        height=reflector.height,
        material=reflector.material,
    )


def test_initialization(reflector):
    assert reflector.radius == pytest.approx(42.0 * 0.5 * CM_PER_INCH)
    assert reflector.height == pytest.approx(23.13 * CM_PER_INCH)
    assert isinstance(reflector.material, Graphite)
    assert reflector.get_materials() == unique_materials([reflector.material])


def test_equality_and_hash(reflector, unequal_reflector):
    assert reflector == deepcopy(reflector)
    assert reflector != unequal_reflector
    assert hash(reflector) == hash(deepcopy(reflector))
    assert hash(reflector) != hash(unequal_reflector)

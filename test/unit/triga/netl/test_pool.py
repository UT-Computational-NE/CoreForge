import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import Pool
from coreforge.materials import Water


@pytest.fixture
def pool():
    return Pool(radius=90.0, height=160.0, material=Water())


@pytest.fixture
def unequal_pool(pool):
    return Pool(radius=pool.radius * 1.1, height=pool.height, material=pool.material)


def test_initialization(pool):
    assert pool.radius == pytest.approx(90.0)
    assert pool.height == pytest.approx(160.0)
    assert isinstance(pool.material, Water)


def test_equality_and_hash(pool, unequal_pool):
    assert pool == deepcopy(pool)
    assert pool != unequal_pool
    assert hash(pool) == hash(deepcopy(pool))
    assert hash(pool) != hash(unequal_pool)

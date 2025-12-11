import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import Core
from .test_central_thimble import central_thimble  # reuse fixtures
from .test_transient_rod import transient_rod
from .test_fuel_follower_control_rod import control_rod
from .test_source_holder import source_holder


@pytest.fixture
def core(central_thimble, transient_rod, control_rod, source_holder):
    core_loading = {"B-01": source_holder}
    return Core(
        pitch=1.7,
        central_thimble=central_thimble,
        core_loading=core_loading,
        transient_rod=transient_rod,
        regulating_rod=control_rod,
        shim_1_rod=deepcopy(control_rod),
        shim_2_rod=deepcopy(control_rod),
    )


@pytest.fixture
def unequal_core(core, source_holder):
    alt_loading = {"B-02": source_holder}
    return Core(
        pitch=core.pitch * 1.05,
        central_thimble=core.central_thimble,
        core_loading=alt_loading,
        transient_rod=core.transient_rod,
        regulating_rod=core.regulating_rod,
        shim_1_rod=deepcopy(core.shim_1_rod),
        shim_2_rod=deepcopy(core.shim_2_rod),
    )


def test_initialization(core, source_holder, central_thimble, transient_rod, control_rod):
    assert core.pitch == pytest.approx(1.7)
    assert core.core_map["A-01"] is central_thimble
    assert core.core_map["C-01"] is transient_rod
    assert core.core_map["C-07"] is control_rod
    assert core.core_map["D-06"] is not core.core_map["D-14"]  # distinct shims
    assert core.core_map["G-01"] is None
    assert core.core_map["B-01"] is source_holder

def test_equality_and_hash(core, unequal_core):
    assert core == deepcopy(core)
    assert core != unequal_core
    assert hash(core) == hash(deepcopy(core))
    assert hash(core) != hash(unequal_core)

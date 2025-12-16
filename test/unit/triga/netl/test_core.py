import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga.netl import Core
from .test_central_thimble import central_thimble  # reuse fixtures
from .test_transient_rod import transient_rod
from .test_fuel_follower_control_rod import control_rod
from .test_source_holder import source_holder
from ..test_fuel_element import fuel_element
from ..test_graphite_element import graphite_element

CM_PER_INCH = 2.54


@pytest.fixture
def core(central_thimble, transient_rod, control_rod, source_holder, fuel_element, graphite_element):
    fuel = lambda: deepcopy(fuel_element)
    graphite = lambda: deepcopy(graphite_element)
    source = lambda: deepcopy(source_holder)
    empty = lambda: None

    def fill(locations, factory):
        return {loc: factory() for loc in locations}

    core_loading = {}
    core_loading |= fill(["B-01", "B-02", "B-03", "B-04", "B-05", "B-06"], fuel)

    core_loading |= fill(["C-02", "C-03", "C-04", "C-05", "C-06",
                          "C-08", "C-09", "C-10", "C-11", "C-12"], fuel)

    core_loading |= fill(["D-01", "D-02", "D-04", "D-05",
                          "D-07", "D-08", "D-09", "D-10", "D-11", "D-12",
                          "D-13", "D-15", "D-16", "D-17", "D-18"], fuel)
    core_loading["D-03"] = graphite()

    core_loading |= fill(["E-01", "E-02", "E-03", "E-04", "E-05", "E-06",
                          "E-07", "E-08", "E-09", "E-10", "E-12",
                          "E-13", "E-14", "E-15", "E-16", "E-17", "E-18",
                          "E-19", "E-20", "E-21", "E-22", "E-23", "E-24"], fuel)
    core_loading["E-11"] = empty()

    core_loading |= fill(["F-01", "F-02", "F-03", "F-04", "F-05", "F-06",
                          "F-07", "F-08", "F-09", "F-10", "F-11", "F-12",
                          "F-15", "F-16", "F-17", "F-18",
                          "F-19", "F-20", "F-21", "F-22", "F-23", "F-24",
                          "F-25", "F-26", "F-27", "F-28", "F-29", "F-30"], fuel)
    core_loading["F-13"] = empty()
    core_loading["F-14"] = empty()

    core_loading |= fill(["G-02", "G-03", "G-04", "G-05", "G-06",
                          "G-08", "G-09", "G-10", "G-11", "G-12",
                          "G-14", "G-15", "G-16", "G-17", "G-18",
                          "G-20", "G-21", "G-22", "G-23", "G-24",
                          "G-26", "G-27", "G-28", "G-29", "G-30",
                          "G-33", "G-35", "G-36"], fuel)
    core_loading["G-32"] = source()
    core_loading["G-34"] = empty()

    return Core(
        pitch=1.714 * CM_PER_INCH,
        central_thimble=central_thimble,
        loading=core_loading,
        transient_rod=transient_rod,
        regulating_rod=control_rod,
        shim_1_rod=deepcopy(control_rod),
        shim_2_rod=deepcopy(control_rod),
        fill_material=fuel().outer_material,
    )


@pytest.fixture
def unequal_core(core):
    alt_loading = deepcopy(core.loading)
    alt_loading["B-02"] = None
    return Core(
        pitch=core.pitch * 1.05,
        central_thimble=core.central_thimble,
        loading=alt_loading,
        transient_rod=core.transient_rod,
        regulating_rod=core.regulating_rod,
        shim_1_rod=deepcopy(core.shim_1_rod),
        shim_2_rod=deepcopy(core.shim_2_rod),
        fill_material=core.fill_material,
    )


def test_initialization(core, fuel_element, graphite_element, source_holder, central_thimble, transient_rod, control_rod):
    assert core.pitch == pytest.approx(1.714 * CM_PER_INCH)
    assert core.full_map["B-01"] == fuel_element
    assert core.full_map["D-03"] == graphite_element
    assert core.full_map["A-01"] == central_thimble
    assert core.full_map["C-01"] == transient_rod
    assert core.full_map["C-07"] == control_rod
    assert core.full_map["D-06"] == control_rod
    assert core.full_map["D-14"] == control_rod
    assert core.full_map["G-01"] is None
    assert core.full_map["G-32"] == source_holder

def test_equality_and_hash(core, unequal_core):
    assert core == deepcopy(core)
    assert core != unequal_core
    assert hash(core) == hash(deepcopy(core))
    assert hash(core) != hash(unequal_core)

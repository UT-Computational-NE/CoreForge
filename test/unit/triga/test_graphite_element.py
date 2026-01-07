import pytest
from copy import deepcopy
from math import isclose

from numpy.testing import assert_allclose

from coreforge.geometry_elements.triga import GraphiteElement
from coreforge.materials import Air, Al6061T6, Graphite, Water
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder

CM_PER_INCH = 2.54


@pytest.fixture
def graphite_element():
    clad = GraphiteElement.Cladding(
        thickness=0.020 * CM_PER_INCH,
        outer_radius=1.475 * 0.5 * CM_PER_INCH,
    )
    meat = GraphiteElement.GraphiteMeat(
        outer_radius=1.435 * 0.5 * CM_PER_INCH,
        length=(3.72 + 0.031 + 15.0 + 2.56 + 0.5) * CM_PER_INCH,  # mirrors fuel interior length
    )
    upper_end = GraphiteElement.EndFitting(length=7.3552, r2=0.25, direction="up")
    lower_end = GraphiteElement.EndFitting(length=7.6209, r2=0.25, direction="down")

    return GraphiteElement(
        cladding=clad,
        graphite_meat=meat,
        upper_end_fitting=upper_end,
        lower_end_fitting=lower_end,
        gap_tolerance=1e-8,
        fill_gas=Air(),
        outer_material=Water(),
    )


@pytest.fixture
def unequal_graphite_element(graphite_element):
    base = graphite_element
    altered_meat = GraphiteElement.GraphiteMeat(
        outer_radius=base.graphite_meat.outer_radius * 0.95,
        length=base.graphite_meat.length,
    )
    return GraphiteElement(
        cladding=base.cladding,
        graphite_meat=altered_meat,
        upper_end_fitting=base.upper_end_fitting,
        lower_end_fitting=base.lower_end_fitting,
        gap_tolerance=base.gap_tolerance,
        fill_gas=base.fill_gas,
        outer_material=base.outer_material,
    )


def test_initialization(graphite_element):
    pin = graphite_element.graphite_pincell
    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([
        graphite_element.graphite_meat.outer_radius,
        graphite_element.cladding.outer_radius,
    ])
    assert isinstance(materials[0], Graphite)
    assert isinstance(materials[1], Al6061T6)
    assert isinstance(pin.outer_material, Water)


def test_equality_and_hash(graphite_element, unequal_graphite_element):
    assert graphite_element == deepcopy(graphite_element)
    assert graphite_element != unequal_graphite_element
    assert hash(graphite_element) == hash(deepcopy(graphite_element))
    assert hash(graphite_element) != hash(unequal_graphite_element)


def test_openmc_builder(graphite_element):
    geom_element = graphite_element
    universe = openmc_builder.build(geom_element)
    assert universe.name == "graphite_element"
    assert len(universe.cells) == 5


def test_mpact_builder(graphite_element):
    geom_element = graphite_element
    core = mpact_builder.build(geom_element)

    expected_xy = graphite_element.cladding.outer_radius * 2.0
    expected_z = sorted([graphite_element.lower_end_fitting.length,
                         graphite_element.graphite_meat.length,
                         graphite_element.upper_end_fitting.length])
    expected_nz = len(expected_z)
    expected_height = sum(expected_z)

    assert isclose(core.mod_dim['X'], expected_xy)
    assert isclose(core.mod_dim['Y'], expected_xy)
    assert_allclose(core.mod_dim['Z'], expected_z)
    assert core.nz == expected_nz
    assert isclose(core.height, expected_height)

    assert len(core.pins)       == expected_nz
    assert len(core.modules)    == expected_nz
    assert len(core.lattices)   == expected_nz
    assert len(core.assemblies) == 1

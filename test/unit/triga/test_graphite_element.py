import pytest
from copy import deepcopy

from coreforge.geometry_elements.triga import GraphiteElement
from coreforge.materials import Air, Al6061T6, Graphite, Water


@pytest.fixture
def graphite_element():
    meat = GraphiteElement.GraphiteMeat(outer_radius=0.50, length=10.0)
    clad = GraphiteElement.Cladding(thickness=0.05, outer_radius=0.80)
    upper_end = GraphiteElement.EndFitting(length=3.0, direction="up")
    lower_end = GraphiteElement.EndFitting(length=3.0, direction="down")

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
    altered_meat = GraphiteElement.GraphiteMeat(outer_radius=0.55, length=base.graphite_meat.length)
    return GraphiteElement(
        cladding=base.cladding,
        graphite_meat=altered_meat,
        upper_end_fitting=base.upper_end_fitting,
        lower_end_fitting=base.lower_end_fitting,
        gap_tolerance=base.gap_tolerance,
        fill_gas=base.fill_gas,
        outer_material=base.outer_material,
    )


def test_graphite_element_initialization(graphite_element):
    pin = graphite_element.graphite_pincell
    radii = [zone.shape.outer_radius for zone in pin.zones]
    materials = [zone.material for zone in pin.zones]

    assert radii == pytest.approx([0.50, 0.75, 0.80])
    assert isinstance(materials[0], Graphite)
    assert isinstance(materials[1], Air)
    assert isinstance(materials[2], Al6061T6)
    assert isinstance(pin.outer_material, Water)


def test_equality_and_hash(graphite_element, unequal_graphite_element):
    assert graphite_element == deepcopy(graphite_element)
    assert graphite_element != unequal_graphite_element
    assert hash(graphite_element) == hash(deepcopy(graphite_element))
    assert hash(graphite_element) != hash(unequal_graphite_element)

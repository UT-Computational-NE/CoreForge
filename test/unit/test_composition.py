""" Tests for code-agnostic composition records
"""

import pytest

import coreforge
from coreforge.composition import Composition, compositions, from_material
from coreforge.materials import Graphite, UZrH, Water, Zr


def test_compositions_is_reachable_from_the_package_root():
    """ Downstream consumers look for `coreforge.compositions`
    """
    assert callable(coreforge.compositions)


def test_catalogue_is_not_empty():
    assert compositions()


def test_every_record_is_complete():
    """ A record missing density or composition is worse than an absent one
    """
    for composition in compositions():
        assert composition.name
        assert composition.density > 0.
        assert composition.temperature > 0.
        assert composition.number_densities
        assert composition.source_class


def test_names_are_unique():
    """ Two records under one name is the duplicate-definition problem this
        interface exists to prevent
    """
    names = [composition.name for composition in compositions()]
    assert len(names) == len(set(names))


def test_uzrh_declares_both_thermal_scattering_laws():
    """ TRIGA fuel needs hydrogen-in-ZrH and zirconium-in-ZrH. A consumer that
        can hold only one of them cannot describe this fuel.
    """
    uzrh = next(c for c in compositions() if c.source_class == "UZrH")
    assert uzrh.thermal_scattering == ("c_H_in_ZrH", "c_Zr_in_ZrH")


def test_water_declares_its_thermal_scattering_law():
    water = next(c for c in compositions() if c.source_class == "Water")
    assert water.thermal_scattering == ("c_H_in_H2O",)


def test_materials_without_bound_atom_treatment_declare_nothing():
    zirconium = next(c for c in compositions() if c.source_class == "Zr")
    assert zirconium.thermal_scattering == ()


def test_from_material_round_trips_the_declared_values():
    """ The record must agree with the material it describes
    """
    material = UZrH()
    composition = from_material(material)

    assert composition.name == material.name
    assert composition.density == pytest.approx(material.density)
    assert composition.temperature == pytest.approx(material.temperature)
    assert composition.number_densities == material.number_densities
    assert composition.thermal_scattering == material.thermal_scattering


def test_number_densities_are_copied_not_shared():
    """ A consumer mutating the record must not reach back into the material
    """
    material = Water()
    composition = from_material(material)
    composition.number_densities.clear()

    assert material.number_densities


def test_parameterised_materials_are_excluded():
    """ Graphite has no single canonical density — NETL and MSRE graphite differ
        in density, contamination and pore intrusion — so publishing one would
        mean inventing it
    """
    assert not any(c.source_class == "Graphite" for c in compositions())


def test_graphite_still_declares_its_law_when_constructed():
    """ Excluded from the catalogue, but not undescribed
    """
    assert Graphite(graphite_density=1.86).thermal_scattering == ("c_Graphite",)


def test_records_are_frozen():
    """ A published composition is a fact, not a scratch pad
    """
    composition = compositions()[0]
    with pytest.raises(Exception):
        composition.density = 1.0


def test_composition_is_exported():
    assert Composition is coreforge.Composition

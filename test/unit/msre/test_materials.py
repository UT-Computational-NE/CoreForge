import pytest

import mpactpy

from coreforge.materials.msre import Salt, ThimbleGas, Insulation, ControlRodPoison
import coreforge.mpact_builder as mpact_builder
from test.unit.test_materials import materials_are_close

@pytest.fixture
def salt():
    return Salt()

@pytest.fixture
def thimble_gas():
    return ThimbleGas()

@pytest.fixture
def insulation():
    return Insulation()

@pytest.fixture
def control_rod_poison():
    return ControlRodPoison()

def test_salt(salt):
    material = mpact_builder.build_material(salt)

    num_dens = {'Li6' : 1.275735187868613e-06,  'Li7' : 0.021873764212173234,   'F19' : 0.049502055565221276,
                'Be9' : 0.009868717929396724,   'Zr90': 0.000877756207579554,  'Zr91': 0.00019141738870831094,
                'Zr92': 0.000292585402526518,   'Zr94': 0.0002965092883913052, 'Zr96': 4.776904531045193e-05,
                'U234': 7.529656447502962e-07,  'U235': 8.424186460334052e-05,
                'U236': 3.858682025989735e-07,  'U238': 0.00018097690879985385}
    expected_material = mpactpy.material.Material(
        temperature      = 900.,
        number_densities = num_dens,
        mpact_specs      = mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS[Salt]
    )

    assert materials_are_close(material, expected_material)

def test_thimble_gas(thimble_gas):
    material = mpact_builder.build_material(thimble_gas)

    num_dens = {'N14': 4.762813753259977e-05, 'N15': 1.7510327106381968e-07, 'O16': 2.1973775396694824e-06,
                'O17': 8.347923925535761e-10, 'O18': 4.406117947398875e-09}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS[ThimbleGas])

    assert materials_are_close(material, expected_material)

def test_insulation(insulation):
    material = mpact_builder.build_material(insulation)

    num_dens = {'Si' : 0.0016057278006239388, 'O16': 0.003210238459575004, 'O17': 1.2171416728729455e-06}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS[Insulation])

    assert materials_are_close(material, expected_material)

def test_control_rod_poison(control_rod_poison):
    material = mpact_builder.build_material(control_rod_poison)

    num_dens = {'Gd152': 2.7319499017784082e-05, 'Gd154': 0.0002977825392938465, 'Gd155': 0.002021642927316022,
                'Gd156': 0.002796150724470201,   'Gd157': 0.0021377507981416044, 'Gd158': 0.0033930817780087833,
                'Gd160': 0.0029860212426438006,  'O16'  : 0.051692735794137225,  'O17'  : 1.9598974877456564e-05,
                'Al27' : 0.02081514033711775}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS[ControlRodPoison])

    assert materials_are_close(material, expected_material)

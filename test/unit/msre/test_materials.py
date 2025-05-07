import pytest
from math import isclose

import mpactpy

from coreforge.materials.msre import Salt, ThimbleGas, Insulation, ControlRodPoison
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
    material = salt.mpact_material

    num_dens = {'Li6' : 1.7431446223252428e-06, 'Li7' : 0.02988796955594127,   'F19' : 0.05218107467967278,
                'Be9' : 0.00898964129413786,    'Zr90': 0.00047974094545786845,'Zr91': 0.00010461989131267802,
                'Zr92': 0.00015991364848595618, 'Zr94': 0.00016205826301375617,'Zr96': 2.6108350773217338e-05,
                'U234': 4.115361955751947e-07,  'U235': 4.604270687345431e-05, 'U236': 2.1089771252934387e-07,
                'U238': 9.891360788333172e-05}
    expected_material = mpactpy.material.Material(temperature                 = 900.,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = salt.mpact_build_specs)

    assert materials_are_close(material, expected_material)

def test_thimble_gas(thimble_gas):
    material = thimble_gas.mpact_material

    num_dens = {'N14': 5.1248390373520565e-05, 'N15': 1.884130107967543e-07, 'O16': 2.3697368312685885e-06,
                'O17': 8.984707794762167e-10}
    expected_material = mpactpy.material.Material(temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = thimble_gas.mpact_build_specs)

    assert materials_are_close(material, expected_material)

def test_insulation(insulation):
    material = insulation.mpact_material

    num_dens = {'Si' : 0.0016057278006239388, 'O16': 0.003210238459575004, 'O17': 1.2171416728729455e-06}
    expected_material = mpactpy.material.Material(temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = insulation.mpact_build_specs)

    assert materials_are_close(material, expected_material)

def test_control_rod_poison(control_rod_poison):
    material = control_rod_poison.mpact_material

    num_dens = {'Gd152': 2.7319499017784082e-05, 'Gd154': 0.0002977825392938465, 'Gd155': 0.002021642927316022,
                'Gd156': 0.002796150724470201,   'Gd157': 0.0021377507981416044, 'Gd158': 0.0033930817780087833,
                'Gd160': 0.0029860212426438006,  'O16'  : 0.051692735794137225,  'O17'  : 1.9598974877456564e-05,
                'Al27' : 0.02081514033711775}
    expected_material = mpactpy.material.Material(temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = control_rod_poison.mpact_build_specs)

    assert materials_are_close(material, expected_material)

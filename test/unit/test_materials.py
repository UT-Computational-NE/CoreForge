import pytest

from coreforge.materials import Graphite, Inconel, Air, SS304, SS316H, Water, Helium, INOR8, B4C
from coreforge.materials.msre import Salt             as MSRESalt, \
                                     ThimbleGas       as MSREThimbleGas, \
                                     Insulation       as MSREInsulation, \
                                     ControlRodPoison as MSREControlRodPoison


# All tests currently only exercise the factories, but don't actually check isotopics
def test_Graphite():
    material = Graphite(density=1.86, boron_equiv_contamination=0.00008).make_material()

def test_Inconel():
    material = Inconel().make_material()

def test_Air():
    material = Air().make_material()

def test_SS304():
    material = SS304().make_material()

def test_SS316H():
    material = SS316H().make_material()

def test_Water():
    material = Water().make_material()

def test_Helium():
    material = Helium().make_material()

def test_INOR8():
    material = INOR8().make_material()

def test_B4C():
    material = B4C().make_material()

def test_MSRESalt():
    material = MSRESalt().make_material()

def test_MSREThimbleGas():
    material = MSREThimbleGas().make_material()

def test_MSREInsulation():
    material = MSREInsulation().make_material()

def test_MSREControlRodPoison():
    material = MSREControlRodPoison().make_material()

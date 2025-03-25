import pytest
from math import isclose

import mpactpy

from coreforge.materials import Material, Graphite, Inconel, Air, SS304, SS316H, Water, Helium, INOR8, B4C
from coreforge.materials.msre import Salt             as MSRESalt, \
                                     ThimbleGas       as MSREThimbleGas, \
                                     Insulation       as MSREInsulation, \
                                     ControlRodPoison as MSREControlRodPoison


@pytest.fixture
def graphite():
    return Graphite(graphite_density=1.86, boron_equiv_contamination=0.00008)

@pytest.fixture
def inconel():
    return Inconel()

@pytest.fixture
def air():
    return Air()

@pytest.fixture
def ss304():
    return SS304()

@pytest.fixture
def ss316h():
    return SS316H()

@pytest.fixture
def water():
    return Water()

@pytest.fixture
def helium():
    return Helium()

@pytest.fixture
def inor8():
    return INOR8()

@pytest.fixture
def b4c():
    return B4C()

@pytest.fixture
def msre_salt():
    return MSRESalt()

@pytest.fixture
def msre_thimble_gas():
    return MSREThimbleGas()

@pytest.fixture
def msre_insulation():
    return MSREInsulation()

@pytest.fixture
def msre_control_rod_poison():
    return MSREControlRodPoison()

def materials_are_close(lhs: mpactpy.material.Material,
                        rhs: mpactpy.material.Material) -> bool:
    """ Helper function for making sure materials are close

    With the isotopic comparisons, different versions of openmc, and particularly
    different cross-section libraries, will result in different isotopes being
    associated with 'natural' concentrations.  For this testing, the expected_material
    is defined using 'fewer' natural isotopes, and the test material must at least
    have those isotopes.  This allows the test material to have additional `natural`
    isotopes from using different openmc / xs-library versions and the test still pass.
    """

    return (isclose(lhs.density, rhs.density)                                  and
            isclose(lhs.temperature, rhs.temperature)                          and
            lhs.thermal_scattering_isotopes == rhs.thermal_scattering_isotopes and
            lhs.is_fluid                    == rhs.is_fluid                    and
            lhs.is_depletable               == rhs.is_depletable               and
            lhs.has_resonance               == rhs.has_resonance               and
            lhs.is_fuel                     == rhs.is_fuel                     and
            all(iso in lhs.number_densities.keys() for iso in rhs.number_densities.keys()) and
            all(isclose(lhs.number_densities[iso], rhs.number_densities[iso], rel_tol=1E-2)
                for iso in rhs.number_densities.keys()))

def test_initialization(air):
    material = Material(air.openmc_material)
    assert material.name == "Air"
    assert isclose(material.temperature, air.temperature)
    assert isclose(material.density, air.density)
    assert material.number_densities.keys() == air.number_densities.keys()
    assert all(isclose(material.number_densities[iso],
                       air.number_densities[iso])
                       for iso in material.number_densities.keys())
def test_equality(air, graphite):
    material         = Material(air.openmc_material)
    equal_material   = Material(material.openmc_material)
    unequal_material = Material(graphite.openmc_material)
    assert material == equal_material
    assert material != unequal_material

def test_hash(air, graphite):
    material         = Material(air.openmc_material)
    equal_material   = Material(material.openmc_material)
    unequal_material = Material(graphite.openmc_material)
    assert hash(material) == hash(equal_material)
    assert hash(material) != hash(unequal_material)

def test_graphite(graphite):
    material = graphite.mpact_material

    num_dens = {'C'  : 0.0932567267810358, 'B10': 1.642700833205197e-08, 'B11': 6.645396206175213e-08}
    expected_material = mpactpy.material.Material(density                     = 1.86,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = ['C'],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_inconel(inconel):
    material = inconel.mpact_material

    num_dens = {'C'   : 6.644393722101037e-05, 'Si'  : 0.0002906922253419203,   'S'   : 1.2458238228939444e-05,
                'Ti'  : 0.0009551315975520237, 'Al27': 0.0006644393722101035,   'B10' : 9.876891267903188e-07,
                'B11' : 3.995606164785457e-06, 'Cr50': 0.0007578346314663864,   'Cr52': 0.014614086521504498,
                'Cr53': 0.0016571200997841508, 'Cr54': 0.000412492267760185,    'Co59': 0.0008305492152626295,
                'Cu63': 0.00017229743470623248,'Cu65': 7.686732987255636e-05,   'Fe54': 0.0008252752277457118,
                'Fe56': 0.012955056158525243,  'Fe57': 0.00029918874381405704,  'Fe58': 3.981652937969046e-05,
                'Mn55': 0.0002906922253419203, 'Mo92': 0.00040150160999461457,  'Mo94': 0.00025179843614038663,
                'Mo95': 0.0004350491538975026, 'Mo96': 0.0004569756531804361,   'Mo97': 0.00026262464516133504,
                'Mo98': 0.0006657981507262733, 'Mo100': 0.00026706476126612904, 'Ni58': 0.02778096100680029,
                'Ni60': 0.010701176442779044,  'Ni61': 0.00046517273042179734,  'Ni62': 0.0014831742159119416,
                'Ni64': 0.0003777207468009612, 'Nb93': 0.004568020683944462,    'P31': 1.2458238228939442e-05}
    expected_material = mpactpy.material.Material(density                     = 8.19,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = True,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_air(air):
    material = air.mpact_material

    num_dens = {'N14':  3.8309042069284913e-05, 'N15':  1.408419250713269e-07,  'O16':  1.0312753274594694e-05,
                'O17':  3.910015386903025e-09,  'Ar36': 1.5935034402538069e-09, 'Ar38': 3.0045373618694377e-10,
                'Ar40': 4.7577493978213445e-07}
    expected_material = mpactpy.material.Material(density                     = 0.0012,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_ss304(ss304):
    material = ss304.mpact_material

    num_dens = {'C'   : 0.00031687257245297543, 'Si'  : 0.001270453856962005, 'S'   : 4.45126225771339e-05,
                'Mn55': 0.001731947822362768,   'P31' : 6.911885744910015e-05,'Cr50': 0.0007951091418903892,
                'Cr52': 0.015332888352095236,   'Cr53': 0.0017386264573303997,'Cr54': 0.00043278092533274344,
                'Ni58': 0.005793995627837622,   'Ni60': 0.0022318367426887643,'Ni61': 9.701639787023354e-05,
                'Ni62': 0.00030933072906339496, 'Ni64': 7.877741720211267e-05,'N14' : 0.00033841344948970997,
                'N15' : 1.244165844970936e-06,  'Fe54': 0.0033110526543034652,'Fe56': 0.05197644572163562,
                'Fe57': 0.001200362801448938,   'Fe58': 0.00015974625295356323}
    expected_material = mpactpy.material.Material(density                     = 7.90,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = True,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_ss316h(ss316h):
    material = ss316h.mpact_material

    num_dens = {'C'    : 0.000401104522092374,  'Si'   : 0.0012865355513539292, 'S'    : 4.50760734958318e-05,
                'Cr50' : 0.0007246564331152913, 'Cr52' : 0.013974277991783001,  'Cr53' : 0.0015845709484530223,
                'Cr54' : 0.00039443324840452576,'Ni58' : 0.00782311645952759,   'Ni60' : 0.0030134504542633097,
                'Ni61' : 0.00013099260471930268,'Ni62' : 0.00041766174388306506,'Ni64' : 0.00010636613293112259,
                'Mo92' : 0.0002206635899282463, 'Mo94' : 0.00013838735754459678,'Mo95' : 0.0002391011784375079,
                'Mo96' : 0.00025115188988146964,'Mo97' : 0.00014433739632005297,'Mo98' : 0.00036591985299590127,
                'Mo100': 0.00014677766538745524,'Mn55' : 0.0017538712125192586, 'P31'  : 6.999377969529131e-05,
                'Fe54' : 0.003130089248410418,  'Fe56' : 0.049135707253832255,  'Fe57' : 0.0011347577617419463,
                'Fe58' : 0.00015101542652724343}
    expected_material = mpactpy.material.Material(density                     = 8.0,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = True,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_water(water):
    material = water.mpact_material

    num_dens = {'H'  : 0.06687084844887618, 'O16': 0.03342275219865702, 'O17': 1.2672025781062035e-05}
    expected_material = mpactpy.material.Material(density                     = 1.0,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = ['H'],
                                                  is_fluid                    = True,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_helium(helium):
    material = helium.mpact_material

    num_dens = {'He3': 5.370665761547269e-11,
                'He4': 2.6853275101078733e-05}
    expected_material = mpactpy.material.Material(density                     = 0.00017848,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_inor8(inor8):
    material = inor8.mpact_material

    num_dens = {'C'    : 0.0002639618721824652, 'Si'   : 0.001539026944633406,  'S'    : 2.6368000459278417e-05,
                'Ti'   : 0.0002257525732369653, 'Ni58' : 0.041676675048575806,  'Ni60' : 0.016053780613781005,
                'Ni61' : 0.0006978467275664952, 'Ni62' : 0.002225040732819044,  'Ni64' : 0.0005666522774239392,
                'Mo92' : 0.0013714839744596564, 'Mo94' : 0.0008601149070490042, 'Mo95' : 0.0014860785805582719,
                'Mo96' : 0.0015609770159168439, 'Mo97' : 0.0008970960095072995, 'Mo98' : 0.0022742909896630464,
                'Mo100': 0.0009122629426674101, 'Cr50' : 0.0003090936465735477, 'Cr52' : 0.00596056330327986,
                'Cr53' : 0.0006758800313222732, 'Cr54' : 0.0001682408456033235, 'Fe54' : 0.0002765300856844263,
                'Fe56' : 0.004340930963539581,  'Fe57' : 0.00010025102678619322,'Fe58' : 1.3341571285373518e-05,
                'Al27' : 0.00040049756947749916,'Mn55' : 0.0007867801585360432, 'Cu63' : 0.00016445345808847056,
                'Cu65' : 7.336788404959243e-05, 'B10'  : 7.74939702202097e-06,  'B11'  : 3.1349477962948606e-05,
                'W180' : 1.410696599225658e-07, 'W182' : 3.115288323289996e-05, 'W183' : 1.6822556945765977e-05,
                'W184' : 3.601978650022848e-05, 'W186' : 3.342175359665455e-05, 'P31'  : 2.047201399787779e-05,
                'Co59' : 0.00014704733332743196}
    expected_material = mpactpy.material.Material(density                     = 8.7745,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = True,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_b4c(b4c):
    material = b4c.mpact_material

    num_dens = {'C'  : 0.019180730627934073, 'B10': 0.015206483241826132, 'B11': 0.06151643926991015}
    expected_material = mpactpy.material.Material(density                     = 1.76,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_msre_salt(msre_salt):
    material = msre_salt.mpact_material

    num_dens = {'Li6' : 1.7431446223252428e-06, 'Li7' : 0.02988796955594127,   'F19' : 0.05218107467967278,
                'Be9' : 0.00898964129413786,    'Zr90': 0.00047974094545786845,'Zr91': 0.00010461989131267802,
                'Zr92': 0.00015991364848595618, 'Zr94': 0.00016205826301375617,'Zr96': 2.6108350773217338e-05,
                'U234': 4.115361955751947e-07,  'U235': 4.604270687345431e-05, 'U236': 2.1089771252934387e-07,
                'U238': 9.891360788333172e-05}
    expected_material = mpactpy.material.Material(density                     = 2.3275,
                                                  temperature                 = 900.,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = True,
                                                  is_depletable               = True,
                                                  has_resonance               = True,
                                                  is_fuel                     = True)

    assert materials_are_close(material, expected_material)

def test_msre_thimble_gas(msre_thimble_gas):
    material = msre_thimble_gas.mpact_material

    num_dens = {'N14': 5.1248390373520565e-05, 'N15': 1.884130107967543e-07, 'O16': 2.3697368312685885e-06,
                'O17': 8.984707794762167e-10}
    expected_material = mpactpy.material.Material(density                     = 0.00125932,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_msre_insulation(msre_insulation):
    material = msre_insulation.mpact_material

    num_dens = {'Si' : 0.0016057278006239388, 'O16': 0.003210238459575004, 'O17': 1.2171416728729455e-06}
    expected_material = mpactpy.material.Material(density                     = 0.160185,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = False,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

def test_msre_control_rod_poison(msre_control_rod_poison):
    material = msre_control_rod_poison.mpact_material

    num_dens = {'Gd152': 2.7319499017784082e-05, 'Gd154': 0.0002977825392938465, 'Gd155': 0.002021642927316022,
                'Gd156': 0.002796150724470201,   'Gd157': 0.0021377507981416044, 'Gd158': 0.0033930817780087833,
                'Gd160': 0.0029860212426438006,  'O16'  : 0.051692735794137225,  'O17'  : 1.9598974877456564e-05,
                'Al27' : 0.02081514033711775}
    expected_material = mpactpy.material.Material(density                     = 5.873,
                                                  temperature                 = 273.15,
                                                  number_densities            = num_dens,
                                                  thermal_scattering_isotopes = [],
                                                  is_fluid                    = False,
                                                  is_depletable               = False,
                                                  has_resonance               = True,
                                                  is_fuel                     = False)

    assert materials_are_close(material, expected_material)

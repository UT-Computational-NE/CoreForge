import pytest
from math import isclose

import mpactpy

from coreforge.materials import Material, Graphite, Inconel, Air, SS304, SS316H, Water, Helium, INOR8, B4C, Mo, Zr, UZrH, Al6061T6
import coreforge.mpact_builder as mpact_builder

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
def mo():
    return Mo()

@pytest.fixture
def zr():
    return Zr()

@pytest.fixture
def uzrh():
    return UZrH()

@pytest.fixture
def al6061t6():
    return Al6061T6()

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

    return (isclose(lhs.density, rhs.density)            and
            isclose(lhs.temperature, rhs.temperature)    and
            lhs.replace_isotopes == rhs.replace_isotopes and
            lhs.is_fluid         == rhs.is_fluid         and
            lhs.is_depletable    == rhs.is_depletable    and
            lhs.has_resonance    == rhs.has_resonance    and
            lhs.is_fuel          == rhs.is_fuel          and
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
    material = mpact_builder.build_material(graphite)

    num_dens = {'C'  : 0.0932567267810358, 'B10': 1.642700833205197e-08, 'B11': 6.645396206175213e-08}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[Graphite])

    assert materials_are_close(material, expected_material)

def test_inconel(inconel):
    material = mpact_builder.build_material(inconel)

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
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[Inconel])

    assert materials_are_close(material, expected_material)

def test_air(air):
    material = mpact_builder.build_material(air)

    num_dens = {'N14':  3.8309042069284913e-05, 'N15':  1.408419250713269e-07,  'O16':  1.0312753274594694e-05,
                'O17':  3.910015386903025e-09,  'Ar36': 1.5935034402538069e-09, 'Ar38': 3.0045373618694377e-10,
                'Ar40': 4.7577493978213445e-07}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[Air])

    assert materials_are_close(material, expected_material)

def test_ss304(ss304):
    material = mpact_builder.build_material(ss304)

    num_dens = {'C'   : 0.00031687257245297543, 'Si'  : 0.001270453856962005, 'S'   : 4.45126225771339e-05,
                'Mn55': 0.001731947822362768,   'P31' : 6.911885744910015e-05,'Cr50': 0.0007951091418903892,
                'Cr52': 0.015332888352095236,   'Cr53': 0.0017386264573303997,'Cr54': 0.00043278092533274344,
                'Ni58': 0.005793995627837622,   'Ni60': 0.0022318367426887643,'Ni61': 9.701639787023354e-05,
                'Ni62': 0.00030933072906339496, 'Ni64': 7.877741720211267e-05,'N14' : 0.00033841344948970997,
                'N15' : 1.244165844970936e-06,  'Fe54': 0.0033110526543034652,'Fe56': 0.05197644572163562,
                'Fe57': 0.001200362801448938,   'Fe58': 0.00015974625295356323}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[SS304])

    assert materials_are_close(material, expected_material)

def test_ss316h(ss316h):
    material = mpact_builder.build_material(ss316h)

    num_dens = {'C'    : 0.000401104522092374,  'Si'   : 0.0012865355513539292, 'S'    : 4.50760734958318e-05,
                'Cr50' : 0.0007246564331152913, 'Cr52' : 0.013974277991783001,  'Cr53' : 0.0015845709484530223,
                'Cr54' : 0.00039443324840452576,'Ni58' : 0.00782311645952759,   'Ni60' : 0.0030134504542633097,
                'Ni61' : 0.00013099260471930268,'Ni62' : 0.00041766174388306506,'Ni64' : 0.00010636613293112259,
                'Mo92' : 0.0002206635899282463, 'Mo94' : 0.00013838735754459678,'Mo95' : 0.0002391011784375079,
                'Mo96' : 0.00025115188988146964,'Mo97' : 0.00014433739632005297,'Mo98' : 0.00036591985299590127,
                'Mo100': 0.00014677766538745524,'Mn55' : 0.0017538712125192586, 'P31'  : 6.999377969529131e-05,
                'Fe54' : 0.003130089248410418,  'Fe56' : 0.049135707253832255,  'Fe57' : 0.0011347577617419463,
                'Fe58' : 0.00015101542652724343}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[SS316H])

    assert materials_are_close(material, expected_material)

def test_water(water):
    material = mpact_builder.build_material(water)

    num_dens = {'H'  : 0.06687084844887618, 'O16': 0.03342275219865702, 'O17': 1.2672025781062035e-05}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[Water])

    assert materials_are_close(material, expected_material)

def test_helium(helium):
    material = mpact_builder.build_material(helium)

    print(helium.number_densities)
    num_dens = {'He3': 4.996933865769493e-11,
                'He4': 2.4984619359508816e-05}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[Helium])

    assert materials_are_close(material, expected_material)

def test_inor8(inor8):
    material = mpact_builder.build_material(inor8)

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
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[INOR8])

    assert materials_are_close(material, expected_material)

def test_b4c(b4c):
    material = mpact_builder.build_material(b4c)

    num_dens = {'C'  : 0.019180730627934073, 'B10': 0.015206483241826132, 'B11': 0.06151643926991015}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[B4C])

    assert materials_are_close(material, expected_material)

def test_mo(mo):
    material = mpact_builder.build_material(mo)

    num_dens = {'Mo92': 0.009549482369139634, 'Mo94': 0.005967618298385837, 'Mo95': 0.010280079192235626,
                'Mo96': 0.010784384963930204, 'Mo97': 0.0061809784325643135, 'Mo98': 0.015639944381143384,
                'Mo100': 0.006252098477290471}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[Mo])

    assert materials_are_close(material, expected_material)

def test_zr(zr):
    material = mpact_builder.build_material(zr)

    num_dens = {'Zr90': 0.022077110297960726, 'Zr91': 0.004814483528534876, 'Zr92': 0.00735903676598691,
                'Zr94': 0.007457729387338338, 'Zr96': 0.0012014753903652098}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[Zr])

    assert materials_are_close(material, expected_material)

def test_uzrh(uzrh):
    material = mpact_builder.build_material(uzrh)

    num_dens = {'Zr'  : 0.03236252669648184,    'H'   : 0.05017992823867929,    'Mn55': 9.161779589954229e-05,
                'U235': 0.00022782770293680135, 'U238': 0.0009111657877251246,  'Cr50': 3.9958261676252606e-05,
                'Cr52': 0.0007705553020924119,  'Cr53': 8.737478577355029e-05,  'Cr54': 2.174943357061851e-05,
                'Fe54': 0.00018306448319297205, 'Fe56': 0.0028737208880903267,  'Fe57': 6.636674762804238e-05,
                'Fe58': 8.83219576739403e-06,   'Ni58': 0.00027730385362067074, 'Ni60': 0.00010681694794974817,
                'Ni61': 4.6432587668093355e-06, 'Ni62': 1.480474075617908e-05,  'Ni64': 3.7703310067187678e-06}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[UZrH])

    assert materials_are_close(material, expected_material)

def test_al6061t6(al6061t6):
    material = mpact_builder.build_material(al6061t6)

    num_dens = {'Mg24': 0.0005351155852920017,  'Mg25': 6.503067876051443e-05, 'Mg26': 6.8851718642783e-05,
                'Si28': 0.00032153335601827154, 'Si29': 1.577116461221087e-05, 'Si30': 1.0062105023655176e-05,
                'B10' : 2.3945249929578925e-07, 'Al27': 0.05901561597803719,   'Cr50': 2.6872280480586553e-06,
                'Cr52': 4.983052010820289e-05,  'Cr53': 5.543557861124277e-06, 'Cr54': 1.3544141367559698e-06,
                'Cu63': 5.001752206004382e-05,  'Cu65': 2.1628225745539073e-05}
    expected_material = mpactpy.material.Material(temperature                 = 293.6,
                                                  number_densities            = num_dens,
                                                  mpact_specs                 = mpact_builder.DEFAULT_MPACT_SPECS[Al6061T6])

    assert materials_are_close(material, expected_material)


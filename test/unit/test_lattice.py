import pytest
from copy import deepcopy
from math import isclose, sqrt

import openmc
from numpy.testing import assert_allclose
from mpactpy import RectangularPinMesh, GeneralCylindricalPinMesh, Pin

from coreforge.geometry_elements import RectLattice, HexLattice, CylindricalPinCell
from coreforge.materials import unique_materials
import coreforge.openmc_builder as openmc_builder
import coreforge.mpact_builder as mpact_builder
from test.unit.test_materials import graphite
from test.unit.msre.test_materials import salt
from test.unit.test_pincell import cylindrical_pincell as pincell, \
                                   cylindrical_pincell_mpact_specs as pincell_mpact_specs
from test.unit.test_stack import stack, unequal_stack, stack_mpact_specs

@pytest.fixture
def rect_lattice(graphite, stack, unequal_stack):
    p1 = stack
    p2 = unequal_stack
    elements = [[None,  p1, None],
                [  p2,  p1,   p2],
                [None,  p1, None]]
    return RectLattice(pitch=(8., 8.), elements=elements, outer_material=graphite)

@pytest.fixture
def unequal_rect_lattice(graphite, stack, unequal_stack):
    p1 = stack
    p2 = unequal_stack
    elements = [[None,  p1, None],
                [  p2,  p1,   p2],
                [None,  p2, None]]
    return RectLattice(pitch=(8., 8.), elements=elements, outer_material=graphite)

@pytest.fixture
def rect_lattice_mpact_specs(stack, unequal_stack, stack_mpact_specs):
    return mpact_builder.RectLattice.Specs(element_specs={stack:         stack_mpact_specs,
                                                          unequal_stack: stack_mpact_specs})

@pytest.fixture
def hex_x_lattice(graphite, stack, unequal_stack):
    p1 = stack
    p2 = unequal_stack
    elements = [[   p1,   p1,   ],

                [p2,   p2,  p1, ],

                [   p1,   p1,   ]]
    return HexLattice(pitch=6., outer_material=graphite, orientation='x', elements=elements, map_type='offset')

@pytest.fixture
def hex_y_lattice(graphite, stack, unequal_stack):
    p1 = stack
    p2 = unequal_stack
    elements = [[     p1     ],
                [p1,       p1],
                [     p2,    ],
                [p2,       p1],
                [     p1     ]]
    return HexLattice(pitch=6., outer_material=graphite, orientation='y', elements=elements, map_type='offset')

@pytest.fixture
def hex_lattice_mpact_specs(stack, unequal_stack, stack_mpact_specs):
    return mpact_builder.HexLattice.Specs(element_specs={stack:         stack_mpact_specs,
                                                         unequal_stack: stack_mpact_specs})

@pytest.fixture
def mpact_voxel_specs(salt, graphite):
    mat_specs = {
        salt:     mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS[type(salt)],
        graphite: mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS[type(graphite)],
    }

    return mpact_builder.VoxelBuilder.Specs(
        target_thicknesses = {"X": 1.0, "Y": 1.0, "Z": 1.0},
        material_specs     = mat_specs
    )

def test_rect_lattice_initialization(rect_lattice, stack, unequal_stack):
    p1 = stack
    p2 = unequal_stack
    geom_element = rect_lattice
    assert geom_element.name == "rect_lattice"
    assert geom_element.shape[0] == 3
    assert geom_element.shape[1] == 3
    assert isclose(geom_element.pitch[0], 8.0)
    assert isclose(geom_element.pitch[1], 8.0)
    assert geom_element.elements == [[None,  p1, None],
                                     [  p2,  p1,   p2],
                                     [None,  p1, None]]
    expected = [geom_element.outer_material]
    for row in geom_element.elements:
        for element in row:
            if element is not None:
                expected.extend(element.get_materials())
    assert geom_element.get_materials() == unique_materials(expected)


def test_rect_lattice_equality(rect_lattice, unequal_rect_lattice):
    assert rect_lattice == deepcopy(rect_lattice)
    assert rect_lattice != unequal_rect_lattice

def test_rect_lattice_hash(rect_lattice, unequal_rect_lattice):
    assert hash(rect_lattice) == hash(deepcopy(rect_lattice))
    assert hash(rect_lattice) != hash(unequal_rect_lattice)

def test_rect_lattice_openmc_builder(rect_lattice):
    geom_element = rect_lattice
    universe = openmc_builder.build(geom_element)
    lattice = next(iter(universe.cells.values())).fill
    assert lattice.shape[0] == 3
    assert lattice.shape[1] == 3
    assert isclose(lattice.pitch[0], 8.0)
    assert isclose(lattice.pitch[1], 8.0)

def test_rect_lattice_mpact_builder(rect_lattice, rect_lattice_mpact_specs, stack):
    geom_element = rect_lattice
    core         = mpact_builder.build(geom_element, rect_lattice_mpact_specs)
    assert isclose(core.mod_dim['X'], 8.0)
    assert isclose(core.mod_dim['Y'], 8.0)
    assert_allclose(core.mod_dim['Z'], [1.0, 3.0, 4.0])
    assert core.nx == 3
    assert core.ny == 3
    assert core.nz == 3
    assert isclose(core.height, 8.0)

    assert len(core.pins)       == 3
    assert len(core.modules)    == 3
    assert len(core.lattices)   == 3
    assert len(core.assemblies) == 1 # This is one because the axial mesh unionization results in only one unique assembly

    for assembly in core.assemblies:
        assert len(assembly.lattice_map) == 3
        assert isclose(assembly.lattice_map[0].pitch['Z'], 3.0)
        assert isclose(assembly.lattice_map[1].pitch['Z'], 1.0)
        assert isclose(assembly.lattice_map[2].pitch['Z'], 4.0)

    p1 = stack
    p2 = rect_lattice
    elements = [[None,  p1, None],
                [  p2,  p1,   p1],
                [None,  p1, None]]
    geom_element = RectLattice(pitch=(8., 8.), elements=elements, outer_material=graphite)
    mpact_build_specs = rect_lattice_mpact_specs
    mpact_build_specs.element_specs[rect_lattice] = rect_lattice_mpact_specs
    expected_assertion = "RectLattice builder does not accept X or Y bounds - they are determined by lattice pitch"
    with pytest.raises(AssertionError, match=expected_assertion):
        core = mpact_builder.build(geom_element, mpact_build_specs)


def test_hex_lattice_initialization(hex_x_lattice, hex_y_lattice, stack, unequal_stack):
    p1 = stack
    p2 = unequal_stack
    geom_element = hex_x_lattice
    assert geom_element.name == "hex_lattice"
    assert geom_element.num_rings == 2
    assert geom_element.orientation == "x"
    assert isclose(geom_element.pitch, 6.0)
    expected_elements = [[p1, p1, p1, p2, p1, p1], [p2]]
    for ring, expected_ring in zip(geom_element.elements, expected_elements):
        assert len(ring) == len(expected_ring)
        for i, element, expected_element in zip(range(len(ring)), ring, expected_ring):
            assert element == expected_element
    expected = [geom_element.outer_material]
    for ring in geom_element.elements:
        for element in ring:
            if element is not None:
                expected.extend(element.get_materials())
    assert geom_element.get_materials() == unique_materials(expected)

    geom_element = hex_y_lattice
    assert geom_element.name == "hex_lattice"
    assert geom_element.num_rings == 2
    assert geom_element.orientation == "y"
    assert isclose(geom_element.pitch, 6.0)
    expected_elements = [[p1, p1, p1, p1, p2, p1], [p2]]
    for ring, expected_ring in zip(geom_element.elements, expected_elements):
        assert len(ring) == len(expected_ring)
        for element, expected_element in zip(ring, expected_ring):
            assert element == expected_element
    expected = [geom_element.outer_material]
    for ring in geom_element.elements:
        for element in ring:
            if element is not None:
                expected.extend(element.get_materials())
    assert geom_element.get_materials() == unique_materials(expected)

def test_hex_lattice_equality(hex_x_lattice, hex_y_lattice):
    assert hex_x_lattice == deepcopy(hex_x_lattice)
    assert hex_x_lattice != hex_y_lattice

def test_hex_lattice_hash(hex_x_lattice, hex_y_lattice):
    assert hash(hex_x_lattice) == hash(deepcopy(hex_x_lattice))
    assert hash(hex_x_lattice) != hash(hex_y_lattice)

def test_hex_lattice_openmc_builder(hex_x_lattice, hex_y_lattice):
    geom_element = hex_x_lattice
    universe = openmc_builder.build(geom_element)
    lattice = next(iter(universe.cells.values())).fill
    assert lattice.orientation == 'x'
    assert lattice.num_rings == 2
    assert isclose(lattice.pitch[0], 6.0)

    geom_element = hex_y_lattice
    universe = openmc_builder.build(geom_element)
    lattice = next(iter(universe.cells.values())).fill
    assert lattice.orientation == 'y'
    assert lattice.num_rings == 2
    assert isclose(lattice.pitch[0], 6.0)

def test_hex_lattice_mpact_ring_positions(hex_x_lattice, hex_y_lattice):
    builder = mpact_builder.HexLattice()

    assert builder._ring_to_offset_positions(hex_y_lattice) == [
        (0, 2), (1, 4), (3, 4), (4, 2), (3, 0), (1, 0), (2, 2)
    ]
    assert builder._ring_to_offset_positions(hex_x_lattice) == [
        (2, 4), (4, 3), (4, 1), (2, 0), (0, 1), (0, 3), (2, 2)
    ]


def _cylinder_radii(universe):
    radii = []
    for cell in universe.cells.values():
        if cell.region is not None:
            radii += [s.r for s in cell.region.get_surfaces().values()
                      if isinstance(s, (openmc.Cylinder, openmc.ZCylinder))]
        if isinstance(cell.fill, openmc.UniverseBase):
            radii += _cylinder_radii(cell.fill)
    return radii


@pytest.mark.parametrize("orientation", ["x", "y"])
def test_hex_lattice_mpact_builder_matches_openmc(salt, graphite, orientation):
    """ Every element must be placed in MPACT at the centre of the OpenMC lattice cell that holds it """

    num_rings, pitch = 4, 6.0
    ring_sizes = [6 * (num_rings - 1 - i) for i in range(num_rings - 1)] + [1]
    element_by_radius, rings = {}, []
    for size in ring_sizes:
        ring = []
        for _ in range(size):
            radius = round(0.5 + 0.05 * len(element_by_radius), 6)
            element_by_radius[radius] = len(element_by_radius)
            ring.append(CylindricalPinCell(radii=[radius], materials=[salt, graphite],
                                           name=f"pin{element_by_radius[radius]}"))
        rings.append(ring)
    lattice = HexLattice(pitch=pitch, outer_material=graphite, elements=rings,
                         orientation=orientation, map_type='ring')

    core = mpact_builder.build(lattice)
    quad_width, quad_height = core.mod_dim['X'], core.mod_dim['Y']
    num_rows, num_cols = len(core.assembly_map), len(core.assembly_map[0])
    mpact_centres = {}
    for i, row in enumerate(core.assembly_map):
        for j, assembly in enumerate(row):
            if assembly is None:
                continue
            for pin in assembly.pins:
                mesh = pin.pinmesh
                if isinstance(mesh, GeneralCylindricalPinMesh):
                    # MPACT core is centred on the lattice centre; gcyl bounds are relative to the hex centre
                    x = (j - 0.5 * num_cols) * quad_width - mesh.xMin
                    y = (num_rows - 1 - i - 0.5 * num_rows) * quad_height - mesh.yMin
                    element = element_by_radius[round(mesh.r[-1], 6)]
                    mpact_centres.setdefault(element, set()).add((round(x, 6), round(y, 6)))

    assert len(mpact_centres) == len(element_by_radius)
    openmc_lattice = next(iter(openmc_builder.build(lattice).cells.values())).fill
    for element, centres in mpact_centres.items():
        assert len(centres) == 1, f"quadrants of element {element} disagree on its centre: {centres}"
        x, y = next(iter(centres))
        (ix, ia, *_), local = openmc_lattice.find_element((x, y, 0.0))
        assert isclose(local[0], 0.0, abs_tol=1e-6) and isclose(local[1], 0.0, abs_tol=1e-6), \
            f"element {element} at ({x}, {y}) is not on an OpenMC lattice cell centre"
        universe = openmc_lattice.get_universe((ix, ia))
        radii = {round(r, 6) for r in _cylinder_radii(universe)}
        assert {element_by_radius.get(r) for r in radii} == {element}, \
            f"element {element} at ({x}, {y}) is element(s) {radii} in OpenMC"

def test_hex_lattice_mpact_builder_x_oriented(hex_x_lattice, hex_lattice_mpact_specs, stack):
    geom_element = hex_x_lattice
    core = mpact_builder.build(geom_element, hex_lattice_mpact_specs)
    hex_width  = geom_element.pitch
    hex_height = geom_element.pitch * sqrt(3.0) / 2.0
    assert isclose(core.mod_dim['X'], hex_width/2)
    assert isclose(core.mod_dim['Y'], hex_height/2)
    assert_allclose(core.mod_dim['Z'], [1.0, 3.0, 4.0])
    assert core.nx == 6
    assert core.ny == 6
    assert core.nz == 3
    assert isclose(core.height, 8.0)

    assert len(core.pins)       == 12
    assert len(core.modules)    == 12
    assert len(core.lattices)   == 12
    assert len(core.assemblies) == 4

    for assembly in core.assemblies:
        assert len(assembly.lattice_map) == 3
        assert isclose(assembly.lattice_map[0].pitch['Z'], 3.0)
        assert isclose(assembly.lattice_map[1].pitch['Z'], 1.0)
        assert isclose(assembly.lattice_map[2].pitch['Z'], 4.0)


def test_hex_lattice_mpact_builder_y_oriented(hex_y_lattice, hex_lattice_mpact_specs, stack):
    geom_element = hex_y_lattice
    core = mpact_builder.build(geom_element, hex_lattice_mpact_specs)
    hex_width  = geom_element.pitch * sqrt(3.0) / 2.0
    hex_height = geom_element.pitch
    assert isclose(core.mod_dim['X'], hex_width/2)
    assert isclose(core.mod_dim['Y'], hex_height/2)
    assert_allclose(core.mod_dim['Z'], [1.0, 3.0, 4.0])
    assert core.nx == 6
    assert core.ny == 6
    assert core.nz == 3
    assert isclose(core.height, 8.0)

    assert len(core.pins)       == 12
    assert len(core.modules)    == 12
    assert len(core.lattices)   == 12
    assert len(core.assemblies) == 4

    for assembly in core.assemblies:
        assert len(assembly.lattice_map) == 3
        assert isclose(assembly.lattice_map[0].pitch['Z'], 3.0)
        assert isclose(assembly.lattice_map[1].pitch['Z'], 1.0)
        assert isclose(assembly.lattice_map[2].pitch['Z'], 4.0)

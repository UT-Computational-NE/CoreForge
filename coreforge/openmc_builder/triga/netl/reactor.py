from typing import Tuple

import openmc

from coreforge.geometry_elements.cylindrical_stack import CylindricalStack
from coreforge.openmc_builder.builder import Builder
from coreforge.openmc_builder.openmc_builder import register_builder, build
from coreforge.shapes import Hexagon
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl

@register_builder(geometry_elements_triga_netl.Reactor)
class Reactor(Builder[geometry_elements_triga_netl.Reactor]):
    """ An OpenMC geometry builder class for a TRIGA NETL Reactor
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga_netl.Reactor) -> openmc.Universe:
        pool_height = element.pool.height
        pool_region = -openmc.model.RightCircularCylinder(radius = element.pool.radius,
                                                          height = pool_height,
                                                          center_base = (0.0, 0.0, -pool_height*0.5),
                                                          boundary_type='vacuum',
                                                          axis   = 'z')

        def build_beam_port_surfaces(beamport: geometry_elements_triga_netl.Reactor.BeamPort
        ) -> Tuple[openmc.model.RightCircularCylinder, openmc.model.RightCircularCylinder]:
            """ Helper to build OpenMC surfaces for a beam port."""
            surfaces = []
            length = beamport.geometry.length
            for radius in (beamport.geometry.inner_radius, beamport.geometry.outer_radius):
                surface = openmc.model.RightCircularCylinder(radius = radius,
                                                             height = length,
                                                             center_base = (-length * 0.5, 0.0, 0.0),
                                                             axis   = 'x')
                surface = surface.rotate((0.0, 0.0, beamport.rotation)).translate(beamport.translation)
                surfaces.append(surface)
            return surfaces[0], surfaces[1]

        cells = []
        for beamport_id in (1, 2, 3, 4):
            beamport = element.beam_port[beamport_id]
            inner_surface, outer_surface = build_beam_port_surfaces(beamport)
            cells.append(openmc.Cell(fill   = beamport.geometry.fill_material.openmc_material,
                                     region = -inner_surface & pool_region,
                                     name=beamport.geometry.name + "_fill"))
            cells.append(openmc.Cell(fill   = beamport.geometry.tube_material.openmc_material,
                                     region = +inner_surface & -outer_surface & pool_region,
                                     name=beamport.geometry.name + "_tube"))
            pool_region &= +outer_surface

        cells.append(openmc.Cell(fill   = build_pool(element),
                                 region = pool_region,
                                 name   = "reactor_pool"))

        return openmc.Universe(cells=cells, name=element.name)


def build_pool(reactor: geometry_elements_triga_netl.Reactor) -> openmc.Universe:
    """ Helper to build an OpenMC universe for reactor pool.

    Parameters
    ----------
    reactor: geometry_elements_triga_netl.Reactor
        The geometry element whose pool is to be built

    Returns
    -------
    openmc.Universe
        Universe containing the pool.
    """

    reflector_radius        = openmc.ZCylinder(r = reactor.reflector.geometry.radius)
    top_of_reflector        = openmc.ZPlane(z0 = reactor.reflector.axial_bounds.upper)
    bottom_of_reflector     = openmc.ZPlane(z0 = reactor.reflector.axial_bounds.lower)
    bottom_of_rsr_cavity    = openmc.ZPlane(z0 = reactor.rotary_specimen_rack_cavity.axial_bounds.lower)
    rsr_cavity_outer_radius = openmc.ZCylinder(
                                  r = reactor.rotary_specimen_rack_cavity.outer_radius)
    primary_hex_shape       = Hexagon(inner_radius= reactor.shroud.primary_hex_inner_radius +
                                      reactor.shroud.thickness)
    rotated_hex_shape       = Hexagon(inner_radius= reactor.shroud.rotated_hex_inner_radius +
                                      reactor.shroud.thickness)

    primary_hex    = openmc.model.HexagonalPrism(edge_length = primary_hex_shape.outer_radius,
                                                  orientation = 'y')
    rotated_hex    = openmc.model.HexagonalPrism(edge_length = rotated_hex_shape.outer_radius,
                                                 orientation = 'y').rotate((0, 0, 30))
    shroud_region  = -primary_hex & -rotated_hex

    cells = []
    cells.append(openmc.Cell(fill   = build_shroud(reactor),
                             region = shroud_region,
                             name   = "shroud"))
    cells.append(openmc.Cell(fill   = build_rsr_cavity(reactor),
                             region = -top_of_reflector & +bottom_of_rsr_cavity &
                                      -rsr_cavity_outer_radius & ~shroud_region,
                             name   = "rsr_cavity"))
    cells.append(openmc.Cell(fill   = reactor.reflector.geometry.material.openmc_material,
                             region = -top_of_reflector & +bottom_of_reflector & -reflector_radius &
                                      ~(-rsr_cavity_outer_radius & +bottom_of_rsr_cavity),
                             name   = "reflector"))
    cells.append(openmc.Cell(fill   = reactor.pool.material.openmc_material,
                             region = +reflector_radius |
                                      (-reflector_radius & ~shroud_region &
                                      (-bottom_of_reflector | +top_of_reflector)),
                             name   = "pool"))

    return openmc.Universe(cells=cells)

def build_rsr_cavity(reactor: geometry_elements_triga_netl.Reactor) -> openmc.Universe:
    """ Helper to build an OpenMC universe for reactor RSR cavity.

    Parameters
    ----------
    reactor: geometry_elements_triga_netl.Reactor
        The geometry element whose RSR cavity is to be built

    Returns
    -------
    openmc.Universe
        Universe containing the RSR cavity.
    """

    rsr = reactor.rotary_specimen_rack_cavity
    outer_radius = rsr.tube_outer_boundary.r
    inner_radius = outer_radius - rsr.tube_specs.thickness

    cavity_fill_material = rsr.material.openmc_material
    tube_clad_material   = rsr.tube_specs.material.openmc_material

    cells          = []
    outside_region = None
    for i, (x, y) in enumerate(rsr.tube_centers, start=1):
        tube  = f"rsr_tube_{i:02d}"
        inner_surface = openmc.ZCylinder(r=inner_radius, x0=x, y0=y, name=tube+"_id")
        outer_surface = openmc.ZCylinder(r=outer_radius, x0=x, y0=y, name=tube+"_od")
        cells.append(openmc.Cell(fill   = cavity_fill_material,
                                 region = -inner_surface,
                                 name   = tube+"_fill"))
        cells.append(openmc.Cell(fill   = tube_clad_material,
                                 region = -outer_surface & +inner_surface,
                                 name   = tube+"_clad"))
        outside_region = +outer_surface if outside_region is None else outside_region & +outer_surface

    cells.append(openmc.Cell(fill= cavity_fill_material, region=outside_region, name="rsr_cavity_fill"))

    return openmc.Universe(cells=cells)

def build_shroud(reactor: geometry_elements_triga_netl.Reactor) -> openmc.Universe:
    """ Helper to build an OpenMC universe for reactor shroud.

    Parameters
    ----------
    reactor: geometry_elements_triga_netl.Reactor
        The geometry element whose shroud is to be built

    Returns
    -------
    openmc.Universe
        Universe containing the shroud.
    """

    primary_hex_shape = Hexagon(inner_radius= reactor.shroud.primary_hex_inner_radius)
    rotated_hex_shape = Hexagon(inner_radius= reactor.shroud.rotated_hex_inner_radius)

    primary_hex    = openmc.model.HexagonalPrism(edge_length = primary_hex_shape.outer_radius,
                                                 orientation = 'y')
    rotated_hex   = openmc.model.HexagonalPrism(edge_length = rotated_hex_shape.outer_radius,
                                                 orientation = 'y').rotate((0, 0, 30))
    shroud_top    = openmc.ZPlane(z0 = reactor.shroud.axial_bounds.upper)
    shroud_bottom = openmc.ZPlane(z0 = reactor.shroud.axial_bounds.lower)

    shroud_region = ~(-primary_hex & -rotated_hex) & (-shroud_top & +shroud_bottom)

    core_cell    = openmc.Cell(fill=build_core_lattice(reactor), region=~shroud_region)
    shroud_cell  = openmc.Cell(fill=reactor.shroud.material.openmc_material, region=shroud_region)


    return openmc.Universe(cells=[core_cell,shroud_cell])


def build_core_lattice(reactor: geometry_elements_triga_netl.Reactor) -> openmc.Lattice:
    """Helper to build an OpenMC lattice for reactor the core.

    Parameters:
    -----------
    reactor: geometry_elements_triga_netl.Reactor
        The geometry element whose core lattice is to be built

    Returns
    -------
    openmc.Lattice
        Lattice containing the full core.
    """

    grid_plate_specs = geometry_elements_triga_netl.Reactor.CoreCellSpecs.GridPlateSpecs
    outer_core_cell_specs = geometry_elements_triga_netl.Reactor.CoreCellSpecs(
        location="outer",
        outer_material=reactor.core.fill_material,
        upper_grid_plate=grid_plate_specs(
            axial_bounds=reactor.upper_grid_plate.axial_bounds,
            material=reactor.upper_grid_plate.geometry.material,
            penetration_radius=None,
        ),
        lower_grid_plate=grid_plate_specs(
            axial_bounds=reactor.lower_grid_plate.axial_bounds,
            material=reactor.lower_grid_plate.geometry.material,
            penetration_radius=None,
        ),
    )
    outer_universe = build_core_element(core_cell_specs=outer_core_cell_specs)

    universes = []
    for ring_index, ring in enumerate(reactor.core.lattice.elements):
        ring_universes = []
        for element_index, _ in enumerate(ring):
            core_location = geometry_elements_triga_netl.Core.RING_MAP[ring_index][element_index]
            universe = build_core_element(
                core_cell_specs=reactor.get_core_cell_specs(core_location),
            )
            ring_universes.append(universe)
        universes.append(ring_universes)

    lattice = openmc.HexLattice()
    lattice.orientation = reactor.core.lattice.orientation
    lattice.pitch = [reactor.core.pitch]
    lattice.universes = universes
    lattice.center = (0.0, 0.0)
    lattice.outer = outer_universe
    return lattice


def build_core_element(
    core_cell_specs: geometry_elements_triga_netl.Reactor.CoreCellSpecs,
) -> openmc.Universe:
    """Build an OpenMC universe from resolved core-cell geometry specifications.

    Parameters
    ----------
    core_cell_specs : geometry_elements_triga_netl.Reactor.CoreCellSpecs
        Resolved element, grid-plate, fill-material, and placement data for the
        core cell.

    Returns
    -------
    openmc.Universe
        Universe containing the specified element, grid plates, and outer material.
    """

    cells        = []
    outer_region = None
    grid_regions = None

    grid_plate_specs = (core_cell_specs.upper_grid_plate,
                        core_cell_specs.lower_grid_plate)

    for grid_plate in grid_plate_specs:
        if grid_plate is None:
            continue

        region = +openmc.ZPlane(grid_plate.axial_bounds.lower)
        region &= -openmc.ZPlane(grid_plate.axial_bounds.upper)
        if grid_plate.penetration_radius is not None:
            region &= +openmc.ZCylinder(r=grid_plate.penetration_radius,
                                        x0=grid_plate.x0,
                                        y0=grid_plate.y0)

        grid_cell = openmc.Cell(fill   = grid_plate.material.openmc_material,
                                region = region)
        cells.append(grid_cell)
        grid_regions = grid_cell.region if grid_regions is None else grid_regions | grid_cell.region
        outer_region = ~grid_cell.region if outer_region is None else outer_region & ~grid_cell.region

    element_specs = core_cell_specs.element
    if element_specs is not None:
        element       = element_specs.geometry
        bottom_z      = element_specs.bottom_axial_position
        top_z         = bottom_z + element.length
        bottom_plane   = openmc.ZPlane(bottom_z)
        top_plane      = openmc.ZPlane(top_z)
        element_region = +bottom_plane & -top_plane
        outer_region   = ~element_region if outer_region is None else outer_region & ~element_region
        element_region = element_region & ~grid_regions if grid_regions else element_region
        element_cell   = openmc.Cell(fill=build(element), region=element_region)
        z_translation  = bottom_z
        # CylindricalStacks and PNTs already use element.bottom_pos, so remove it from the translation
        if isinstance(element, (CylindricalStack, geometry_elements_triga_netl.PNT)):
            z_translation -= element.bottom_pos
        element_cell.translation = (element_specs.x0, element_specs.y0, z_translation)
        cells.append(element_cell)

    cells.append(openmc.Cell(fill=core_cell_specs.outer_material.openmc_material,
                             region=outer_region))

    return openmc.Universe(cells=cells)

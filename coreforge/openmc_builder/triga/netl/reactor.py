from typing import Optional, Tuple

import numpy as np
import openmc


from coreforge.openmc_builder.openmc_builder import register_builder, build
from coreforge.shapes import Hexagon
import coreforge.geometry_elements.triga as geometry_elements_triga
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl

@register_builder(geometry_elements_triga_netl.Reactor)
class Reactor:
    """ An OpenMC geometry builder class for a TRIGA NETL Reactor
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements_triga_netl.Reactor) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a TRIGA NETL Reactor

        Origin of contructed universe is at the core centerline.

        Parameters
        ----------
        element: geometry_elements_triga_netl.Reactor
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """


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
        for beamport in [element.beam_port_1_5, element.beam_port_2,
                         element.beam_port_3,   element.beam_port_4]:
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

        return openmc.Universe(cells=cells)


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
    top_of_reflector        = openmc.ZPlane(z0 = reactor.reflector.core_centerline_offset +
                                                 reactor.reflector.geometry.height / 2.0)
    bottom_of_reflector     = openmc.ZPlane(z0 = reactor.reflector.core_centerline_offset -
                                                 reactor.reflector.geometry.height / 2.0)
    bottom_of_rsr_cavity    = openmc.ZPlane(z0 = top_of_reflector.z0 -
                                                 reactor.rotary_specimen_rack_cavity.height)
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

    r                = reactor.rotary_specimen_rack_cavity.tube_to_center_distance
    number_of_tubes  = reactor.rotary_specimen_rack_cavity.number_of_tubes
    d_theta          = 360.0 / number_of_tubes
    outer_radius     = reactor.rotary_specimen_rack_cavity.tube_specs.outer_radius
    inner_radius     = outer_radius - reactor.rotary_specimen_rack_cavity.tube_specs.thickness

    cavity_fill_material = reactor.rotary_specimen_rack_cavity.material.openmc_material
    tube_clad_material   = reactor.rotary_specimen_rack_cavity.tube_specs.material.openmc_material

    cells          = []
    outside_region = None
    for i in range(1, number_of_tubes + 1):
        angle = 90.0 + (i-1) * -d_theta
        x     = r * np.cos(np.radians(angle))
        y     = r * np.sin(np.radians(angle))
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
    shroud_top    = openmc.ZPlane(z0 = reactor.upper_grid_plate.top_to_core_centerline_distance)
    shroud_bottom = openmc.ZPlane(z0 = reactor.reflector.geometry.height * -0.5 +
                                       reactor.reflector.core_centerline_offset)

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

    outer_material = reactor.core.fill_material.openmc_material

    universes = []
    for ring in reactor.core.lattice.elements:
        ring_universes = []
        for element in ring:
            element_bottom_axial_position = None # For None elements
            if isinstance(element, geometry_elements_triga_netl.CentralThimble):
                element_bottom_axial_position = -0.5 * element.length
            elif isinstance(element, geometry_elements_triga.FuelElement):
                element_bottom_axial_position = (-0.5 * element.fuel_meat.length -
                    element.moly_disc.thickness - element.lower_end_fitting.length -
                    element.lower_graphite_reflector.thickness)
            elif isinstance(element, geometry_elements_triga.GraphiteElement):
                element_bottom_axial_position = (-0.5 * element.graphite_meat.length -
                    element.lower_end_fitting.length)
            elif element is reactor.core.transient_rod:
                element_bottom_axial_position = reactor.transient_rod_position
            elif element is reactor.core.regulating_rod:
                element_bottom_axial_position = reactor.regulating_rod_position
            elif element is reactor.core.shim_1_rod:
                element_bottom_axial_position = reactor.shim_1_rod_position
            elif element is reactor.core.shim_2_rod:
                element_bottom_axial_position = reactor.shim_2_rod_position
            elif isinstance(element, geometry_elements_triga_netl.SourceHolder):
                element_bottom_axial_position = (
                    reactor.upper_grid_plate.top_to_core_centerline_distance + element.length)

            universe = build_core_element(element,
                                          element_bottom_axial_position,
                                          outer_material,
                                          reactor.upper_grid_plate,
                                          reactor.lower_grid_plate)
            ring_universes.append(universe)
        universes.append(ring_universes)

    lattice = openmc.HexLattice()
    lattice.orientation = reactor.core.lattice.orientation
    lattice.pitch = [reactor.core.pitch]
    lattice.universes = universes
    lattice.center = (0.0, 0.0)
    lattice.outer = openmc.Universe(cells=[openmc.Cell(fill=outer_material)])
    return lattice


def build_core_element(
    element: Optional[geometry_elements_triga_netl.Core.Element] = None,
    element_bottom_axial_position: Optional[float] = None,
    outer_material: Optional[openmc.Material] = None,
    upper_grid_plate: Optional[geometry_elements_triga_netl.Reactor.GridPlate] = None,
    lower_grid_plate: Optional[geometry_elements_triga_netl.Reactor.GridPlate] = None,
) -> openmc.Universe:
    """Helper to build an OpenMC universe for a single core element with optional grid plates.

    Parameters
    ----------
    element : geometry_elements_triga_netl.Core.Element, optional
        Core element to place in the cell. When omitted, only the grids and outer
        material will be present in the returned universe.
    element_bottom_axial_position : float, optional
        Axial z-position (cm) of the element bottom relative to the core centerline.
        If not provided, a sensible default is derived from the element type (mirrors
        legacy behavior from ``build_element_openmc_universe``).
    outer_material : openmc.Material, optional
        Material filling the region outside the element and grid plates. If omitted
        and ``element`` is provided, the element's ``outer_material`` is used. If
        ``element`` is ``None``, this must be provided.
    upper_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate, optional
        Upper grid plate geometry and placement.
    lower_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate, optional
        Lower grid plate geometry and placement.

    Returns
    -------
    openmc.Universe
        Universe containing the element (if provided), surrounding coolant, and any
        provided grid plates.
    """

    assert element is not None or outer_material is not None, (
        "If no element is provided, outer_material must be specified."
    )

    bottom_z     = element_bottom_axial_position or 0.0
    cells        = []
    outer_region = None
    grid_regions = None

    def hole_radius(elment:     geometry_elements_triga_netl.Core.Element,
                    grid_plate: geometry_elements_triga_netl.GridPlate):
        radius = grid_plate.fuel_penetration_radius
        if isinstance(elment, geometry_elements_triga_netl.Core.Fixture):
            radius = grid_plate.control_rod_penetration_radius
            if isinstance(elment, geometry_elements_triga_netl.CentralThimble):
                radius = elment.cladding.outer_radius
        return radius

    if upper_grid_plate:
        region = -openmc.ZPlane(upper_grid_plate.top_to_core_centerline_distance)
        region &= +openmc.ZPlane(upper_grid_plate.top_to_core_centerline_distance -
                                upper_grid_plate.geometry.thickness)
        if element is not None:
            region &= +openmc.ZCylinder(r = hole_radius(element, upper_grid_plate.geometry))

        cells.append(openmc.Cell(fill   = upper_grid_plate.geometry.material.openmc_material,
                                 region = region))
        grid_regions = cells[-1].region
        outer_region = ~cells[-1].region

    if lower_grid_plate:
        region = +openmc.ZPlane(-(lower_grid_plate.top_to_core_centerline_distance +
                                  lower_grid_plate.geometry.thickness))
        region &= -openmc.ZPlane(-lower_grid_plate.top_to_core_centerline_distance)
        if element is not None:
            region &= +openmc.ZCylinder(r = hole_radius(element, lower_grid_plate.geometry))

        cells.append(openmc.Cell(fill   = lower_grid_plate.geometry.material.openmc_material,
                                 region = region))

        grid_regions = cells[-1].region if grid_regions is None else grid_regions | cells[-1].region
        outer_region = ~cells[-1].region if outer_region is None else outer_region & ~cells[-1].region

    if element is not None:
        top_z          = bottom_z + element.length
        bottom_plane   = openmc.ZPlane(bottom_z)
        top_plane      = openmc.ZPlane(top_z)
        element_region = +bottom_plane & -top_plane
        outer_region   = ~element_region if outer_region is None else outer_region & ~element_region
        element_region = element_region & ~grid_regions if grid_regions else element_region
        element_cell   = openmc.Cell(fill=build(element), region=element_region)
        element_cell.translation = (0.0, 0.0, bottom_z)
        cells.append(element_cell)

    outer_fill = outer_material or element.outer_material.openmc_material
    cells.append(openmc.Cell(fill=outer_fill, region=outer_region))

    return openmc.Universe(cells=cells)

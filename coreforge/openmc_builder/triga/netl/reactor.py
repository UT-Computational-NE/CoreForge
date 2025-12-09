from typing import Optional

import openmc
from coreforge.openmc_builder.openmc_builder import register_builder, build
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

        return openmc.Universe()

def build_element_cell_universe(
    element: Optional[geometry_elements_triga_netl.Core.Element] = None,
    element_bottom_axial_position: Optional[float] = None,
    outer_material: Optional[openmc.Material] = None,
    upper_grid: Optional[geometry_elements_triga_netl.GridPlate] = None,
    upper_grid_distance_from_axial_centerline: Optional[float] = None,
    lower_grid: Optional[geometry_elements_triga_netl.GridPlate] = None,
    lower_grid_distance_from_axial_centerline: Optional[float] = None,
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
    upper_grid : geometry_elements_triga_netl.GridPlate, optional
        Upper grid plate definition.
    upper_grid_distance_from_axial_centerline : float, optional
        Non-negative distance (cm) from the core axial centerline to the nearest face
        of the upper grid plate.
    lower_grid : geometry_elements_triga_netl.GridPlate, optional
        Lower grid plate definition.
    lower_grid_distance_from_axial_centerline : float, optional
        Non-negative distance (cm) from the core axial centerline to the nearest face
        of the lower grid plate.

    Returns
    -------
    openmc.Universe
        Universe containing the element (if provided), surrounding coolant, and any
        provided grid plates.
    """

    def _validate_grid_args(grid, distance, name: str) -> None:
        if grid is None:
            return
        if distance is None:
            raise ValueError(f"{name} provided without distance from axial centerline.")
        if distance < 0.0:
            raise ValueError(f"{name} distance_from_axial_centerline must be non-negative.")

    _validate_grid_args(upper_grid, upper_grid_distance_from_axial_centerline, "upper_grid")
    _validate_grid_args(lower_grid, lower_grid_distance_from_axial_centerline, "lower_grid")

    # Determine hole radii and element bottom position
    bottom_z = element_bottom_axial_position or 0.0
    upper_hole_radius = lower_hole_radius = None
    if element:
        if isinstance(element, (geometry_elements_triga.FuelElement, geometry_elements_triga.GraphiteElement,
                                geometry_elements_triga_netl.SourceHolder)):
            upper_hole_radius = upper_grid.fuel_penetration_radius if upper_grid else None
            lower_hole_radius = lower_grid.fuel_penetration_radius if lower_grid else None
        elif isinstance(element, geometry_elements_triga_netl.CentralThimble):
            upper_hole_radius = element.cladding.outer_radius
            lower_hole_radius = element.cladding.outer_radius
        else:
            upper_hole_radius = upper_grid.control_rod_penetration_radius if upper_grid else None
            lower_hole_radius = lower_grid.control_rod_penetration_radius if lower_grid else None

    cells = []
    outer_region = None
    grid_regions = None

    if upper_grid:
        bottom = openmc.ZPlane(upper_grid_distance_from_axial_centerline)
        top    = openmc.ZPlane(upper_grid_distance_from_axial_centerline + upper_grid.thickness)
        hole   = openmc.ZCylinder(r = upper_hole_radius)
        cell   = openmc.Cell(fill = upper_grid.material.openmc_material, region = +bottom & -top & +hole)
        grid_regions = cell.region
        outer_region = ~cell.region
        cells.append(cell)

    if lower_grid:
        top    = openmc.ZPlane(-lower_grid_distance_from_axial_centerline)
        bottom = openmc.ZPlane(-(lower_grid_distance_from_axial_centerline + lower_grid.thickness))
        hole   = openmc.ZCylinder(r = lower_hole_radius)
        cell   = openmc.Cell(fill = lower_grid.material.openmc_material, region = +bottom & -top & +hole)
        grid_regions = cell.region if grid_regions is None else grid_regions | cell.region
        outer_region = ~cell.region if outer_region is None else outer_region & ~cell.region
        cells.append(cell)

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

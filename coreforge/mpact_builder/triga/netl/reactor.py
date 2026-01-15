from __future__ import annotations
from typing import Dict, Optional, Tuple, TypeAlias
from dataclasses import dataclass, field

import openmc
import mpactpy

import coreforge.geometry_elements as geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl
from coreforge.materials import Material
import coreforge.openmc_builder as openmc_builder
from coreforge.mpact_builder import (Bounds, Builder, BuilderSpecs, HexLattice, InfiniteMedium, Stack, stack as stack_builder,
                                     MaterialSpecs, DEFAULT_MPACT_MATERIAL_SPECS, build, get_builder, register_builder)
from coreforge.mpact_builder.triga import CoreElement, FuelElement, GraphiteElement
from .central_thimble import CentralThimble
from .fuel_follower_control_rod import FuelFollowerControlRod
from .source_holder import SourceHolder
from .transient_rod import TransientRod



@register_builder(geometry_elements_triga_netl.Reactor)
class Reactor(Builder[geometry_elements_triga_netl.Reactor]):
    """ An MPACT geometry builder class for a TRIGA NETL Reactor

    Parameters
    ----------
    specs: Optional[Specs]
        Specifications for building the MPACT representation of this element

    Attributes
    ----------
    specs: Optional[Specs]
        Specifications for building the MPACT representation of this element
    """

    CoreElementSpecs: TypeAlias = (FuelElement.Specs |
                                   GraphiteElement.Specs |
                                   CentralThimble.Specs |
                                   SourceHolder.Specs |
                                   TransientRod.Specs |
                                   FuelFollowerControlRod.Specs)

    @dataclass
    class VoxelizedSegmentSpecs(Stack.Segment.Specs):
        """Specifications for voxelized segments outside core element regions.

        Attributes
        ----------
        builder_specs : Optional[InfiniteMedium.Specs]
            Builder specifications for the voxelized segment element.
        """

        builder_specs: Optional[InfiniteMedium.Specs] = None

        def __post_init__(self) -> None:
            super().__post_init__()
            if self.builder_specs is None:
                return
            assert isinstance(
                self.builder_specs,
                InfiniteMedium.Specs,
            ), "VoxelizedSegmentSpecs.builder_specs must be InfiniteMedium.Specs."

    @dataclass
    class CoreCellSpecs:
        """Specifications for a single core location build.

        Attributes
        ----------
        element_specs : Optional[Reactor.CoreElementSpecs]
            Builder specifications for the core element at this location. Must be
            consistent with the element being built.
        outer_region_specs : Optional[Reactor.VoxelizedSegmentSpecs | CoreElement.SegmentSpecs]
            Specifications for axial regions outside the core element. Use
            VoxelizedSegmentSpecs (InfiniteMedium.Specs) when there are no grid
            plate penetrations, and CoreElement.SegmentSpecs
            (CylindricalPinCell.Specs) when penetrations are present.
        axial_bounds : Optional[tuple[float, float]]
            Lower and upper axial bounds (cm) to clip the constructed stack.
        """

        element_specs:      Optional[Reactor.CoreElementSpecs] = None
        outer_region_specs: Optional[Reactor.VoxelizedSegmentSpecs | CoreElement.SegmentSpecs] = None
        axial_bounds:       Optional[Tuple[float, float]] = None

        def __post_init__(self) -> None:
            if self.axial_bounds is not None:
                assert self.axial_bounds[1] > self.axial_bounds[0], \
                    f"Upper axial bound {self.axial_bounds[1]} must be greater than lower axial bound {self.axial_bounds[0]}."

    @dataclass
    class Specs(BuilderSpecs):
        """ Building specifications for Reactor

        Attributes
        ----------
        core_specs : Dict[str, Reactor.CoreCellSpecs]
            Per-location overrides for core element specs.
        min_thickness : float
            The minimum allowed thickness (cm) for axial mesh unionization.
            See HexLattice.Specs.min_thickness for details.
        material_specs : MaterialSpecs
            Specifications for how materials should be treated in MPACT.
            Should be used for all materials that are not in DEFAULT_MPACT_MATERIAL_SPECS,
            or to override the default behavior for specific materials.
        num_procs : int = 1
            Number of processors to use when building the reactor.
        openmc_universe : Optional[openmc.Universe]
            Optional OpenMC geometry for excore regions. If provided, excore
            regions will be built from this geometry instead of using the
            OpenMC geometry generated from the Reactor.
        offset : Tuple[float, float, float]
            Offset of the OpenMC model's lower-left corner relative to the
            MPACT Core lower-left.  Needs only be provided if the provided OpenMC
            is not centered at the origin.  Otherwise, will be determined automatically.
        """

        core_specs:      Dict[str, Reactor.CoreCellSpecs] = field(default_factory=dict)
        min_thickness:   float = 0.0
        material_specs:  MaterialSpecs = field(default_factory=MaterialSpecs)
        openmc_universe: Optional[openmc.Universe] = None
        num_procs:       int = 1
        offset:          Optional[Tuple[float, float, float]] = None

        def __post_init__(self) -> None:
            valid_locations = {loc for ring in geometry_elements_triga_netl.Core.RING_MAP for loc in ring}
            invalid = [loc for loc in self.core_specs.keys() if loc not in valid_locations]
            assert not invalid, f"Invalid core location(s) in core_specs: {invalid}"
            assert self.num_procs > 0, f"num_procs must be > 0 (got {self.num_procs})"
            assert self.min_thickness >= 0.0, f"min_thickness must be >= 0.0 cm (got {self.min_thickness})"



    def __init__(self, specs: Optional[Specs] = None):
        super().__init__(specs)

    def default_specs(self) -> Specs:
        return self.Specs()

    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs is not None else self.Specs()


    def build(self,
              element: geometry_elements_triga_netl.Reactor,
              bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a TRIGA NETL Reactor

        Parameters
        ----------
        element: geometry_elements_triga_netl.Reactor
            The geometry element to be built
        bounds: Optional[Bounds]
            The spatial bounds for the geometry.

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """
        pass
#        openmc_universe  = self.specs.openmc_universe or openmc_builder.build(element)
#        openmc_materials = openmc.Materials(list(openmc_universe.get_all_materials().values()))
#        openmc_geometry  = openmc.Geometry(openmc_universe)
#
#        element_specs = {} # To be filled in
#
#        lattice       = # To be filled in
#        lattice_specs = HexLattice.Specs(min_thickness = self.specs.min_thickness,
#                                                element_specs = element_specs,
#                                                num_procs     = self.specs.num_procs,)
#
#        mpact_core = build(lattice, lattice_specs)
#
#        # - All Excore elements can share the same target thicknesses and segement lengths cause it'll all be unionized anyways
#        #   - just define once and assign to all excore elements
#        #   - Only the radial resolution need be different for excore elements
#        # - Can define the same specs for the same cell type (e.g., reflector, pool, shroud, beam tube, rsr) and just choose which
#        #   which core locations to assign to (may need to build openmc model and sample the points to see which locations are which cell type)
#        #      - Would be best to sample by universe, but could do it by universe name
#        # - K, build the core lattice, and start adding rings to the outside of it until we get the full radius
#        # - We can make custom stacks for the various regions of resolution (one stack for beam tubes, one for shroud, etc)
#        # - RSR, BeamTube, Shroud, Reflector, Pool resolutions
#        # - We can then place our stacks based on the ring and ring position
#        # - Any interior cells that hit the shroud need to be replaced with shroud cells
#        # - Allow for providing a custom OpenMC model for excore regions?  If not present, generate from Reactor
#
#        return _apply_openmc_overlay(mpact_core, openmc_universe, self.specs.material_specs, self.specs.num_procs, self.specs.offset)


def _apply_openmc_overlay(core: mpactpy.Core,
                          openmc_universe: openmc.Universe,
                          num_procs: int,
                          offset: int) -> mpactpy.Core:
    pass
    # I need to refactor MaterialSpecs into a typed dict or something
    # Default to MPACT default MaterialSpecs and then replace with whatever is in MatSpecs
    # Maybe add a helper function in mpactpy for all eligible pins or all eligible pins with material_specs
    # Or maybe we can think of something better

#    openmc_materials = openmc.Materials(list(openmc_universe.get_all_materials().values()))
#    openmc_geometry  = openmc.Geometry(openmc_universe)
#
#    # Only overlay pins/modules/lattices/assemblies that contain voxelized pins
#    pins_to_overlay = {pin for pin in core.pins if isinstance(pin.pinmesh, mpactpy.RectangularPinMesh)}
#    modules_to_overlay = {m for m in core.modules if pins_to_overlay.intersection(m.pins)}
#    lattices_to_overlay = {l for l in core.lattices if modules_to_overlay.intersection(l.modules)}
#    assemblies_to_overlay = {a for a in core.assemblies if lattices_to_overlay.intersection(a.lattices)}
#
#    # Create overlay masks
#    pin_mask:      mpactpy.Pin.OverlayMask      = {material                for material in core.materials}
#    module_mask:   mpactpy.Module.OverlayMask   = {pin:      pin_mask      for pin      in pins_to_overlay}
#    lattice_mask:  mpactpy.Lattice.OverlayMask  = {module:   module_mask   for module   in modules_to_overlay}
#    assembly_mask: mpactpy.Assembly.OverlayMask = {lattice:  lattice_mask  for lattice  in lattices_to_overlay}
#    include_only:  mpactpy.Core.OverlayMask     = {assembly: assembly_mask for assembly in assemblies_to_overlay}
#
#    overlay_policy           = mpactpy.PinMesh.OverlayPolicy(num_procs=num_procs)
#    material_specs           = MPACT_MATERIAL_SPECS.material_specs
#    material_specs           = {material.name: material_specs[material] for material in material_specs}
#    overlay_policy.mat_specs = {material: material_specs[material.name] for material in openmc_materials}
#
#    half_mpact_model_width = core.width['X'] * 0.5
#    offset = (-half_mpact_model_width, -half_mpact_model_width, 0.0)
#
#    return core.overlay(openmc_geometry, offset, include_only, overlay_policy)

def build_core_element(
    core_location:                 str,
    upper_grid_plate:              geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate:              geometry_elements_triga_netl.Reactor.GridPlate,
    element:                       Optional[geometry_elements_triga_netl.Core.Element] = None,
    element_bottom_axial_position: Optional[float] = None,
    outer_material:                Optional[Material] = None,
    core_cell_specs:               Optional[Reactor.CoreCellSpecs] = None,
) -> Tuple[geometry_elements.Stack, Stack.Specs]:
    """Helper to build an MPACT core for a single element with grid plates.

    This function handles core locations with or without grid plate penetrations.
    Non-element axial regions are represented as either voxelized InfiniteMedium
    segments (no penetrations) or cylindrical pincells (with penetrations) that
    use the upper/lower penetration radii as mesh boundaries.

    Parameters
    ----------
    core_location : str
        Core location identifier (e.g., ``"C-07"``) used to look up grid plate
        penetration radii.
    upper_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate
        Upper grid plate geometry and placement.
    lower_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate
        Lower grid plate geometry and placement.
    element : geometry_elements_triga_netl.Core.Element, optional
        Core element to place in the cell. When omitted, only the grid plates and outer
        material will be present in the returned universe.
    element_bottom_axial_position : float, optional
        Axial z-position (cm) of the element bottom relative to the core centerline.
    outer_material : Material, optional
        Material filling the region outside the element and grid plates. If omitted
        and ``element`` is provided, the element's ``outer_material`` is used. If
        ``element`` is ``None``, this must be provided.
    core_cell_specs : Optional[Reactor.CoreCellSpecs]
        Specifications for building the core cell location, including element
        specs, outer region specs, and optional axial bounds.

    Returns
    -------
    Tuple[geometry_elements.Stack, Stack.Specs]
        Stack and corresponding specs for the core element with grid plates and non-core axial regions.
    """

    core_cell_specs    = core_cell_specs or Reactor.CoreCellSpecs()
    element_specs      = core_cell_specs.element_specs
    outer_region_specs = core_cell_specs.outer_region_specs
    axial_bounds       = core_cell_specs.axial_bounds

    upper_penetration_radius = upper_grid_plate.geometry.penetration_map.get(core_location)
    lower_penetration_radius = lower_grid_plate.geometry.penetration_map.get(core_location)

    both_grids_have_penetrations       = upper_penetration_radius and lower_penetration_radius
    both_grid_do_not_have_penetrations = not upper_penetration_radius and not lower_penetration_radius
    assert both_grids_have_penetrations or both_grid_do_not_have_penetrations, \
        "Both upper and lower penetration radii must be provided or both must be None."

    if outer_region_specs is None:
        outer_region_specs = (
            CoreElement.SegmentSpecs()
            if both_grids_have_penetrations
            else Reactor.VoxelizedSegmentSpecs()
        )

    if both_grids_have_penetrations:
        assert isinstance(outer_region_specs, CoreElement.SegmentSpecs), \
            "outer_region_specs must be CoreElement.SegmentSpecs when penetrations are present."
    else:
        assert isinstance(outer_region_specs, Reactor.VoxelizedSegmentSpecs), \
            "outer_region_specs must be Reactor.VoxelizedSegmentSpecs when no penetrations are present."

    if element is not None:
        outer_material = outer_material or element.outer_material
        assert element_bottom_axial_position is not None, \
            "element_bottom_axial_position must be provided if element is not None."
        assert both_grids_have_penetrations, \
            "Grid plate penetration radii must be provided for core locations with elements."

    assert outer_material is not None, "outer_material must be provided if element is None."

    if axial_bounds is None:
        axial_bounds = (-(lower_grid_plate.top_to_core_centerline_distance +
                              lower_grid_plate.geometry.thickness),
                        upper_grid_plate.top_to_core_centerline_distance)

        if element is not None:
            axial_bounds = (min(axial_bounds[0], element_bottom_axial_position),
                            max(axial_bounds[1], element_bottom_axial_position + element.length))

    if upper_penetration_radius is None and lower_penetration_radius is None:
        return _build_core_location_with_no_penetrations(upper_grid_plate,
                                                         lower_grid_plate,
                                                         axial_bounds,
                                                         outer_material,
                                                         outer_region_specs)
    elif element is None:
        return _build_core_location_with_water_hole(upper_grid_plate,
                                                    lower_grid_plate,
                                                    axial_bounds,
                                                    outer_material,
                                                    core_location,
                                                    outer_region_specs)

    return _build_core_location_with_element(upper_grid_plate,
                                             lower_grid_plate,
                                             element,
                                             element_bottom_axial_position,
                                             axial_bounds,
                                             outer_material,
                                             core_location,
                                             element_specs,
                                             outer_region_specs)


def _build_core_location_with_no_penetrations(
    upper_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    axial_bounds:       tuple[float, float],
    outer_material:     Material,
    outer_region_specs: Optional[Reactor.VoxelizedSegmentSpecs] = None,
) -> Tuple[geometry_elements.Stack, Stack.Specs]:
    outer_region_specs = outer_region_specs or Reactor.VoxelizedSegmentSpecs()

    lower_plate_top    = -lower_grid_plate.top_to_core_centerline_distance
    lower_plate_bottom = lower_plate_top - lower_grid_plate.geometry.thickness
    upper_plate_top    = upper_grid_plate.top_to_core_centerline_distance
    upper_plate_bottom = upper_plate_top - upper_grid_plate.geometry.thickness

    buffer       = axial_bounds[1] - axial_bounds[0]
    stack_bottom = lower_plate_bottom - buffer

    segments = [
        geometry_elements.Stack.Segment(
            element = geometry_elements.InfiniteMedium(outer_material, name="outer_region"),
            length  = buffer,
        ),
        geometry_elements.Stack.Segment(
            element = geometry_elements.InfiniteMedium(lower_grid_plate.geometry.material,
                                                       name="lower_grid_plate"),
            length  = lower_plate_top - lower_plate_bottom,
        ),
        geometry_elements.Stack.Segment(
            element = geometry_elements.InfiniteMedium(outer_material, name="outer_region"),
            length  = upper_plate_bottom - lower_plate_top,
        ),
        geometry_elements.Stack.Segment(
            element = geometry_elements.InfiniteMedium(upper_grid_plate.geometry.material,
                                                       name="upper_grid_plate"),
            length  = upper_plate_top - upper_plate_bottom,
        ),
        geometry_elements.Stack.Segment(
            element = geometry_elements.InfiniteMedium(outer_material, name="outer_region"),
            length  = buffer,
        ),
    ]

    stack = geometry_elements.Stack(segments   = segments,
                                    name       = "outer_region_stack",
                                    bottom_pos = stack_bottom)
    stack_specs = Stack.Specs({segment: outer_region_specs for segment in segments})

    return stack_builder.get_axial_slice(stack, stack_specs, axial_bounds[0], axial_bounds[1])


def _build_core_location_with_water_hole(
    upper_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    axial_bounds:       tuple[float, float],
    outer_material:     Material,
    core_location:      str,
    outer_region_specs: Optional[CoreElement.SegmentSpecs] = None,
) -> Tuple[geometry_elements.Stack, Stack.Specs]:

    outer_pincell = _build_outer_pincell(upper_grid_plate,
                                         lower_grid_plate,
                                         outer_material,
                                         core_location)

    lower_plate_top    = -lower_grid_plate.top_to_core_centerline_distance
    lower_plate_bottom = lower_plate_top - lower_grid_plate.geometry.thickness
    upper_plate_top    = upper_grid_plate.top_to_core_centerline_distance

    buffer       = axial_bounds[1] - axial_bounds[0]
    stack_bottom = lower_plate_bottom - buffer

    segment = geometry_elements.Stack.Segment(
        element = outer_pincell,
        length  = upper_plate_top - lower_plate_bottom + 2 * buffer,
    )

    stack = geometry_elements.Stack(segments   = [segment],
                                    name       = f"{core_location}_outer_stack",
                                    bottom_pos = stack_bottom)
    stack_specs = Stack.Specs({segment: outer_region_specs})

    stack, specs = stack_builder.get_axial_slice(stack, stack_specs, axial_bounds[0], axial_bounds[1])
    stack, specs = _add_grid_plates_to_stack(stack, specs, upper_grid_plate, lower_grid_plate, core_location)
    return stack, specs


def _build_core_location_with_element(
    upper_grid_plate:              geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate:              geometry_elements_triga_netl.Reactor.GridPlate,
    element:                       geometry_elements_triga_netl.Core.Element,
    element_bottom_axial_position: float,
    axial_bounds:                  tuple[float, float],
    outer_material:                Material,
    core_location:                 str,
    element_specs:                 Optional[Reactor.CoreElementSpecs] = None,
    outer_region_specs:            Optional[CoreElement.SegmentSpecs] = None,
) -> Tuple[geometry_elements.Stack, Stack.Specs]:

    outer_pincell = _build_outer_pincell(upper_grid_plate,
                                         lower_grid_plate,
                                         outer_material,
                                         core_location)

    builder_cls: CoreElement = get_builder(element)
    element_stack, element_stack_specs = builder_cls(element_specs).build_stack_and_specs(element)
    element_top = element_bottom_axial_position + element_stack.length

    lower_plate_top    = -lower_grid_plate.top_to_core_centerline_distance
    lower_plate_bottom = lower_plate_top - lower_grid_plate.geometry.thickness
    upper_plate_top    = upper_grid_plate.top_to_core_centerline_distance

    buffer = axial_bounds[1] - axial_bounds[0]
    stack_bottom = min(lower_plate_bottom, element_bottom_axial_position) - buffer
    stack_top    = max(upper_plate_top, element_top) + buffer

    bottom_segment = geometry_elements.Stack.Segment(
        element = outer_pincell,
        length  = element_bottom_axial_position - stack_bottom,
    )
    top_segment = geometry_elements.Stack.Segment(
        element = outer_pincell,
        length  = stack_top - element_top,
    )

    segments = [bottom_segment] + element_stack.segments + [top_segment]
    stack = geometry_elements.Stack(segments   = segments,
                                    name       = f"{core_location}_element_stack",
                                    bottom_pos = stack_bottom)

    segment_specs = {bottom_segment: outer_region_specs,
                     top_segment: outer_region_specs,}
    segment_specs.update(element_stack_specs.segment_specs)
    stack_specs = Stack.Specs(segment_specs=segment_specs,
                              num_procs=element_stack_specs.num_procs)

    stack, specs = stack_builder.get_axial_slice(stack, stack_specs, axial_bounds[0], axial_bounds[1])
    stack, specs = _add_grid_plates_to_stack(stack, specs, upper_grid_plate, lower_grid_plate, core_location)
    return stack, specs


def _build_outer_pincell(
    upper_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    outer_material:     Material,
    core_location:      str,
) -> geometry_elements.CylindricalPinCell:

    radii = sorted({upper_grid_plate.geometry.penetration_map.get(core_location),
                    lower_grid_plate.geometry.penetration_map.get(core_location)})

    outer_pincell = geometry_elements.CylindricalPinCell(
        radii     = radii,
        materials = [outer_material for _ in range(len(radii) + 1)],
        name      = f"{core_location}_outer_pincell")

    return outer_pincell


def _add_grid_plates_to_stack(
    stack:            geometry_elements.Stack,
    stack_specs:      Stack.Specs,
    upper_grid_plate: geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate: geometry_elements_triga_netl.Reactor.GridPlate,
    core_location:    str,
) -> Tuple[geometry_elements.Stack, Stack.Specs]:

    plate_ranges = [
        (lower_grid_plate,
         -lower_grid_plate.top_to_core_centerline_distance,
         -lower_grid_plate.top_to_core_centerline_distance - lower_grid_plate.geometry.thickness),
        (upper_grid_plate,
         upper_grid_plate.top_to_core_centerline_distance,
         upper_grid_plate.top_to_core_centerline_distance - upper_grid_plate.geometry.thickness),
    ]

    for grid_plate, plate_top, plate_bottom in plate_ranges:
        penetration_radius = grid_plate.geometry.penetration_map.get(core_location)
        assert penetration_radius is not None, \
            f"No penetration radius for core location {core_location}."

        grid_part = _build_grid_stack_and_specs(stack,
                                                stack_specs,
                                                plate_top,
                                                plate_bottom,
                                                grid_plate.geometry.material,
                                                penetration_radius)
        if grid_part is None:
            continue

        grid_stack, grid_specs = grid_part

        lower_part = stack_builder.get_axial_slice(stack, stack_specs, stack.bottom_pos, plate_bottom)
        upper_part = stack_builder.get_axial_slice(stack, stack_specs, plate_top, stack.bottom_pos + stack.length)

        segments = []
        segment_specs = {}
        if lower_part is not None:
            lower_stack, lower_specs = lower_part
            segments.extend(lower_stack.segments)
            segment_specs.update(lower_specs.segment_specs)

        segments.extend(grid_stack.segments)
        segment_specs.update(grid_specs.segment_specs)

        if upper_part is not None:
            upper_stack, upper_specs = upper_part
            segments.extend(upper_stack.segments)
            segment_specs.update(upper_specs.segment_specs)

        stack = geometry_elements.Stack(segments   = segments,
                                        name       = stack.name,
                                        bottom_pos = stack.bottom_pos)
        stack_specs = Stack.Specs(segment_specs=segment_specs, num_procs=stack_specs.num_procs)

    return stack, stack_specs


def _build_grid_stack_and_specs(
    stack:              geometry_elements.Stack,
    stack_specs:        Stack.Specs,
    plate_top:          float,
    plate_bottom:       float,
    plate_material:     Material,
    penetration_radius: float,
) -> Optional[Tuple[geometry_elements.Stack, Stack.Specs]]:

    def material_for_radius(pincell: geometry_elements.CylindricalPinCell, radius: float):
        for zone in pincell.zones:
            if radius <= zone.shape.outer_radius:
                return zone.material
        return pincell.outer_material

    grid_slice = stack.get_axial_slice_with_origins(plate_bottom, plate_top)
    if grid_slice is None:
        return None

    sliced_stack, origins = grid_slice
    grid_segments = []
    grid_segment_specs = {}
    for sliced_segment, origin_segment in zip(sliced_stack.segments, origins):
        assert isinstance(sliced_segment.element, geometry_elements.CylindricalPinCell), \
            "Grid plate stacking expects CylindricalPinCell segments."
        pincell = sliced_segment.element
        radii = [zone.shape.outer_radius for zone in pincell.zones]
        if not any(radius == penetration_radius for radius in radii):
            radii.append(penetration_radius)
        radii = sorted(radii)

        materials = []
        for radius in radii:
            if radius <= penetration_radius:
                materials.append(material_for_radius(pincell, radius))
            else:
                materials.append(plate_material)
        materials.append(plate_material)

        grid_pincell = geometry_elements.CylindricalPinCell(
            radii     = radii,
            materials = materials,
            name      = f"{pincell.name}_grid_plate")

        new_segment = geometry_elements.Stack.Segment(element = grid_pincell,
                                                      length  = sliced_segment.length)
        grid_segments.append(new_segment)
        grid_segment_specs[new_segment] = stack_specs.segment_specs.get(origin_segment, None)

    grid_stack = geometry_elements.Stack(segments   = grid_segments,
                                         name       = stack.name,
                                         bottom_pos = plate_bottom)
    grid_specs = Stack.Specs(segment_specs=grid_segment_specs, num_procs=stack_specs.num_procs)
    return grid_stack, grid_specs

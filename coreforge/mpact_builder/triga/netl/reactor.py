from __future__ import annotations
from typing import Dict, List, Optional, Tuple, TypeAlias
from dataclasses import dataclass, field
from math import ceil, inf, isclose

import openmc
import mpactpy
from mpactpy.utils import ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge import geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl
from coreforge.materials import Material
from coreforge.shapes import Rectangle
from coreforge import openmc_builder
from coreforge.mpact_builder.builder import Bounds, Builder
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs, DEFAULT_MPACT_MATERIAL_SPECS
from coreforge.mpact_builder.hex_lattice import HexLattice
from coreforge.mpact_builder.infinite_medium import InfiniteMedium
from coreforge.mpact_builder.stack import Stack
import coreforge.mpact_builder.stack as stack_builder
from coreforge.mpact_builder.mpact_builder import build, get_builder, register_builder
from coreforge.mpact_builder.triga.core_element import CoreElement
from coreforge.mpact_builder.triga.fuel_element import FuelElement
from coreforge.mpact_builder.triga.graphite_element import GraphiteElement
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
        unionize_radial_mesh : bool
            Whether to unionize the radial mesh across stack segments when a core
            element is present.  Only applicable for cells with core elements.
        """

        element_specs:      Optional[Reactor.CoreElementSpecs] = None
        outer_region_specs: Optional[Reactor.VoxelizedSegmentSpecs | CoreElement.SegmentSpecs] = None
        axial_bounds:       Optional[Tuple[float, float]] = None
        unionize_radial_mesh: bool = False

        def __post_init__(self) -> None:
            if self.axial_bounds is not None:
                assert self.axial_bounds[1] > self.axial_bounds[0], \
                    f"Upper axial bound {self.axial_bounds[1]} must be greater than lower axial bound {self.axial_bounds[0]}."

    @dataclass
    class VoxelationSpecs:
        """ Specifications for voxelation of non-core regions

        Attributes
        ----------
        shroud_target_thicknesses : float
            Target radial thickness (cm) for shroud region voxelation.
        rsr_target_thicknesses : float
            Target radial thickness (cm) for RSR region voxelation.
        reflector_target_thicknesses : float
            Target radial thickness (cm) for reflector region voxelation.
        beamport_target_thicknesses : float
            Target radial thickness (cm) for beamport region voxelation.
        pool_target_thicknesses : float
            Target radial thickness (cm) for pool region voxelation.
        """

        shroud_target_thicknesses:    float = inf
        rsr_target_thicknesses:       float = inf
        reflector_target_thicknesses: float = inf
        beamport_target_thicknesses:  float = inf
        pool_target_thicknesses:      float = inf

        def __post_init__(self) -> None:
            assert self.shroud_target_thicknesses > 0.0, "shroud_target_thicknesses must be > 0.0 cm"
            assert self.rsr_target_thicknesses > 0.0, "rsr_target_thicknesses must be > 0.0 cm"
            assert self.reflector_target_thicknesses > 0.0, "reflector_target_thicknesses must be > 0.0 cm"
            assert self.beamport_target_thicknesses > 0.0, "beamport_target_thicknesses must be > 0.0 cm"
            assert self.pool_target_thicknesses > 0.0, "pool_target_thicknesses must be > 0.0 cm"

    @dataclass
    class Specs(BuilderSpecs):
        """ Building specifications for Reactor

        Attributes
        ----------
        core_specs : Dict[str, Reactor.CoreCellSpecs]
            Per-location overrides for core element specs.
        voxelation_specs : Reactor.VoxelationSpecs
            Specifications for voxelation of non-core regions.
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
        exclude_excore : bool
            Whether to skip excore overlay construction.
        offset : Tuple[float, float, float]
            Offset of the OpenMC model's lower-left corner relative to the
            MPACT Core lower-left.  Needs only be provided if the provided OpenMC
            is not centered at the origin.  Otherwise, will be determined automatically.
        """

        core_specs:       Dict[str, Reactor.CoreCellSpecs] = field(default_factory=dict)
        voxelation_specs: Reactor.VoxelationSpecs = field(default_factory=lambda: Reactor.VoxelationSpecs())  # pylint: disable=unnecessary-lambda
        min_thickness:    float = 0.0
        material_specs:   MaterialSpecs = field(default_factory=dict)
        openmc_universe:  Optional[openmc.Universe] = None
        num_procs:        int = 1
        exclude_excore:   bool = False
        offset:           Optional[Tuple[float, float, float]] = None

        def __post_init__(self) -> None:
            valid_locations = {loc for ring in geometry_elements_triga_netl.Core.RING_MAP for loc in ring}
            invalid = [loc for loc in self.core_specs if loc not in valid_locations]
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
        reactor = element

        elements = []
        element_specs = {}
        for ring in geometry_elements_triga_netl.Core.RING_MAP:
            elements.append([])
            for loc in ring:
                core_cell_specs = self.specs.core_specs.get(loc, None)
                if core_cell_specs is None:
                    core_cell_specs = Reactor.CoreCellSpecs(axial_bounds=reactor.pool_axial_bounds)
                else:
                    core_cell_specs = Reactor.CoreCellSpecs(
                        element_specs        = core_cell_specs.element_specs,
                        outer_region_specs   = core_cell_specs.outer_region_specs,
                        axial_bounds         = reactor.pool_axial_bounds,
                        unionize_radial_mesh = core_cell_specs.unionize_radial_mesh,
                    )
                element                       = reactor.core.full_map.get(loc, None)
                element_bottom_axial_position = reactor.get_element_bottom_axial_position(element)
                stack, stack_specs = build_core_element(core_location                 = loc,
                                                        upper_grid_plate              = reactor.upper_grid_plate,
                                                        lower_grid_plate              = reactor.lower_grid_plate,
                                                        element                       = element,
                                                        element_bottom_axial_position = element_bottom_axial_position,
                                                        outer_material                = reactor.pool.material,
                                                        core_cell_specs               = core_cell_specs)
                stack_specs.apply_material_specs(stack, self.specs.material_specs)
                elements[-1].append(stack)
                element_specs[stack] = stack_specs

        lattice = geometry_elements.HexLattice(pitch          = reactor.core.pitch,
                                               outer_material = reactor.pool.material,
                                               elements       = elements,
                                               name           = f"{reactor.name}",
                                               orientation    = 'y',
                                               map_type       = 'ring')

        lattice_specs = HexLattice.Specs(min_thickness = self.specs.min_thickness,
                                         element_specs = element_specs,
                                         num_procs     = self.specs.num_procs)

        mpact_core = build(lattice, lattice_specs)

        if self.specs.exclude_excore:
            return mpact_core

        openmc_universe = self.specs.openmc_universe or openmc_builder.build(reactor)
        return self._apply_openmc_overlay(mpact_core, openmc_universe, reactor)
    def _apply_openmc_overlay(self,
                              core: mpactpy.Core,
                              openmc_universe: openmc.Universe,
                              reactor: geometry_elements_triga_netl.Reactor
    ) -> mpactpy.Core:

        core = self._add_excore_cells(core, reactor)

        # Only overlay pins/modules/lattices/assemblies that contain voxelized pins
        pins_to_overlay = {pin for pin in core.pins if isinstance(pin.pinmesh, mpactpy.RectangularPinMesh)}
        modules_to_overlay = {m for m in core.modules if pins_to_overlay.intersection(m.pins)}
        lattices_to_overlay = {l for l in core.lattices if modules_to_overlay.intersection(l.modules)}
        assemblies_to_overlay = {a for a in core.assemblies if lattices_to_overlay.intersection(a.lattices)}

        # Create overlay masks
        pin_mask:      mpactpy.Pin.OverlayMask      = set(core.materials)
        module_mask:   mpactpy.Module.OverlayMask   = {pin:      pin_mask      for pin      in pins_to_overlay}
        lattice_mask:  mpactpy.Lattice.OverlayMask  = {module:   module_mask   for module   in modules_to_overlay}
        assembly_mask: mpactpy.Assembly.OverlayMask = {lattice:  lattice_mask  for lattice  in lattices_to_overlay}
        include_only:  mpactpy.Core.OverlayMask     = {assembly: assembly_mask for assembly in assemblies_to_overlay}

        overlay_policy           = mpactpy.PinMesh.OverlayPolicy(num_procs=self.specs.num_procs)

        # Map MPACT materials specs to OpenMC materials
        default_material_specs   = {material: DEFAULT_MPACT_MATERIAL_SPECS[type(material)]
                                    for material in reactor.get_materials() if type(material) in DEFAULT_MPACT_MATERIAL_SPECS}
        material_specs           = default_material_specs | self.specs.material_specs
        material_specs           = {material.name: material_specs[material] for material in material_specs.keys()}
        openmc_materials         = openmc.Materials(list(openmc_universe.get_all_materials().values()))
        overlay_policy.mat_specs = {material: material_specs[material.name]
                                    for material in openmc_materials if material.name in material_specs}

        half_mpact_model_width = core.width['X'] * 0.5
        offset = self.specs.offset or (-half_mpact_model_width, -half_mpact_model_width, 0.0)

        return core.overlay(openmc.Geometry(openmc_universe), offset, include_only, overlay_policy)



    def _add_excore_cells(self,
                          core: mpactpy.Core,
                          reactor: geometry_elements_triga_netl.Reactor
    ) -> mpactpy.Core:

        core_map = core.assembly_map
        if not core_map:
            return core

        axial_mesh = self._get_axial_mesh(reactor)
        if not axial_mesh:
            return core

        row_pitch = next((pitch for pitch in core.pitch["row"] if pitch > 0.0), None)
        col_pitch = next((pitch for pitch in core.pitch["column"] if pitch > 0.0), None)
        assert row_pitch is not None and col_pitch is not None, \
            "MPACT core must have non-zero row and column pitch to add excore cells."

        pad_cols = max(0, ceil((reactor.pool.radius - core.width["X"] * 0.5) / col_pitch))
        pad_rows = max(0, ceil((reactor.pool.radius - core.width["Y"] * 0.5) / row_pitch))
        if pad_rows == 0 and pad_cols == 0:
            return core

        num_rows = len(core_map)
        num_cols = len(core_map[0])
        padded_rows = num_rows + 2 * pad_rows
        padded_cols = num_cols + 2 * pad_cols
        padded_map = [[None for _ in range(padded_cols)]
                      for _ in range(padded_rows)]

        for row_index, row in enumerate(core_map):
            padded_map[row_index + pad_rows][pad_cols:pad_cols + num_cols] = row

        total_width_x = padded_cols * col_pitch
        total_width_y = padded_rows * row_pitch

        for row_index, row in enumerate(padded_map):
            y_center = (row_index + 0.5) * row_pitch - total_width_y * 0.5
            for col_index, assembly in enumerate(row):
                x_center = (col_index + 0.5) * col_pitch - total_width_x * 0.5
                row[col_index] = self._set_cell(assembly,
                                                (col_pitch, row_pitch),
                                                (x_center, y_center),
                                                axial_mesh,
                                                reactor)

        return mpactpy.Core(padded_map,
                            symmetry_opt=core.symmetry_opt,
                            quarter_sym_opt=core.quarter_sym_opt,
                            min_thickness=self.specs.min_thickness)



    def _get_axial_mesh(self, reactor: geometry_elements_triga_netl.Reactor
    ) -> List[float]:

        pool_bottom, pool_top = reactor.pool_axial_bounds
        reflector_bottom, reflector_top = reactor.reflector_axial_bounds
        rsr_bottom, _ = reactor.rsr_axial_bounds

        points = [pool_bottom,
                  pool_top,
                  reflector_bottom,
                  reflector_top,
                  rsr_bottom]

        for beamport_id in (1, 2, 3, 4):
            points.extend(reactor.beamport_axial_bounds[beamport_id])

        def within_pool(z: float) -> bool:
            return ((z > pool_bottom or isclose(z, pool_bottom, rel_tol=TOL, abs_tol=TOL)) and
                    (z < pool_top or isclose(z, pool_top, rel_tol=TOL, abs_tol=TOL)))

        points = sorted(z for z in points if within_pool(z))

        unique_points: List[float] = []
        for z in points:
            if not unique_points or not isclose(z, unique_points[-1], rel_tol=TOL):
                unique_points.append(z)

        if len(unique_points) < 2:
            return []

        axial_mesh = []
        for start, stop in zip(unique_points[:-1], unique_points[1:]):
            length = stop - start
            if isclose(length, 0.0, rel_tol=TOL, abs_tol=TOL):
                continue
            if length < 0.0:
                raise ValueError("Axial mesh points must be ordered from bottom to top.")
            axial_mesh.append(length)

        return axial_mesh



    def _set_cell(self,
                  assembly: Optional[mpactpy.Assembly],
                  side_lengths: Tuple[float, float],
                  radial_location: Tuple[float, float],
                  axial_mesh: List[float],
                  reactor: geometry_elements_triga_netl.Reactor,
    ) -> Optional[mpactpy.Assembly]:

        if not axial_mesh:
            return None

        rect = Rectangle(w=side_lengths[0], h=side_lengths[1])
        if reactor.shroud_inner_contains(rect, radial_location) and assembly is not None:
            return assembly

        if not reactor.pool_contains(rect, radial_location):
            return None

        voxel_specs = self.specs.voxelation_specs
        material = mpactpy.Material(temperature=300.0,
                                    number_densities={"H1": 1.0})

        lattice_cache: Dict[Tuple[float, float], mpactpy.Lattice] = {}
        lattice_map: List[mpactpy.Lattice] = []
        z_cursor = reactor.pool_axial_bounds[0]
        for length in axial_mesh:
            z_next = z_cursor + length
            axial_bounds = (z_cursor, z_next)
            z_cursor = z_next

            target_thicknesses: List[float] = []
            if reactor.shroud_intersects(rect, radial_location, axial_bounds):
                target_thicknesses.append(voxel_specs.shroud_target_thicknesses)
            if reactor.rsr_intersects(rect, radial_location, axial_bounds):
                target_thicknesses.append(voxel_specs.rsr_target_thicknesses)
            if reactor.reflector_intersects(rect, radial_location, axial_bounds):
                target_thicknesses.append(voxel_specs.reflector_target_thicknesses)
            if reactor.any_beamport_intersects(rect, radial_location, axial_bounds):
                target_thicknesses.append(voxel_specs.beamport_target_thicknesses)

            if not target_thicknesses:
                target_thicknesses.append(voxel_specs.pool_target_thicknesses)

            target_thickness = min(target_thicknesses)

            lattice = None
            for (cached_length, cached_thickness), cached_lattice in lattice_cache.items():
                if (isclose(length, cached_length, rel_tol=TOL, abs_tol=TOL) and
                        isclose(target_thickness, cached_thickness, rel_tol=TOL, abs_tol=TOL)):
                    lattice = cached_lattice
                    break
            if lattice is None:
                pin = mpactpy.build_rec_pin(
                    thicknesses={"X": [side_lengths[0]],
                                 "Y": [side_lengths[1]],
                                 "Z": [length]},
                    materials=[material],
                    target_cell_thicknesses={"X": target_thickness, "Y": target_thickness},
                )
                module = mpactpy.Module(1, [[pin]])
                lattice = mpactpy.Lattice([[module]])
                lattice_cache[(length, target_thickness)] = lattice
            lattice_map.append(lattice)

        return mpactpy.Assembly(lattice_map)


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
    if element is None:
        return _build_core_location_with_water_hole(upper_grid_plate,
                                                    lower_grid_plate,
                                                    axial_bounds,
                                                    outer_material,
                                                    core_location,
                                                    outer_region_specs)

    stack, specs = _build_core_location_with_element(upper_grid_plate,
                                                     lower_grid_plate,
                                                     element,
                                                     element_bottom_axial_position,
                                                     axial_bounds,
                                                     outer_material,
                                                     core_location,
                                                     element_specs,
                                                     outer_region_specs)
    if core_cell_specs.unionize_radial_mesh:
        old_segments = stack.segments
        old_specs = specs
        stack = stack.unionize_radial_mesh()
        segment_specs = {new_segment: old_specs.segment_specs.get(old_segment)
                         for new_segment, old_segment in zip(stack.segments, old_segments)}
        specs = Stack.Specs(segment_specs=segment_specs, num_procs=old_specs.num_procs)

    return stack, specs


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

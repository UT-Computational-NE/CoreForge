from __future__ import annotations
from typing import Dict, List, Optional, Tuple, TypeAlias, TypedDict
from dataclasses import dataclass, field
from math import ceil, inf, isclose, isfinite, isinf

import openmc
import mpactpy
from mpactpy.utils import ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge import geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl
from coreforge.materials import Material
from coreforge.shapes import Interval, Rectangle
from coreforge import openmc_builder
from coreforge.mpact_builder.builder import AxisBounds, Bounds, Builder
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs, DEFAULT_MPACT_MATERIAL_SPECS
from coreforge.mpact_builder.hex_lattice import HexLattice
from coreforge.mpact_builder.infinite_medium import InfiniteMedium
from coreforge.mpact_builder.stack import Stack
import coreforge.mpact_builder.stack as stack_builder
from coreforge.mpact_builder.mpact_builder import build, get_builder, register_builder
from coreforge.mpact_builder.triga.core_element import CoreElement
from coreforge.mpact_builder.triga.cylindrical_stack import CylindricalStack
from coreforge.mpact_builder.triga.fuel_element import FuelElement
from coreforge.mpact_builder.triga.graphite_element import GraphiteElement
from .central_thimble import CentralThimble
from .fuel_follower_control_rod import FuelFollowerControlRod
from .source_holder import SourceHolder
from .transient_rod import TransientRod


def _default_voxelation_specs() -> "Reactor.VoxelationSpecs":
    return Reactor.VoxelationSpecs()


def _default_excore_specs() -> "Reactor.ExcoreSpecs":
    return Reactor.ExcoreSpecs()


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
                                   CylindricalStack.Specs |
                                   SourceHolder.Specs |
                                   TransientRod.Specs |
                                   FuelFollowerControlRod.Specs)

    @dataclass
    class CoreCellSpecs:
        """Specifications for a single core location build.

        Attributes
        ----------
        element_specs : Optional[Reactor.CoreElementSpecs]
            Builder specifications for the core element at this location. Must be
            consistent with the element being built.
        outer_region_specs : Optional[Reactor.VoxelationSpecs | CoreElement.SegmentSpecs]
            Specifications for axial regions outside the core element. Use
            VoxelationSpecs when there are no grid plate penetrations, and
            CoreElement.SegmentSpecs (CylindricalPinCell.Specs) when
            penetrations are present.
        voxelization_specs : Optional[Reactor.VoxelationSpecs]
            Specifications for representing the complete core location as a
            rectangular voxel mesh. When omitted, populated core locations use
            their analytic MPACT representation.
        axial_bounds : Optional[Interval]
            Lower and upper axial bounds (cm) to clip the constructed stack.
        unionize_radial_mesh : bool
            Whether to unionize the radial mesh across stack segments when a core
            element is present.  Only applicable for cells with core elements.
        """

        element_specs:      Optional[Reactor.CoreElementSpecs] = None
        outer_region_specs: Optional[Reactor.VoxelationSpecs | CoreElement.SegmentSpecs] = None
        voxelization_specs: Optional[Reactor.VoxelationSpecs] = None
        axial_bounds:       Optional[Interval | Tuple[float, float]] = None
        unionize_radial_mesh: bool = False

        def __post_init__(self) -> None:
            if self.axial_bounds is not None:
                if not isinstance(self.axial_bounds, Interval):
                    self.axial_bounds = Interval(*self.axial_bounds)
                assert self.axial_bounds.upper > self.axial_bounds.lower, \
                    (f"Upper axial bound {self.axial_bounds.upper} must be greater than lower axial bound "
                     f"{self.axial_bounds.lower}.")

    @dataclass
    class VoxelationSpecs:
        """Voxel mesh specifications for a geometry region.

        Attributes
        ----------
        target_thicknesses : Optional[TargetThicknesses]
            Target voxel thicknesses (cm). ``radial`` is used for X/Y
            voxelation and ``axial`` is used to add axial mesh points. Missing
            targets default to infinity.
        axial_points : List[float]
            Required axial mesh points in the reactor coordinate system (cm).
        """

        class TargetThicknesses(TypedDict, total=False):
            """Target voxel thicknesses by direction."""

            radial: float
            axial:  float

        target_thicknesses: Optional[TargetThicknesses] = None
        axial_points: List[float] = field(default_factory=list)

        def __post_init__(self) -> None:
            self.target_thicknesses = dict(self.target_thicknesses or {})
            self.axial_points = list(self.axial_points)

            for direction in ["radial", "axial"]:
                self.target_thicknesses.setdefault(direction, inf)

            assert all(target > 0.0 for target in self.target_thicknesses.values()), \
                f"VoxelationSpecs.target_thicknesses = {self.target_thicknesses}"
            if not all(isfinite(point) for point in self.axial_points):
                raise ValueError(f"Axial mesh points must be finite: {self.axial_points}")

    @dataclass
    class ExcoreSpecs:
        """Specifications for excore region construction.

        Axial voxelation targets from these regions are combined into one
        global MPACT axial mesh before excore overlay. If multiple overlapping
        regions specify finite axial targets, their mesh points are unionized;
        for paired regions such as RSR cavity/tube or beamport exterior/interior,
        it is usually best to set one axial target and leave the other
        unspecified.

        Attributes
        ----------
        shroud : Reactor.VoxelationSpecs
            Voxelation specifications for the shroud region.
        rsr_cavity : Reactor.VoxelationSpecs
            Voxelation specifications for the RSR cavity region.
        rsr_tube : Reactor.VoxelationSpecs
            Voxelation specifications for RSR tube regions.
        reflector : Reactor.VoxelationSpecs
            Voxelation specifications for the reflector region.
        beamport_exterior : Reactor.VoxelationSpecs
            Voxelation specifications for beamport exterior regions.
        beamport_interior : Reactor.VoxelationSpecs
            Voxelation specifications for beamport interior regions.
        pool : Reactor.VoxelationSpecs
            Voxelation specifications for the pool region.
        """

        shroud:            Reactor.VoxelationSpecs = field(default_factory=_default_voxelation_specs)
        rsr_cavity:        Reactor.VoxelationSpecs = field(default_factory=_default_voxelation_specs)
        rsr_tube:          Reactor.VoxelationSpecs = field(default_factory=_default_voxelation_specs)
        reflector:         Reactor.VoxelationSpecs = field(default_factory=_default_voxelation_specs)
        beamport_exterior: Reactor.VoxelationSpecs = field(default_factory=_default_voxelation_specs)
        beamport_interior: Reactor.VoxelationSpecs = field(default_factory=_default_voxelation_specs)
        pool:              Reactor.VoxelationSpecs = field(default_factory=_default_voxelation_specs)


    @dataclass
    class Specs(BuilderSpecs):
        """ Building specifications for Reactor

        Attributes
        ----------
        core_specs : Dict[str, Reactor.CoreCellSpecs]
            Per-location overrides for core element specs.
        excore_specs : Reactor.ExcoreSpecs
            Specifications for excore region construction.
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

        core_specs:      Dict[str, Reactor.CoreCellSpecs] = field(default_factory=dict)
        excore_specs:    Reactor.ExcoreSpecs = field(default_factory=_default_excore_specs)
        min_thickness:   float = 0.0
        material_specs:  MaterialSpecs = field(default_factory=dict)
        openmc_universe: Optional[openmc.Universe] = None
        num_procs:       int = 1
        exclude_excore:  bool = False
        offset:          Optional[Tuple[float, float, float]] = None

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
                    core_cell_specs = Reactor.CoreCellSpecs(axial_bounds=reactor.pool.axial_bounds)
                else:
                    core_cell_specs = Reactor.CoreCellSpecs(
                        element_specs        = core_cell_specs.element_specs,
                        outer_region_specs   = core_cell_specs.outer_region_specs,
                        voxelization_specs   = core_cell_specs.voxelization_specs,
                        axial_bounds         = reactor.pool.axial_bounds,
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

        has_incore_overlay = any(core_cell_specs.voxelization_specs is not None
                                 for core_cell_specs in self.specs.core_specs.values())
        if self.specs.exclude_excore and not has_incore_overlay:
            return mpact_core

        openmc_universe = self.specs.openmc_universe or openmc_builder.build(reactor)
        return self._apply_openmc_overlay(mpact_core, openmc_universe, reactor)


    def _apply_openmc_overlay(self,
                              core: mpactpy.Core,
                              openmc_universe: openmc.Universe,
                              reactor: geometry_elements_triga_netl.Reactor
    ) -> mpactpy.Core:

        core = core if self.specs.exclude_excore else self._add_excore_cells(core, reactor)

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

        overlay_policy = mpactpy.PinMesh.OverlayPolicy(num_procs=self.specs.num_procs)

        # Map MPACT material specs to OpenMC materials by material name.
        material_specs = {}
        for material in reactor.get_materials():
            mpact_specs = self.specs.material_specs.get(material, DEFAULT_MPACT_MATERIAL_SPECS.get(type(material)))
            if mpact_specs is not None:
                material_specs[material.name] = mpact_specs

        openmc_materials = openmc.Materials(list(openmc_universe.get_all_materials().values()))
        overlay_policy.mat_specs = {material: material_specs[material.name]
                                    for material in openmc_materials if material.name in material_specs}

        offset = self.specs.offset or (-core.width['X'] * 0.5,
                                       -core.width['Y'] * 0.5,
                                       reactor.pool.axial_bounds.lower)

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
            y_center = total_width_y * 0.5 - (row_index + 0.5) * row_pitch
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

        pool_bottom = reactor.pool.axial_bounds.lower
        pool_top = reactor.pool.axial_bounds.upper
        excore_specs = self.specs.excore_specs

        points = []

        def add_mesh_points(bounds: Interval,
                            specs: Reactor.VoxelationSpecs) -> None:
            points.extend(bounds.bounds)

            def within_bounds(point: float) -> bool:
                return ((point > bounds.lower or isclose(point, bounds.lower, rel_tol=TOL, abs_tol=TOL)) and
                        (point < bounds.upper or isclose(point, bounds.upper, rel_tol=TOL, abs_tol=TOL)))

            invalid_points = [point for point in specs.axial_points if not within_bounds(point)]
            if invalid_points:
                raise ValueError(f"Axial mesh point(s) {invalid_points} are outside feature bounds {bounds.bounds}")
            points.extend(specs.axial_points)

            target = specs.target_thicknesses["axial"]
            if isinf(target):
                return

            lower = max(bounds.lower, pool_bottom)
            upper = min(bounds.upper, pool_top)
            length = upper - lower
            if isclose(length, 0.0, rel_tol=TOL, abs_tol=TOL):
                return
            if length < 0.0:
                return

            num_subdivisions = max(1, ceil(length / target))
            subd_length = length / num_subdivisions
            points.extend(lower + i * subd_length for i in range(num_subdivisions + 1))

        add_mesh_points(reactor.pool.axial_bounds, excore_specs.pool)
        add_mesh_points(reactor.shroud.axial_bounds, excore_specs.shroud)
        add_mesh_points(reactor.rotary_specimen_rack_cavity.axial_bounds, excore_specs.rsr_cavity)
        add_mesh_points(reactor.rotary_specimen_rack_cavity.axial_bounds, excore_specs.rsr_tube)
        add_mesh_points(reactor.reflector.axial_bounds, excore_specs.reflector)
        for beamport_id in (1, 2, 3, 4):
            add_mesh_points(reactor.beam_port[beamport_id].axial_bounds, excore_specs.beamport_exterior)
            add_mesh_points(reactor.beam_port[beamport_id].interior_axial_bounds, excore_specs.beamport_interior)

        def within_pool(z: float) -> bool:
            return ((z > pool_bottom or isclose(z, pool_bottom, rel_tol=TOL, abs_tol=TOL)) and
                    (z < pool_top or isclose(z, pool_top, rel_tol=TOL, abs_tol=TOL)))

        points = sorted(z for z in points if within_pool(z))

        unique_points: List[float] = []
        for z in points:
            if not unique_points or not isclose(z, unique_points[-1], rel_tol=TOL, abs_tol=TOL):
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
        if reactor.shroud.contains(rect, radial_location) and assembly is not None:
            return assembly

        if not reactor.pool.contains(rect, radial_location):
            return None

        excore_specs = self.specs.excore_specs
        voxel_material = geometry_elements.InfiniteMedium(reactor.pool.material, name="excore_voxel")

        gride_plate_bounds = Interval(reactor.lower_grid_plate.axial_bounds.lower,
                                      reactor.upper_grid_plate.axial_bounds.upper)

        lattice_cache: Dict[Tuple[float, float], mpactpy.Lattice] = {}
        lattice_map: List[mpactpy.Lattice] = []
        z_cursor = reactor.pool.axial_bounds.lower
        for length in axial_mesh:
            z_next = z_cursor + length
            axial_bounds = Interval(z_cursor, z_next)
            z_cursor = z_next

            between_grid_plate_bounds = axial_bounds.intersects(gride_plate_bounds)

            target_thicknesses: List[float] = []
            if reactor.shroud.intersects(rect, radial_location) and between_grid_plate_bounds:
                target_thicknesses.append(excore_specs.shroud.target_thicknesses["radial"])
            if reactor.rsr_cavity_intersects(rect, radial_location, axial_bounds):
                target_thicknesses.append(excore_specs.rsr_cavity.target_thicknesses["radial"])
            if reactor.rsr_tube_intersects(rect, radial_location, axial_bounds):
                target_thicknesses.append(excore_specs.rsr_tube.target_thicknesses["radial"])
            if reactor.reflector_intersects(rect, radial_location, axial_bounds):
                target_thicknesses.append(excore_specs.reflector.target_thicknesses["radial"])
            for bp in (1, 2, 3, 4):
                if reactor.beam_port[bp].intersects(rect, radial_location, axial_bounds):
                    if reactor.beam_port[bp].contains(rect, radial_location, axial_bounds):
                        target_thicknesses.append(excore_specs.beamport_interior.target_thicknesses["radial"])
                    else:
                        target_thicknesses.append(excore_specs.beamport_exterior.target_thicknesses["radial"])

            if not target_thicknesses:
                target_thicknesses.append(excore_specs.pool.target_thicknesses["radial"])

            target_thickness = min(target_thicknesses)

            lattice = None
            for (cached_length, cached_thickness), cached_lattice in lattice_cache.items():
                if (isclose(length, cached_length, rel_tol=TOL, abs_tol=TOL) and
                        isclose(target_thickness, cached_thickness, rel_tol=TOL, abs_tol=TOL)):
                    lattice = cached_lattice
                    break
            if lattice is None:
                voxel_build_specs = InfiniteMedium.Specs(
                    target_cell_thicknesses = {"X": target_thickness,
                                               "Y": target_thickness},
                    divide_materials        = True,
                    material_specs          = self.specs.material_specs,
                )
                voxel_bounds = Bounds(
                    X = AxisBounds(min=0.0, max=side_lengths[0]),
                    Y = AxisBounds(min=0.0, max=side_lengths[1]),
                    Z = AxisBounds(min=0.0, max=length),
                )
                lattice = build(voxel_material, voxel_build_specs, voxel_bounds).lattices[0]
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
    voxelization_specs = core_cell_specs.voxelization_specs
    axial_bounds       = core_cell_specs.axial_bounds

    upper_penetration_radius = upper_grid_plate.geometry.penetration_map.get(core_location)
    lower_penetration_radius = lower_grid_plate.geometry.penetration_map.get(core_location)

    both_grids_have_penetrations       = upper_penetration_radius and lower_penetration_radius
    both_grid_do_not_have_penetrations = not upper_penetration_radius and not lower_penetration_radius
    assert both_grids_have_penetrations or both_grid_do_not_have_penetrations, \
        "Both upper and lower penetration radii must be provided or both must be None."

    if element is not None:
        outer_material = outer_material or element.outer_material

    assert outer_material is not None, "outer_material must be provided if element is None."

    if axial_bounds is None:
        axial_bounds = Interval(lower_grid_plate.axial_bounds.lower, upper_grid_plate.axial_bounds.upper)

        if element is not None:
            assert element_bottom_axial_position is not None, \
                "element_bottom_axial_position must be provided if element is not None and axial_bounds is None."
            axial_bounds = Interval(min(axial_bounds.lower, element_bottom_axial_position),
                                    max(axial_bounds.upper, element_bottom_axial_position + element.length))

    if voxelization_specs is not None:
        return _build_voxelized_core_location(upper_grid_plate,
                                               lower_grid_plate,
                                               axial_bounds,
                                               outer_material,
                                               voxelization_specs)

    if outer_region_specs is None:
        outer_region_specs = (
            CoreElement.SegmentSpecs()
            if both_grids_have_penetrations
            else Reactor.VoxelationSpecs()
        )

    if both_grids_have_penetrations:
        assert isinstance(outer_region_specs, CoreElement.SegmentSpecs), \
            "outer_region_specs must be CoreElement.SegmentSpecs when penetrations are present."
    else:
        assert isinstance(outer_region_specs, Reactor.VoxelationSpecs), \
            "outer_region_specs must be Reactor.VoxelationSpecs when no penetrations are present."

    if element is not None:
        assert element_bottom_axial_position is not None, \
            "element_bottom_axial_position must be provided if element is not None."
        assert both_grids_have_penetrations, \
            "Grid plate penetration radii must be provided for core locations with elements."

    if upper_penetration_radius is None and lower_penetration_radius is None:
        return _build_voxelized_core_location(upper_grid_plate,
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


def _build_voxelized_core_location(
    upper_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    axial_bounds:       Interval,
    outer_material:     Material,
    voxelization_specs: Optional[Reactor.VoxelationSpecs] = None,
) -> Tuple[geometry_elements.Stack, Stack.Specs]:
    voxelization_specs = voxelization_specs or Reactor.VoxelationSpecs()

    def within_axial_bounds(point: float) -> bool:
        return ((point > axial_bounds.lower or
                 isclose(point, axial_bounds.lower, rel_tol=TOL, abs_tol=TOL)) and
                (point < axial_bounds.upper or
                 isclose(point, axial_bounds.upper, rel_tol=TOL, abs_tol=TOL)))

    invalid_points = [point for point in voxelization_specs.axial_points
                      if not within_axial_bounds(point)]
    if invalid_points:
        raise ValueError(f"Axial mesh point(s) {invalid_points} are outside core cell bounds {axial_bounds.bounds}")

    points = [axial_bounds.lower, axial_bounds.upper]
    points.extend(voxelization_specs.axial_points)
    points.extend(lower_grid_plate.axial_bounds.bounds)
    points.extend(upper_grid_plate.axial_bounds.bounds)

    def clamp_to_axial_bounds(point: float) -> float:
        if isclose(point, axial_bounds.lower, rel_tol=TOL, abs_tol=TOL):
            return axial_bounds.lower
        if isclose(point, axial_bounds.upper, rel_tol=TOL, abs_tol=TOL):
            return axial_bounds.upper
        return point

    points = sorted(clamp_to_axial_bounds(point) for point in points if within_axial_bounds(point))
    unique_points: List[float] = []
    for point in points:
        if not unique_points or not isclose(point, unique_points[-1], rel_tol=TOL, abs_tol=TOL):
            unique_points.append(point)

    axial_target = voxelization_specs.target_thicknesses["axial"]
    if not isinf(axial_target):
        subdivided_points = [unique_points[0]]
        for lower, upper in zip(unique_points[:-1], unique_points[1:]):
            num_subdivisions = max(1, ceil((upper - lower) / axial_target))
            subd_length = (upper - lower) / num_subdivisions
            subdivided_points.extend(lower + i * subd_length for i in range(1, num_subdivisions + 1))
        unique_points = subdivided_points

    def material_at(point: float) -> Material:
        for grid_plate in [lower_grid_plate, upper_grid_plate]:
            bounds = grid_plate.axial_bounds
            if point > bounds.lower and point < bounds.upper:
                return grid_plate.geometry.material
        return outer_material

    radial_target = voxelization_specs.target_thicknesses["radial"]
    segments = []
    segment_specs = {}
    for lower, upper in zip(unique_points[:-1], unique_points[1:]):
        midpoint = 0.5 * (lower + upper)
        material = material_at(midpoint)
        segment = geometry_elements.Stack.Segment(
            element = geometry_elements.InfiniteMedium(material, name="voxelized_region"),
            length  = upper - lower,
        )
        segments.append(segment)
        segment_specs[segment] = Stack.Segment.Specs(
            builder_specs = InfiniteMedium.Specs(
                target_cell_thicknesses = {"X": radial_target, "Y": radial_target},
                divide_materials        = True,
            ),
        )

    stack = geometry_elements.Stack(segments   = segments,
                                    name       = "voxelized_core_location",
                                    bottom_pos = axial_bounds.lower)
    return stack, Stack.Specs(segment_specs)


def _build_core_location_with_water_hole(
    upper_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate:   geometry_elements_triga_netl.Reactor.GridPlate,
    axial_bounds:       Interval,
    outer_material:     Material,
    core_location:      str,
    outer_region_specs: Optional[CoreElement.SegmentSpecs] = None,
) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:

    outer_pincell = _build_outer_pincell(upper_grid_plate,
                                         lower_grid_plate,
                                         outer_material,
                                         core_location)

    buffer       = axial_bounds.length
    stack_bottom = lower_grid_plate.axial_bounds.lower - buffer

    segment = geometry_elements.Stack.Segment(
        element = outer_pincell,
        length  = upper_grid_plate.axial_bounds.upper - lower_grid_plate.axial_bounds.lower + 2 * buffer,
    )

    stack = geometry_elements.CylindricalStack(
        segments   = [segment],
        name       = f"{core_location}_outer_stack",
        bottom_pos = stack_bottom)
    stack_specs = Stack.Specs({segment: outer_region_specs})

    stack, specs = stack_builder.get_axial_slice(stack, stack_specs, axial_bounds.lower, axial_bounds.upper)
    stack, specs = _add_grid_plates_to_stack(stack, specs, upper_grid_plate, lower_grid_plate, core_location)
    return stack, specs


def _build_core_location_with_element(
    upper_grid_plate:              geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate:              geometry_elements_triga_netl.Reactor.GridPlate,
    element:                       geometry_elements_triga_netl.Core.Element,
    element_bottom_axial_position: float,
    axial_bounds:                  Interval,
    outer_material:                Material,
    core_location:                 str,
    element_specs:                 Optional[Reactor.CoreElementSpecs] = None,
    outer_region_specs:            Optional[CoreElement.SegmentSpecs] = None,
) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:

    outer_pincell = _build_outer_pincell(upper_grid_plate,
                                         lower_grid_plate,
                                         outer_material,
                                         core_location)

    builder_cls: CoreElement = get_builder(element)
    element_stack, element_stack_specs = builder_cls(element_specs).build_stack_and_specs(element)
    element_top = element_bottom_axial_position + element_stack.length

    buffer = axial_bounds.length
    stack_bottom = min(lower_grid_plate.axial_bounds.lower, element_bottom_axial_position) - buffer
    stack_top    = max(upper_grid_plate.axial_bounds.upper, element_top) + buffer

    bottom_segment = geometry_elements.Stack.Segment(
        element = outer_pincell,
        length  = element_bottom_axial_position - stack_bottom,
    )
    top_segment = geometry_elements.Stack.Segment(
        element = outer_pincell,
        length  = stack_top - element_top,
    )

    segments = [bottom_segment] + element_stack.segments + [top_segment]
    stack = geometry_elements.CylindricalStack(
        segments   = segments,
        name       = f"{core_location}_element_stack",
        bottom_pos = stack_bottom)

    segment_specs = {bottom_segment: outer_region_specs,
                     top_segment: outer_region_specs,}
    segment_specs.update(element_stack_specs.segment_specs)
    stack_specs = Stack.Specs(segment_specs=segment_specs,
                              num_procs=element_stack_specs.num_procs)

    stack, specs = stack_builder.get_axial_slice(stack, stack_specs, axial_bounds.lower, axial_bounds.upper)
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
    stack:            geometry_elements.CylindricalStack,
    stack_specs:      Stack.Specs,
    upper_grid_plate: geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate: geometry_elements_triga_netl.Reactor.GridPlate,
    core_location:    str,
) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:

    for grid_plate in (lower_grid_plate, upper_grid_plate):
        penetration_radius = grid_plate.geometry.penetration_map.get(core_location)
        assert penetration_radius is not None, \
            f"No penetration radius for core location {core_location}."

        grid_part = _build_grid_stack_and_specs(stack,
                                                stack_specs,
                                                grid_plate.axial_bounds.upper,
                                                grid_plate.axial_bounds.lower,
                                                grid_plate.geometry.material,
                                                penetration_radius)
        if grid_part is None:
            continue

        grid_stack, grid_specs = grid_part

        lower_part = stack_builder.get_axial_slice(stack, stack_specs, stack.bottom_pos, grid_plate.axial_bounds.lower)
        upper_part = stack_builder.get_axial_slice(stack, stack_specs, grid_plate.axial_bounds.upper,
                                                   stack.bottom_pos + stack.length)

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

        stack = type(stack)(segments   = segments,
                            name       = stack.name,
                            bottom_pos = stack.bottom_pos)
        stack_specs = Stack.Specs(segment_specs=segment_specs, num_procs=stack_specs.num_procs)

    return stack, stack_specs


def _build_grid_stack_and_specs(
    stack:              geometry_elements.CylindricalStack,
    stack_specs:        Stack.Specs,
    plate_top:          float,
    plate_bottom:       float,
    plate_material:     Material,
    penetration_radius: float,
) -> Optional[Tuple[geometry_elements.CylindricalStack, Stack.Specs]]:

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

    grid_stack = type(stack)(segments   = grid_segments,
                             name       = stack.name,
                             bottom_pos = plate_bottom)
    grid_specs = Stack.Specs(segment_specs=grid_segment_specs, num_procs=stack_specs.num_procs)
    return grid_stack, grid_specs

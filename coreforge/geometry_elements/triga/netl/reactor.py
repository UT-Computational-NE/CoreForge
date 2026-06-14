from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from math import cos, isclose, radians, sin, sqrt

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material, unique_materials
from coreforge.shapes import Circle, Hexagon, Interval, Rectangle
from coreforge.geometry_elements.triga import FuelElement as FuelElementGeometry, GraphiteElement as GraphiteElementGeometry
from .beam_port import BeamPort as BeamPortGeometry
from .core import Core as CoreGeometry
from .grid_plate import GridPlate as GridPlateGeometry
from .pool import Pool as PoolGeometry
from .reflector import Reflector as ReflectorGeometry
from .rsr_cavity import RSRCavity as RSRCavityGeometry
from .shroud import Shroud as ShroudGeometry
from .central_thimble import CentralThimble as CentralThimbleGeometry
from .source_holder import SourceHolder as SourceHolderGeometry


# pylint: disable=too-many-public-methods
class Reactor(GeometryElement):
    """Top-level TRIGA NETL reactor geometry container with placement metadata.

    Notes
    -----
    The reactor's core axial centerline is taken as the origin for axial placements,
    meaning that the axial centerline of the fuel elements is at z = 0 cm.
    Reactor-owned component wrappers expose reactor-context metadata through
    ``axial_bounds`` and cached radial boundaries while forwarding geometry
    attributes to their underlying geometry objects.

    Parameters
    ----------
    pool : PoolGeometry
        Reactor pool geometry. The reactor wraps it as ``Reactor.Pool``.
    reflector : Reactor.Reflector
        Graphite reflector canister and its core offset.
    shroud : ShroudGeometry
        Aluminum shroud geometry surrounding the core/reflector region. The
        reactor wraps it as ``Reactor.Shroud``.
    beam_port_1_5 : Reactor.BeamPort
        Beam port located at the shared 1/5 position with rotation/translation.
    beam_port_2 : Reactor.BeamPort
        Beam port 2 geometry with rotation/translation.
    beam_port_3 : Reactor.BeamPort
        Beam port 3 geometry with rotation/translation.
    beam_port_4 : Reactor.BeamPort
        Beam port 4 geometry with rotation/translation.
    rotary_specimen_rack_cavity : RSRCavityGeometry
        Rotary specimen rack cavity geometry. The reactor wraps it as
        ``Reactor.RSRCavity``.
    core : CoreGeometry
        Core geometry and loading definition.
    upper_grid_plate : Reactor.GridPlate
        Upper grid plate geometry and its axial offset.
    lower_grid_plate : Reactor.GridPlate
        Lower grid plate geometry and its axial offset.
    transient_rod_position : float
        Axial position (cm) for the bottom of the transient rod.
    regulating_rod_position : float
        Axial position (cm) for the bottom of the regulating rod.
    shim_1_rod_position : float
        Axial position (cm) for the bottom of shim 1.
    shim_2_rod_position : float
        Axial position (cm) for the bottom of shim 2.
    name : str, optional
        Name for this reactor element.

    Attributes
    ----------
    pool : Reactor.Pool
        Reactor pool geometry, axial bounds, and circular radial boundary.
    reflector : Reactor.Reflector
        Graphite reflector canister, core offset, axial bounds, and circular
        radial boundary.
    shroud : Reactor.Shroud
        Aluminum shroud geometry, axial bounds, and inner/outer hexagonal
        radial boundaries.
    beam_port : Dict[int, Reactor.BeamPort]
        Mapping of beam port IDs to beam port placement wrappers. IDs 1 and 5
        intentionally reference the same ``Reactor.BeamPort`` instance.
    rotary_specimen_rack_cavity : Reactor.RSRCavity
        Rotary specimen rack cavity geometry, axial bounds, and circular radial
        boundary.
    core : CoreGeometry
        Core geometry and loading definition.
    upper_grid_plate : Reactor.GridPlate
        Upper grid plate geometry, axial offset, and axial bounds.
    lower_grid_plate : Reactor.GridPlate
        Lower grid plate geometry, axial offset, and axial bounds.
    transient_rod_position : float
        Axial position (cm) for the bottom of the transient rod.
    regulating_rod_position : float
        Axial position (cm) for the bottom of the regulating rod.
    shim_1_rod_position : float
        Axial position (cm) for the bottom of shim 1.
    shim_2_rod_position : float
        Axial position (cm) for the bottom of shim 2.
    name : str
        Name for this reactor element.
    """

    class Pool:
        """Pool geometry plus reactor-context bounds.

        Parameters
        ----------
        geometry : PoolGeometry
            Reactor pool geometry.

        Attributes
        ----------
        geometry : PoolGeometry
            Wrapped pool geometry.
        outer_boundary : Circle
            Circular pool radial boundary centered on the reactor origin.
        axial_bounds : Interval
            Lower and upper pool bounds (cm) relative to the core centerline.
        """
        def __init__(self, geometry: PoolGeometry) -> None:
            self._geometry = geometry
            self._outer_boundary = Circle(geometry.radius)
            self._axial_bounds = Interval(-0.5 * geometry.height, 0.5 * geometry.height)

        @property
        def geometry(self) -> PoolGeometry:
            return self._geometry

        @property
        def outer_boundary(self) -> Circle:
            return self._outer_boundary

        @property
        def axial_bounds(self) -> Interval:
            assert self._axial_bounds is not None, "Pool axial bounds have not been assigned."
            return self._axial_bounds

        def __getattr__(self, name: str) -> object:
            return getattr(object.__getattribute__(self, "_geometry"), name)

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, Reactor.Pool) and
                    self.geometry == other.geometry and
                    self._axial_bounds == other._axial_bounds)

        def __hash__(self) -> int:
            return hash((self.geometry, self._axial_bounds))

        def contains(self,
                     cell: Rectangle,
                     center: Tuple[float, float] = (0.0, 0.0),
                     axial_bounds: Optional[Interval] = None) -> bool:
            """Check whether a rectangular cell is fully inside the pool.

            Parameters
            ----------
            cell : Rectangle
                Rectangular XY footprint to test.
            center : Tuple[float, float]
                ``(x, y)`` center of the cell footprint.
            axial_bounds : Optional[Interval]
                Optional lower and upper axial bounds (cm) for the cell. When
                provided, the interval must be fully contained in
                ``self.axial_bounds``.

            Returns
            -------
            bool
                True if the cell is axially inside the pool and its XY footprint
                is fully contained by the pool radial boundary.
            """
            if axial_bounds is not None and not self.axial_bounds.contains(axial_bounds):
                return False
            return self.outer_boundary.contains(cell, other_center=center)


    class Shroud:
        """Shroud geometry plus reactor-context bounds.

        Parameters
        ----------
        geometry : ShroudGeometry
            Aluminum shroud geometry surrounding the core/reflector region.

        Attributes
        ----------
        geometry : ShroudGeometry
            Wrapped shroud geometry.
        inner_boundary : Reactor.Shroud.RadialBoundary
            Primary and 30-degree-rotated hexagons defining the inner shroud aperture.
        outer_boundary : Reactor.Shroud.RadialBoundary
            Primary and 30-degree-rotated hexagons defining the shroud exterior.
        axial_bounds : Interval
            Lower and upper shroud bounds (cm) relative to the core centerline.
        """

        @dataclass
        class RadialBoundary:
            """Pair of hexagonal radial boundaries.

            Attributes
            ----------
            primary_hex : Hexagon
                Hexagon in the primary shroud orientation.
            rotated_hex : Hexagon
                Hexagon rotated 30 degrees from the primary shroud orientation.
            """
            primary_hex: Hexagon
            rotated_hex: Hexagon

        def __init__(self, geometry: ShroudGeometry) -> None:
            self._geometry = geometry

            primary_hex_inner_radius = geometry.primary_hex_inner_radius
            rotated_hex_inner_radius = geometry.rotated_hex_inner_radius
            thickness                = geometry.thickness
            self._inner_boundary = self.RadialBoundary(
                primary_hex = Hexagon(inner_radius=primary_hex_inner_radius, orientation='y'),
                rotated_hex = Hexagon(inner_radius=rotated_hex_inner_radius, orientation='y')
            )
            self._outer_boundary = self.RadialBoundary(
                primary_hex = Hexagon(inner_radius=primary_hex_inner_radius + thickness, orientation='y'),
                rotated_hex = Hexagon(inner_radius=rotated_hex_inner_radius + thickness, orientation='y')
            )

            self._axial_bounds: Optional[Interval] = None

        @property
        def geometry(self) -> ShroudGeometry:
            return self._geometry

        @property
        def inner_boundary(self) -> RadialBoundary:
            return self._inner_boundary

        @property
        def outer_boundary(self) -> RadialBoundary:
            return self._outer_boundary

        @property
        def axial_bounds(self) -> Interval:
            assert self._axial_bounds is not None, "Shroud axial bounds have not been assigned."
            return self._axial_bounds

        def __getattr__(self, name: str) -> object:
            return getattr(object.__getattribute__(self, "_geometry"), name)

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, Reactor.Shroud) and
                    self.geometry == other.geometry and
                    self._axial_bounds == other._axial_bounds)

        def __hash__(self) -> int:
            return hash((self.geometry, self._axial_bounds))

        def intersects(self,
                       cell: Rectangle,
                       center: Tuple[float, float] = (0.0, 0.0),
                       axial_bounds: Optional[Interval] = None) -> bool:
            """Check whether a rectangular cell intersects the shroud shell.

            Parameters
            ----------
            cell : Rectangle
                Rectangular XY footprint to test.
            center : Tuple[float, float]
                ``(x, y)`` center of the cell footprint.
            axial_bounds : Optional[Interval]
                Optional lower and upper axial bounds (cm) for the cell. When
                provided, the interval must intersect ``self.axial_bounds``.

            Returns
            -------
            bool
                True if the cell is axially eligible, intersects both outer
                shroud hexagons, and is not fully inside both inner shroud hexagons.
            """
            if axial_bounds is not None and not self.axial_bounds.intersects(axial_bounds):
                return False

            intersects_outer = (
                self.outer_boundary.primary_hex.intersects(cell, other_center=center) and
                self.outer_boundary.rotated_hex.intersects(cell, other_center=center, self_rotation=30.0)
            )

            inside_inner = (
                self.inner_boundary.primary_hex.contains(cell, other_center=center) and
                self.inner_boundary.rotated_hex.contains(cell, other_center=center, self_rotation=30.0)
            )

            return intersects_outer and not inside_inner

        def contains(self,
                     cell: Rectangle,
                     center: Tuple[float, float] = (0.0, 0.0),
                     axial_bounds: Optional[Interval] = None) -> bool:
            """Check whether a rectangular cell is inside the inner shroud aperture.

            Parameters
            ----------
            cell : Rectangle
                Rectangular XY footprint to test.
            center : Tuple[float, float]
                ``(x, y)`` center of the cell footprint.
            axial_bounds : Optional[Interval]
                Optional lower and upper axial bounds (cm) for the cell. When
                provided, the interval must be fully contained in
                ``self.axial_bounds``.

            Returns
            -------
            bool
                True if the cell is axially inside the shroud and all cell
                corners are inside both inner shroud hexagons.
            """
            if axial_bounds is not None and not self.axial_bounds.contains(axial_bounds):
                return False

            return (
                self.inner_boundary.primary_hex.contains(cell, other_center=center) and
                self.inner_boundary.rotated_hex.contains(cell, other_center=center, self_rotation=30.0)
            )

    class RSRCavity:
        """Rotary specimen rack cavity geometry plus reactor-context bounds.

        Parameters
        ----------
        geometry : RSRCavityGeometry
            Rotary specimen rack cavity geometry.

        Attributes
        ----------
        geometry : RSRCavityGeometry
            Wrapped RSR cavity geometry.
        outer_boundary : Circle
            Circular RSR cavity radial boundary centered on the reactor origin.
        tube_centers : Tuple[Tuple[float, float], ...]
            XY centers of all RSR specimen tubes, ordered clockwise starting at
            the +y axis.
        tube_outer_boundary : Circle
            Circular radial boundary for a single specimen tube outer diameter.
        axial_bounds : Interval
            Lower and upper RSR cavity bounds (cm) relative to the core centerline.
        """
        def __init__(self, geometry: RSRCavityGeometry) -> None:
            self._geometry = geometry
            self._outer_boundary = Circle(geometry.outer_radius)
            self._tube_outer_boundary = Circle(geometry.tube_specs.outer_radius)
            d_theta = 360.0 / geometry.number_of_tubes
            self._tube_centers = tuple(
                (geometry.tube_to_center_distance * cos(radians(90.0 - i * d_theta)),
                 geometry.tube_to_center_distance * sin(radians(90.0 - i * d_theta)))
                for i in range(geometry.number_of_tubes)
            )
            self._axial_bounds: Optional[Interval] = None

        @property
        def geometry(self) -> RSRCavityGeometry:
            return self._geometry

        @property
        def outer_boundary(self) -> Circle:
            return self._outer_boundary

        @property
        def tube_centers(self) -> Tuple[Tuple[float, float], ...]:
            return self._tube_centers

        @property
        def tube_outer_boundary(self) -> Circle:
            return self._tube_outer_boundary

        @property
        def axial_bounds(self) -> Interval:
            assert self._axial_bounds is not None, "RSRCavity axial bounds have not been assigned."
            return self._axial_bounds

        def __getattr__(self, name: str) -> object:
            return getattr(object.__getattribute__(self, "_geometry"), name)

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, Reactor.RSRCavity) and
                    self.geometry == other.geometry and
                    self._axial_bounds == other._axial_bounds)

        def __hash__(self) -> int:
            return hash((self.geometry, self._axial_bounds))

    class BeamPort:
        """Beam port geometry plus placement metadata for the reactor.

        Parameters
        ----------
        geometry : BeamPortGeometry
            Beam port tube geometry definition.
        translation : Tuple[float, float, float]
            XYZ translation (cm) of the beam port centerline after rotation.
            Default: (0.0, 0.0, 0.0) - centered at the reactor core centerline.
        rotation : float
            Rotation angle (degrees) about the +z axis applied before translation.
            Default is 0.0 (aligned along the +x axis).

        Attributes
        ----------
        geometry : BeamPortGeometry
            Wrapped beam port tube geometry.
        rotation : float
            Rotation angle (degrees) about the +z axis.
        translation : Tuple[float, float, float]
            XYZ translation (cm) of the beam port centerline.
        exterior_bounding_box : Rectangle
            Rectangular XY footprint using the beam port length and outer diameter.
        interior_box : Rectangle
            Rectangular XY footprint using the beam port length and the side
            length of the largest square fully inscribed in the inner bore.
        axial_bounds : Interval
            Lower and upper beam port bounds (cm) derived from the z-translation
            and outer radius.
        interior_axial_bounds : Interval
            Lower and upper axial bounds (cm) for the inscribed-square interior
            profile, derived from the z-translation and inner radius.
        """

        def __init__(self,
                     geometry: BeamPortGeometry,
                     translation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                     rotation: float = 0.0) -> None:
            self._geometry = geometry
            self._rotation = rotation
            self._translation = translation
            self._exterior_bounding_box = Rectangle(geometry.length, geometry.outer_radius*2.0)
            interior_side = geometry.inner_radius * sqrt(2.0)
            interior_half_width = 0.5 * interior_side
            self._interior_box = Rectangle(geometry.length, interior_side)
            self._interior_axial_bounds = Interval(translation[2] - interior_half_width,
                                                   translation[2] + interior_half_width)
            self._axial_bounds = Interval(translation[2] - geometry.outer_radius,
                                          translation[2] + geometry.outer_radius)

        @property
        def geometry(self) -> BeamPortGeometry:
            return self._geometry

        @property
        def rotation(self) -> float:
            return self._rotation

        @property
        def translation(self) -> Tuple[float, float, float]:
            return self._translation

        @property
        def exterior_bounding_box(self) -> Rectangle:
            return self._exterior_bounding_box

        @property
        def interior_box(self) -> Rectangle:
            return self._interior_box

        @property
        def axial_bounds(self) -> Interval:
            assert self._axial_bounds is not None, "BeamPort axial bounds have not been assigned."
            return self._axial_bounds

        @property
        def interior_axial_bounds(self) -> Interval:
            return self._interior_axial_bounds

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, Reactor.BeamPort) and
                    self.geometry == other.geometry and
                    isclose(self.rotation, other.rotation, rel_tol=TOL) and
                    all(isclose(a, b, rel_tol=TOL) for a, b in zip(self.translation, other.translation)) and
                    self._axial_bounds == other._axial_bounds)

        def __hash__(self) -> int:
            rounded_trans = tuple(relative_round(x, TOL) for x in self.translation)
            return hash((self.geometry, relative_round(self.rotation, TOL), rounded_trans, self._axial_bounds))

        def intersects(self,
                       cell: Rectangle,
                       center: Tuple[float, float],
                       axial_bounds: Optional[Interval] = None) -> bool:
            """Check whether a rectangular cell intersects this beam port.

            Parameters
            ----------
            cell : Rectangle
                Rectangular XY footprint to test.
            center : Tuple[float, float]
                ``(x, y)`` center of the cell footprint.
            axial_bounds : Optional[Interval]
                Optional lower and upper axial bounds (cm) for the cell. When
                provided, the interval must intersect ``self.axial_bounds``.

            Returns
            -------
            bool
                True if the cell is axially eligible and intersects the beam
                port exterior XY bounding box after rotation and translation.
            """
            if axial_bounds is not None and not self.axial_bounds.intersects(axial_bounds):
                return False

            return bool(cell.intersects(self.exterior_bounding_box,
                                        self_center=center,
                                        other_center=(self.translation[0], self.translation[1]),
                                        other_rotation=self.rotation))

        def contains(self,
                     cell: Rectangle,
                     center: Tuple[float, float],
                     axial_bounds: Optional[Interval] = None) -> bool:
            """Check whether a rectangular cell is fully inside this beam port interior.

            Parameters
            ----------
            cell : Rectangle
                Rectangular XY footprint to test.
            center : Tuple[float, float]
                ``(x, y)`` center of the cell footprint.
            axial_bounds : Optional[Interval]
                Optional lower and upper axial bounds (cm) for the cell. When
                provided, the interval must be fully contained in
                ``self.interior_axial_bounds``.

            Returns
            -------
            bool
                True if the cell is axially inside the inscribed-square beam
                port interior and its XY footprint is fully contained by
                ``self.interior_box`` after rotation and translation.
            """
            if axial_bounds is not None and not self.interior_axial_bounds.contains(axial_bounds):
                return False

            return bool(self.interior_box.contains(cell,
                                                   self_center=(self.translation[0], self.translation[1]),
                                                   other_center=center,
                                                   self_rotation=self.rotation))


    class GridPlate:
        """Grid plate geometry plus reactor-context axial placement.

        Parameters
        ----------
        geometry : GridPlateGeometry
            Grid plate geometry definition.
        top_to_core_centerline_distance : float
            Axial distance (cm) from the core centerline to the plate's top surface.

        Attributes
        ----------
        geometry : GridPlateGeometry
            Wrapped grid plate geometry.
        top_to_core_centerline_distance : float
            Axial distance (cm) from the core centerline to the plate's top surface.
        axial_bounds : Interval
            Lower and upper grid plate bounds (cm) relative to the core centerline.
        """
        def __init__(self,
                     geometry: GridPlateGeometry,
                     top_to_core_centerline_distance: float) -> None:
            assert top_to_core_centerline_distance >= 0.0, "top_to_core_centerline_distance must be non-negative."
            self._geometry = geometry
            self._top_to_core_centerline_distance = top_to_core_centerline_distance
            self._axial_bounds: Optional[Interval] = None

        @property
        def geometry(self) -> GridPlateGeometry:
            return self._geometry

        @property
        def top_to_core_centerline_distance(self) -> float:
            return self._top_to_core_centerline_distance

        @property
        def axial_bounds(self) -> Interval:
            assert self._axial_bounds is not None, "GridPlate axial bounds have not been assigned."
            return self._axial_bounds

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, Reactor.GridPlate) and
                    self.geometry == other.geometry and
                    isclose(self.top_to_core_centerline_distance,
                            other.top_to_core_centerline_distance, rel_tol=TOL) and
                    self._axial_bounds == other._axial_bounds)

        def __hash__(self) -> int:
            return hash((self.geometry,
                         relative_round(self.top_to_core_centerline_distance, TOL),
                         self._axial_bounds))

    class Reflector:
        """Reflector canister geometry plus reactor-context placement.

        Parameters
        ----------
        geometry : ReflectorGeometry
            Reflector canister geometry definition.
        core_centerline_offset : float
            Axial offset (cm) of the reflector centerline from the core centerline.

        Attributes
        ----------
        geometry : ReflectorGeometry
            Wrapped reflector geometry.
        outer_boundary : Circle
            Circular reflector radial boundary centered on the reactor origin.
        core_centerline_offset : float
            Axial offset (cm) of the reflector centerline from the core centerline.
        axial_bounds : Interval
            Lower and upper reflector bounds (cm) relative to the core centerline.
        """
        def __init__(self,
                     geometry: ReflectorGeometry,
                     core_centerline_offset: float) -> None:
            self._geometry = geometry
            self._core_centerline_offset = core_centerline_offset
            self._outer_boundary = Circle(geometry.radius)
            reflector_half = 0.5 * geometry.height
            self._axial_bounds = Interval(core_centerline_offset - reflector_half,
                                          core_centerline_offset + reflector_half)

        @property
        def geometry(self) -> ReflectorGeometry:
            return self._geometry

        @property
        def outer_boundary(self) -> Circle:
            return self._outer_boundary

        @property
        def core_centerline_offset(self) -> float:
            return self._core_centerline_offset

        @property
        def axial_bounds(self) -> Interval:
            assert self._axial_bounds is not None, "Reflector axial bounds have not been assigned."
            return self._axial_bounds

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, Reactor.Reflector) and
                    self.geometry == other.geometry and
                    isclose(self.core_centerline_offset, other.core_centerline_offset, rel_tol=TOL) and
                    self._axial_bounds == other._axial_bounds)

        def __hash__(self) -> int:
            return hash((self.geometry, relative_round(self.core_centerline_offset, TOL), self._axial_bounds))

    @property
    def pool(self) -> Pool:
        return self._pool

    @property
    def reflector(self) -> Reflector:
        return self._reflector

    @property
    def shroud(self) -> Shroud:
        return self._shroud

    @property
    def beam_port(self) -> Dict[int, BeamPort]:
        return self._beam_port

    @property
    def rotary_specimen_rack_cavity(self) -> RSRCavity:
        return self._rotary_specimen_rack_cavity

    @property
    def core(self) -> CoreGeometry:
        return self._core

    @property
    def upper_grid_plate(self) -> GridPlate:
        return self._upper_grid_plate

    @property
    def lower_grid_plate(self) -> GridPlate:
        return self._lower_grid_plate

    @property
    def transient_rod_position(self) -> float:
        return self._transient_rod_position

    @transient_rod_position.setter
    def transient_rod_position(self, position: float) -> None:
        self._transient_rod_position = position

    @property
    def regulating_rod_position(self) -> float:
        return self._regulating_rod_position

    @regulating_rod_position.setter
    def regulating_rod_position(self, position: float) -> None:
        self._regulating_rod_position = position

    @property
    def shim_1_rod_position(self) -> float:
        return self._shim_1_rod_position

    @shim_1_rod_position.setter
    def shim_1_rod_position(self, position: float) -> None:
        self._shim_1_rod_position = position

    @property
    def shim_2_rod_position(self) -> float:
        return self._shim_2_rod_position

    @shim_2_rod_position.setter
    def shim_2_rod_position(self, position: float) -> None:
        self._shim_2_rod_position = position

    def __init__(self,
                 pool:                        PoolGeometry,
                 reflector:                   Reflector,
                 shroud:                      ShroudGeometry,
                 beam_port_1_5:               BeamPort,
                 beam_port_2:                 BeamPort,
                 beam_port_3:                 BeamPort,
                 beam_port_4:                 BeamPort,
                 rotary_specimen_rack_cavity: RSRCavityGeometry,
                 core:                        CoreGeometry,
                 upper_grid_plate:            GridPlate,
                 lower_grid_plate:            GridPlate,
                 transient_rod_position:      float,
                 regulating_rod_position:     float,
                 shim_1_rod_position:         float,
                 shim_2_rod_position:         float,
                 name:                        str = "reactor") -> None:

        upper_grid_plate_top    = upper_grid_plate.top_to_core_centerline_distance
        upper_grid_plate_bottom = upper_grid_plate_top - upper_grid_plate.geometry.thickness
        lower_grid_plate_top    = -lower_grid_plate.top_to_core_centerline_distance
        lower_grid_plate_bottom = lower_grid_plate_top - lower_grid_plate.geometry.thickness
        gap          = upper_grid_plate_bottom - lower_grid_plate_top
        assert gap > 0.0, "Grid plates must have a positive axial gap."
        assert upper_grid_plate_top > lower_grid_plate_bottom, "Upper grid plate must be above lower grid plate."

        shroud_bounds = reflector.axial_bounds
        rsr_bounds = Interval(reflector.axial_bounds.upper - rotary_specimen_rack_cavity.height,
                              reflector.axial_bounds.upper)
        super().__init__(name)
        self._pool                        = Reactor.Pool(pool)
        self._reflector                   = reflector
        self._shroud                      = Reactor.Shroud(shroud)
        self._beam_port                   = {1: beam_port_1_5, 2: beam_port_2, 3: beam_port_3, 4: beam_port_4,
                                             5: beam_port_1_5}
        self._rotary_specimen_rack_cavity = Reactor.RSRCavity(rotary_specimen_rack_cavity)
        self._core                        = core
        self._upper_grid_plate            = upper_grid_plate
        self._lower_grid_plate            = lower_grid_plate
        self.transient_rod_position       = transient_rod_position
        self.regulating_rod_position      = regulating_rod_position
        self.shim_1_rod_position          = shim_1_rod_position
        self.shim_2_rod_position          = shim_2_rod_position

        # Reactor fills bounds that depend on cross-component context.
        # pylint: disable=protected-access
        self.shroud._axial_bounds                      = shroud_bounds
        self.rotary_specimen_rack_cavity._axial_bounds = rsr_bounds
        self.upper_grid_plate._axial_bounds            = Interval(upper_grid_plate_bottom, upper_grid_plate_top)
        self.lower_grid_plate._axial_bounds            = Interval(lower_grid_plate_bottom, lower_grid_plate_top)
        # pylint: enable=protected-access

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, Reactor)
            and self.pool == other.pool
            and self.reflector == other.reflector
            and self.shroud == other.shroud
            and self.beam_port == other.beam_port
            and self.rotary_specimen_rack_cavity == other.rotary_specimen_rack_cavity
            and self.core == other.core
            and self.upper_grid_plate == other.upper_grid_plate
            and self.lower_grid_plate == other.lower_grid_plate
            and isclose(self.transient_rod_position, other.transient_rod_position, rel_tol=TOL)
            and isclose(self.regulating_rod_position, other.regulating_rod_position, rel_tol=TOL)
            and isclose(self.shim_1_rod_position, other.shim_1_rod_position, rel_tol=TOL)
            and isclose(self.shim_2_rod_position, other.shim_2_rod_position, rel_tol=TOL)
        )

    def __hash__(self) -> int:
        return hash((
            self.pool,
            self.reflector,
            self.shroud,
            tuple(sorted(self.beam_port.items())),
            self.rotary_specimen_rack_cavity,
            self.core,
            self.upper_grid_plate,
            self.lower_grid_plate,
            relative_round(self.transient_rod_position, TOL),
            relative_round(self.regulating_rod_position, TOL),
            relative_round(self.shim_1_rod_position, TOL),
            relative_round(self.shim_2_rod_position, TOL),
        ))

    def get_materials(self) -> List[Material]:
        """Return the unique materials used by the reactor geometry.

        Returns
        -------
        List[Material]
            Unique materials from the pool, reflector, shroud, RSR cavity, core,
            grid plates, and physical beam ports. Beam port IDs 1 and 5 share one
            instance, so only IDs 1 through 4 are collected.
        """
        materials: List[Material] = []
        materials.extend(self.pool.get_materials())
        materials.extend(self.reflector.geometry.get_materials())
        materials.extend(self.shroud.get_materials())
        materials.extend(self.rotary_specimen_rack_cavity.get_materials())
        materials.extend(self.core.get_materials())
        materials.extend(self.upper_grid_plate.geometry.get_materials())
        materials.extend(self.lower_grid_plate.geometry.get_materials())
        for beam_port_id in (1, 2, 3, 4):
            if self.beam_port[beam_port_id] is not None:
                materials.extend(self.beam_port[beam_port_id].geometry.get_materials())
        return unique_materials(materials)

    def get_element_bottom_axial_position(self,
                                          element: Optional[CoreGeometry.Element],
    ) -> float | None:
        """Return the bottom axial position for a core element.

        Built-in TRIGA fuel, graphite, central thimble, control rod, and source
        holder placements are returned relative to the reactor core centerline.
        Control rod locations use the reactor's current rod-position attributes.

        Parameters
        ----------
        element : Optional[CoreGeometry.Element]
            Core element whose bottom axial position is needed. ``None`` returns
            ``None``.

        Returns
        -------
        Optional[float]
            Bottom axial position (cm) relative to the core centerline, or ``None``
            if no element is provided or no special placement is required.
        """

        axial_position: float | None = None

        if isinstance(element, CentralThimbleGeometry):
            axial_position = -0.5 * element.length
        if isinstance(element, FuelElementGeometry):
            axial_position = (-0.5 * element.fuel_meat.length -
                              element.moly_disc.thickness -
                              element.lower_end_fitting.length -
                              element.lower_graphite_reflector.thickness)
        if isinstance(element, GraphiteElementGeometry):
            axial_position = (-0.5 * element.graphite_meat.length -
                              element.lower_end_fitting.length)
        if element is self.core.transient_rod:
            axial_position = self.transient_rod_position
        if element is self.core.regulating_rod:
            axial_position = self.regulating_rod_position
        if element is self.core.shim_1_rod:
            axial_position = self.shim_1_rod_position
        if element is self.core.shim_2_rod:
            axial_position = self.shim_2_rod_position
        if isinstance(element, SourceHolderGeometry):
            axial_position = self.upper_grid_plate.top_to_core_centerline_distance - \
                             element.length

        return axial_position

    def rsr_cavity_intersects(self,
                              cell: Rectangle,
                              center: Tuple[float, float] = (0.0, 0.0),
                              axial_bounds: Optional[Interval] = None) -> bool:
        """Check whether a rectangular cell intersects the RSR cavity region.

        Parameters
        ----------
        cell : Rectangle
            Rectangular XY footprint to test.
        center : Tuple[float, float]
            ``(x, y)`` center of the cell footprint.
        axial_bounds : Optional[Interval]
            Optional lower and upper axial bounds (cm) for the cell. When
            provided, the interval must intersect the RSR cavity axial bounds.

        Returns
        -------
        bool
            True if the cell is axially eligible, intersects the RSR radial
            boundary, and is outside the shroud shell and inner aperture.
        """
        rsr = self.rotary_specimen_rack_cavity
        if axial_bounds is not None and not axial_bounds.intersects(rsr.axial_bounds):
            return False
        return (cell.intersects(rsr.outer_boundary, center, (0.0, 0.0)) and
                not self.shroud.intersects(cell, center, axial_bounds) and
                not self.shroud.contains(cell, center))

    def rsr_cavity_contains(self,
                            cell: Rectangle,
                            center: Tuple[float, float] = (0.0, 0.0),
                            axial_bounds: Optional[Interval] = None) -> bool:
        """Check whether a rectangular cell is fully inside the RSR cavity fill region.

        Parameters
        ----------
        cell : Rectangle
            Rectangular XY footprint to test.
        center : Tuple[float, float]
            ``(x, y)`` center of the cell footprint.
        axial_bounds : Optional[Interval]
            Optional lower and upper axial bounds (cm) for the cell. When
            provided, the interval must be fully contained in the RSR cavity
            axial bounds.

        Returns
        -------
        bool
            True if the cell is axially inside the RSR cavity, fully contained
            by the RSR outer radial boundary, outside the shroud/core region,
            and does not intersect any RSR specimen tube.
        """
        rsr = self.rotary_specimen_rack_cavity
        if axial_bounds is not None and not rsr.axial_bounds.contains(axial_bounds):
            return False
        return (rsr.outer_boundary.contains(cell, other_center=center) and
                not self.shroud.intersects(cell, center, axial_bounds) and
                not self.shroud.contains(cell, center) and
                not self.rsr_tube_intersects(cell, center, axial_bounds))

    def rsr_tube_intersects(self,
                            cell: Rectangle,
                            center: Tuple[float, float] = (0.0, 0.0),
                            axial_bounds: Optional[Interval] = None) -> bool:
        """Check whether a rectangular cell intersects any RSR specimen tube.

        Parameters
        ----------
        cell : Rectangle
            Rectangular XY footprint to test.
        center : Tuple[float, float]
            ``(x, y)`` center of the cell footprint.
        axial_bounds : Optional[Interval]
            Optional lower and upper axial bounds (cm) for the cell. When
            provided, the interval must intersect the RSR cavity axial bounds.

        Returns
        -------
        bool
            True if the cell is axially eligible and intersects the outer circle
            of at least one RSR specimen tube.
        """
        rsr = self.rotary_specimen_rack_cavity
        if axial_bounds is not None and not axial_bounds.intersects(rsr.axial_bounds):
            return False
        return any(cell.intersects(rsr.tube_outer_boundary, center, tube_center)
                   for tube_center in rsr.tube_centers)


    def reflector_intersects(self,
                             cell: Rectangle,
                             center: Tuple[float, float] = (0.0, 0.0),
                             axial_bounds: Optional[Interval] = None) -> bool:
        """Check whether a rectangular cell intersects the reflector region.

        Parameters
        ----------
        cell : Rectangle
            Rectangular XY footprint to test.
        center : Tuple[float, float]
            ``(x, y)`` center of the cell footprint.
        axial_bounds : Optional[Interval]
            Optional lower and upper axial bounds (cm) for the cell. When
            provided, the interval must intersect the reflector axial bounds.

        Returns
        -------
        bool
            True if the cell is axially eligible, intersects the reflector radial
            boundary, and is outside the shroud and RSR regions.
        """
        if axial_bounds is not None and not axial_bounds.intersects(self.reflector.axial_bounds):
            return False
        return (cell.intersects(self.reflector.outer_boundary, center, (0.0, 0.0)) and
                not self.shroud.intersects(cell, center, axial_bounds) and
                not self.shroud.contains(cell, center) and
                not self.rsr_cavity_intersects(cell, center, axial_bounds))

    def reflector_contains(self,
                           cell: Rectangle,
                           center: Tuple[float, float] = (0.0, 0.0),
                           axial_bounds: Optional[Interval] = None) -> bool:
        """Check whether a rectangular cell is fully inside the reflector material region.

        Parameters
        ----------
        cell : Rectangle
            Rectangular XY footprint to test.
        center : Tuple[float, float]
            ``(x, y)`` center of the cell footprint.
        axial_bounds : Optional[Interval]
            Optional lower and upper axial bounds (cm) for the cell. When
            provided, the interval must be fully contained in the reflector
            axial bounds.

        Returns
        -------
        bool
            True if the cell is axially inside the reflector, fully contained by
            the reflector radial boundary, and does not intersect shroud, RSR,
            or beam port regions.
        """
        if axial_bounds is not None and not self.reflector.axial_bounds.contains(axial_bounds):
            return False
        return (self.reflector.outer_boundary.contains(cell, other_center=center) and
                not self.shroud.intersects(cell, center, axial_bounds) and
                not self.shroud.contains(cell, center) and
                not self.rsr_cavity_intersects(cell, center, axial_bounds) and
                not self.any_beamport_intersects(cell, center, axial_bounds))

    def any_beamport_intersects(self,
                                cell: Rectangle,
                                center: Tuple[float, float],
                                axial_bounds: Optional[Interval] = None) -> bool:
        """Check whether a rectangular cell intersects any physical beam port.

        Parameters
        ----------
        cell : Rectangle
            Rectangular XY footprint to test.
        center : Tuple[float, float]
            ``(x, y)`` center of the cell footprint.
        axial_bounds : Optional[Interval]
            Optional lower and upper axial bounds (cm) for the cell. When
            provided, the interval must intersect a beam port's axial bounds.

        Returns
        -------
        bool
            True if the cell intersects any of beam port IDs 1 through 4. Beam
            port ID 5 aliases ID 1 and is intentionally not checked separately.
        """
        return any(self.beam_port[bid].intersects(cell, center, axial_bounds)
                   for bid in (1, 2, 3, 4))

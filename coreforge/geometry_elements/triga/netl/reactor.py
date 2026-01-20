from __future__ import annotations

from typing import Dict, Optional, Tuple
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.triga.netl import (BeamPort as BeamPortGeometry, Core as CoreGeometry,
                                                    GridPlate as GridPlateGeometry, Pool as PoolGeometry,
                                                    Reflector as ReflectorGeometry, RSRCavity as RSRCavityGeometry,
                                                    Shroud as ShroudGeometry)
from coreforge.shapes import Circle, Rectangle
import coreforge.geometry_elements.triga as geometry_elements_triga
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


class Reactor(GeometryElement):
    """Top-level TRIGA NETL reactor geometry container with placement metadata.

    Notes
    -----
    The reactor's core axial centerline is taken as the origin for axial placements,
    meaning that the axial centerline of the fuel elements is at z = 0 cm.

    Parameters
    ----------
    pool : PoolGeometry
        Reactor pool geometry.
    reflector : Reactor.Reflector
        Graphite reflector canister and its core offset.
    shroud : ShroudGeometry
        Aluminum shroud surrounding the core/reflector region.
    beam_port_1_5 : Reactor.BeamPort
        Beam port located at 1/5 position with rotation/translation.
    beam_port_2 : Reactor.BeamPort
        Beam port 2 geometry with rotation/translation.
    beam_port_3 : Reactor.BeamPort
        Beam port 3 geometry with rotation/translation.
    beam_port_4 : Reactor.BeamPort
        Beam port 4 geometry with rotation/translation.
    rotary_specimen_rack_cavity : RSRCavityGeometry
        Rotary specimen rack cavity geometry.
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
    pool : PoolGeometry
        Reactor pool geometry.
    reflector : Reactor.Reflector
        Graphite reflector canister and its core offset.
    shroud : ShroudGeometry
        Aluminum shroud surrounding the core/reflector region.
    beam_port_1_5 : Reactor.BeamPort
        Beam port located at 1/5 position with rotation/translation.
    beam_port_2 : Reactor.BeamPort
        Beam port 2 geometry with rotation/translation.
    beam_port_3 : Reactor.BeamPort
        Beam port 3 geometry with rotation/translation.
    beam_port_4 : Reactor.BeamPort
        Beam port 4 geometry with rotation/translation.
    rotary_specimen_rack_cavity : RSRCavityGeometry
        Rotary specimen rack cavity geometry.
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
    name : str
        Name for this reactor element.
    pool_axial_bounds : Tuple[float, float]
        Lower and upper axial bounds (cm) for the pool.
    reflector_axial_bounds : Tuple[float, float]
        Lower and upper axial bounds (cm) for the reflector canister.
    shroud_axial_bounds : Tuple[float, float]
        Lower and upper axial bounds (cm) for the shroud region.
    rsr_axial_bounds : Tuple[float, float]
        Lower and upper axial bounds (cm) for the RSR cavity.
    beamport_axial_bounds : Dict[int, Tuple[float, float]]
        Mapping of beamport ID to its lower/upper axial bounds (cm).
    """

    class BeamPort:
        """Beam port geometry plus placement (rotation/translation) for the reactor.

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
        """
        def __init__(self,
                     geometry: BeamPortGeometry,
                     translation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                     rotation: float = 0.0) -> None:
            self._geometry = geometry
            self._rotation = rotation
            self._translation = translation

        @property
        def geometry(self) -> BeamPortGeometry:
            return self._geometry

        @property
        def rotation(self) -> float:
            return self._rotation

        @property
        def translation(self) -> Tuple[float, float, float]:
            return self._translation

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (
                isinstance(other, Reactor.BeamPort) and
                self.geometry == other.geometry and
                isclose(self.rotation, other.rotation, rel_tol=TOL) and
                all(isclose(a, b, rel_tol=TOL) for a, b in zip(self.translation, other.translation))
            )

        def __hash__(self) -> int:
            rounded_trans = tuple(relative_round(x, TOL) for x in self.translation)
            return hash((self.geometry, relative_round(self.rotation, TOL), rounded_trans))

    class GridPlate:
        """Grid plate geometry plus axial offset from the core centerline.

        Parameters
        ----------
        geometry : GridPlateGeometry
            Grid plate geometry definition.
        top_to_core_centerline_distance : float
            Axial distance (cm) from the core centerline to the plate's top surface.
        """
        def __init__(self, geometry: GridPlateGeometry, top_to_core_centerline_distance: float) -> None:
            assert top_to_core_centerline_distance >= 0.0, "top_to_core_centerline_distance must be non-negative."
            self._geometry = geometry
            self._top_to_core_centerline_distance = top_to_core_centerline_distance

        @property
        def geometry(self) -> GridPlateGeometry:
            return self._geometry

        @property
        def top_to_core_centerline_distance(self) -> float:
            return self._top_to_core_centerline_distance

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (
                isinstance(other, Reactor.GridPlate) and
                self.geometry == other.geometry and
                isclose(self.top_to_core_centerline_distance, other.top_to_core_centerline_distance, rel_tol=TOL)
            )

        def __hash__(self) -> int:
            return hash((self.geometry, relative_round(self.top_to_core_centerline_distance, TOL)))

    class Reflector:
        """Reflector canister geometry plus its offset from the core centerline.

        Parameters
        ----------
        geometry : ReflectorGeometry
            Reflector canister geometry definition.
        core_centerline_offset : float
            Axial offset (cm) of the reflector centerline from the core centerline.
        """
        def __init__(self, geometry: ReflectorGeometry, core_centerline_offset: float) -> None:
            self._geometry = geometry
            self._core_centerline_offset = core_centerline_offset

        @property
        def geometry(self) -> ReflectorGeometry:
            return self._geometry

        @property
        def core_centerline_offset(self) -> float:
            return self._core_centerline_offset

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (
                isinstance(other, Reactor.Reflector) and
                self.geometry == other.geometry and
                isclose(self.core_centerline_offset, other.core_centerline_offset, rel_tol=TOL)
            )

        def __hash__(self) -> int:
            return hash((self.geometry, relative_round(self.core_centerline_offset, TOL)))

    @property
    def pool(self) -> PoolGeometry:
        return self._pool

    @property
    def reflector(self) -> Reflector:
        return self._reflector

    @property
    def shroud(self) -> ShroudGeometry:
        return self._shroud

    @property
    def beam_port_1_5(self) -> BeamPort:
        return self._beam_port_1_5

    @property
    def beam_port_2(self) -> BeamPort:
        return self._beam_port_2

    @property
    def beam_port_3(self) -> BeamPort:
        return self._beam_port_3

    @property
    def beam_port_4(self) -> BeamPort:
        return self._beam_port_4

    @property
    def rotary_specimen_rack_cavity(self) -> RSRCavityGeometry:
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

    @property
    def pool_axial_bounds(self) -> Tuple[float, float]:
        return self._pool_axial_bounds

    @property
    def reflector_axial_bounds(self) -> Tuple[float, float]:
        return self._reflector_axial_bounds

    @property
    def shroud_axial_bounds(self) -> Tuple[float, float]:
        return self._shroud_axial_bounds

    @property
    def rsr_axial_bounds(self) -> Tuple[float, float]:
        return self._rsr_axial_bounds

    @property
    def beamport_axial_bounds(self) -> Dict[int, Tuple[float, float]]:
        return self._beamport_axial_bounds

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

        upper_top    = upper_grid_plate.top_to_core_centerline_distance
        upper_bottom = upper_top - upper_grid_plate.geometry.thickness
        lower_top    = -lower_grid_plate.top_to_core_centerline_distance
        lower_bottom = lower_top - lower_grid_plate.geometry.thickness
        gap          = upper_bottom - lower_top
        assert gap > 0.0, "Grid plates must have a positive axial gap."
        assert upper_top > lower_bottom, "Upper grid plate must be above lower grid plate."

        super().__init__(name)
        self._pool                        = pool
        self._reflector                   = reflector
        self._shroud                      = shroud
        self._beam_port_1_5               = beam_port_1_5
        self._beam_port_2                 = beam_port_2
        self._beam_port_3                 = beam_port_3
        self._beam_port_4                 = beam_port_4
        self._rotary_specimen_rack_cavity = rotary_specimen_rack_cavity
        self._core                        = core
        self._upper_grid_plate            = upper_grid_plate
        self._lower_grid_plate            = lower_grid_plate
        self.transient_rod_position       = transient_rod_position
        self.regulating_rod_position      = regulating_rod_position
        self.shim_1_rod_position          = shim_1_rod_position
        self.shim_2_rod_position          = shim_2_rod_position

        self._pool_axial_bounds      = (-0.5 * self.pool.height,
                                        0.5 * self.pool.height)
        reflector_center             = self.reflector.core_centerline_offset
        reflector_half               = 0.5 * self.reflector.geometry.height
        self._reflector_axial_bounds = (reflector_center - reflector_half,
                                        reflector_center + reflector_half)
        self._shroud_axial_bounds    = self._reflector_axial_bounds
        reflector_top                = self._reflector_axial_bounds[1]
        self._rsr_axial_bounds       = (reflector_top - self.rotary_specimen_rack_cavity.height,
                                        reflector_top)

        def beamport_bounds(beamport: Reactor.BeamPort) -> Tuple[float, float]:
            z_center = beamport.translation[2]
            radius = beamport.geometry.outer_radius
            return (z_center - radius, z_center + radius)

        self._beamport_axial_bounds = {
            1: beamport_bounds(self.beam_port_1_5),
            2: beamport_bounds(self.beam_port_2),
            3: beamport_bounds(self.beam_port_3),
            4: beamport_bounds(self.beam_port_4),
            5: beamport_bounds(self.beam_port_1_5),
        }

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, Reactor)
            and self.pool == other.pool
            and self.reflector == other.reflector
            and self.shroud == other.shroud
            and self.beam_port_1_5 == other.beam_port_1_5
            and self.beam_port_2 == other.beam_port_2
            and self.beam_port_3 == other.beam_port_3
            and self.beam_port_4 == other.beam_port_4
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
            self.beam_port_1_5,
            self.beam_port_2,
            self.beam_port_3,
            self.beam_port_4,
            self.rotary_specimen_rack_cavity,
            self.core,
            self.upper_grid_plate,
            self.lower_grid_plate,
            relative_round(self.transient_rod_position, TOL),
            relative_round(self.regulating_rod_position, TOL),
            relative_round(self.shim_1_rod_position, TOL),
            relative_round(self.shim_2_rod_position, TOL),
        ))


    def get_element_bottom_axial_position(self,
                                          element: Optional[CoreGeometry.Element],
    ) -> float | None:
        """Return the bottom axial position for a core element.

        Parameters
        ----------
        element : Optional[CoreGeometry.Element]
            The core element whose bottom axial position is needed.

        Returns
        -------
        Optional[float]
            Bottom axial position (cm) relative to the core centerline, or ``None``
            if no element is provided or no special placement is required.
        """

        if element is None:
            return None

        if isinstance(element, geometry_elements_triga_netl.CentralThimble):
            return -0.5 * element.length
        if isinstance(element, geometry_elements_triga.FuelElement):
            return (-0.5 * element.fuel_meat.length -
                    element.moly_disc.thickness -
                    element.lower_end_fitting.length -
                    element.lower_graphite_reflector.thickness)
        if isinstance(element, geometry_elements_triga.GraphiteElement):
            return (-0.5 * element.graphite_meat.length -
                    element.lower_end_fitting.length)
        if element is self.core.transient_rod:
            return self.transient_rod_position
        if element is self.core.regulating_rod:
            return self.regulating_rod_position
        if element is self.core.shim_1_rod:
            return self.shim_1_rod_position
        if element is self.core.shim_2_rod:
            return self.shim_2_rod_position
        if isinstance(element, geometry_elements_triga_netl.SourceHolder):
            return self.upper_grid_plate.top_to_core_centerline_distance - element.length

        raise ValueError(f"Unsupported core element type: {type(element).__name__}")

    def _axial_bounds_intersect(self,
                                bounds_a: Tuple[float, float],
                                bounds_b: Tuple[float, float]) -> bool:
        """Check whether two axial bounds overlap.

        Parameters
        ----------
        bounds_a : Tuple[float, float]
            Lower and upper axial bounds (cm).
        bounds_b : Tuple[float, float]
            Lower and upper axial bounds (cm).

        Returns
        -------
        bool
            True if the bounds overlap.
        """
        if bounds_a[1] < bounds_b[0] and not isclose(bounds_a[1], bounds_b[0], rel_tol=TOL):
            return False
        if bounds_b[1] < bounds_a[0] and not isclose(bounds_b[1], bounds_a[0], rel_tol=TOL):
            return False
        return True

    def _axial_bounds_contain(self,
                              outer_bounds: Tuple[float, float],
                              inner_bounds: Tuple[float, float]) -> bool:
        """Check whether one axial interval is fully inside another.

        Parameters
        ----------
        outer_bounds : Tuple[float, float]
            Lower and upper axial bounds (cm) for the outer interval.
        inner_bounds : Tuple[float, float]
            Lower and upper axial bounds (cm) for the inner interval.

        Returns
        -------
        bool
            True if the inner interval lies inside the outer interval.
        """
        lower_ok = (inner_bounds[0] > outer_bounds[0] or
                    isclose(inner_bounds[0], outer_bounds[0], rel_tol=TOL))
        upper_ok = (inner_bounds[1] < outer_bounds[1] or
                    isclose(inner_bounds[1], outer_bounds[1], rel_tol=TOL))
        return lower_ok and upper_ok

    def shroud_intersects(self,
                          cell: Rectangle,
                          center: Tuple[float, float] = (0.0, 0.0),
                          axial_bounds: Optional[Tuple[float, float]] = None) -> bool:
        """Check whether a cell intersects the shroud radial region.

        Parameters
        ----------
        cell : Rectangle
            Rectangle representing the cell footprint.
        center : Tuple[float, float]
            (x, y) center of the cell.

        axial_bounds : Optional[Tuple[float, float]]
            Lower and upper axial bounds (cm) for the cell.

        Returns
        -------
        bool
            True if the cell intersects the shroud region.
        """
        if axial_bounds is not None and not self._axial_bounds_intersect(axial_bounds, self.shroud_axial_bounds):
            return False
        inner_radius = min(self.shroud.primary_hex_inner_radius,
                           self.shroud.rotated_hex_inner_radius)
        outer_radius = min(self.shroud.primary_hex_inner_radius + self.shroud.thickness,
                           self.shroud.rotated_hex_inner_radius + self.shroud.thickness)
        inner = Circle(inner_radius)
        outer = Circle(outer_radius)

        intersects_outer = cell.intersects(outer, center, (0.0, 0.0))
        intersects_inner = cell.intersects(inner, center, (0.0, 0.0))
        if intersects_outer and not intersects_inner:
            return True
        return False

    def shroud_inner_contains(self,
                              cell: Rectangle,
                              center: Tuple[float, float] = (0.0, 0.0)) -> bool:
        """Check whether a cell is fully inside the inner shroud radius.

        Parameters
        ----------
        cell : Rectangle
            Rectangle representing the cell footprint.
        center : Tuple[float, float]
            (x, y) center of the cell.

        Returns
        -------
        bool
            True if the cell is fully inside the inner shroud circle.
        """
        inner_radius = min(self.shroud.primary_hex_inner_radius,
                           self.shroud.rotated_hex_inner_radius)
        circle = Circle(inner_radius)
        half_w = 0.5 * cell.w
        half_h = 0.5 * cell.h
        corners = [(center[0] - half_w, center[1] - half_h),
                   (center[0] + half_w, center[1] - half_h),
                   (center[0] - half_w, center[1] + half_h),
                   (center[0] + half_w, center[1] + half_h)]
        return all(circle.contains_point(corner) for corner in corners)

    def pool_intersects(self,
                        cell: Rectangle,
                        center: Tuple[float, float] = (0.0, 0.0),
                        axial_bounds: Optional[Tuple[float, float]] = None) -> bool:
        """Check whether a cell intersects the pool boundary.

        Parameters
        ----------
        cell : Rectangle
            Rectangle representing the cell footprint.
        center : Tuple[float, float]
            (x, y) center of the cell.

        axial_bounds : Optional[Tuple[float, float]]
            Lower and upper axial bounds (cm) for the cell.

        Returns
        -------
        bool
            True if any part of the cell is outside the pool boundary.
        """
        return not self.pool_contains(cell, center, axial_bounds)


    def pool_contains(self,
                      cell: Rectangle,
                      center: Tuple[float, float] = (0.0, 0.0),
                      axial_bounds: Optional[Tuple[float, float]] = None) -> bool:
        """Check whether a cell is fully inside the pool boundary.

        Parameters
        ----------
        cell : Rectangle
            Rectangle representing the cell footprint.
        center : Tuple[float, float]
            (x, y) center of the cell.

        axial_bounds : Optional[Tuple[float, float]]
            Lower and upper axial bounds (cm) for the cell.

        Returns
        -------
        bool
            True if the cell is fully inside the pool boundary.
        """
        if axial_bounds is not None and not self._axial_bounds_contain(self.pool_axial_bounds, axial_bounds):
            return False
        pool_circle = Circle(self.pool.radius)
        half_w = 0.5 * cell.w
        half_h = 0.5 * cell.h
        corners = [(center[0] - half_w, center[1] - half_h),
                   (center[0] + half_w, center[1] - half_h),
                   (center[0] - half_w, center[1] + half_h),
                   (center[0] + half_w, center[1] + half_h)]
        return all(pool_circle.contains_point(corner) for corner in corners)

    def rsr_intersects(self,
                       cell: Rectangle,
                       center: Tuple[float, float] = (0.0, 0.0),
                       axial_bounds: Optional[Tuple[float, float]] = None) -> bool:
        """Check whether a cell intersects the RSR cavity radial region.

        Parameters
        ----------
        cell : Rectangle
            Rectangle representing the cell footprint.
        center : Tuple[float, float]
            (x, y) center of the cell.

        axial_bounds : Optional[Tuple[float, float]]
            Lower and upper axial bounds (cm) for the cell.

        Returns
        -------
        bool
            True if the cell intersects the RSR cavity radius.
        """
        if axial_bounds is not None and not self._axial_bounds_intersect(axial_bounds, self.rsr_axial_bounds):
            return False
        rsr_circle = Circle(self.rotary_specimen_rack_cavity.outer_radius)
        return bool(cell.intersects(rsr_circle, center, (0.0, 0.0)))

    def reflector_intersects(self,
                             cell: Rectangle,
                             center: Tuple[float, float] = (0.0, 0.0),
                             axial_bounds: Optional[Tuple[float, float]] = None) -> bool:
        """Check whether a cell intersects the reflector radial region.

        Parameters
        ----------
        cell : Rectangle
            Rectangle representing the cell footprint.
        center : Tuple[float, float]
            (x, y) center of the cell.

        axial_bounds : Optional[Tuple[float, float]]
            Lower and upper axial bounds (cm) for the cell.

        Returns
        -------
        bool
            True if the cell intersects the reflector radius.
        """
        if axial_bounds is not None and not self._axial_bounds_intersect(axial_bounds,
                                                                        self.reflector_axial_bounds):
            return False
        reflector_circle = Circle(self.reflector.geometry.radius)
        return bool(cell.intersects(reflector_circle, center, (0.0, 0.0)))

    def beamport_intersects(self,
                            cell: Rectangle,
                            center: Tuple[float, float],
                            beamport_id: int,
                            axial_bounds: Optional[Tuple[float, float]] = None) -> bool:
        """Check whether a cell intersects a beam port radial region.

        Parameters
        ----------
        cell : Rectangle
            Rectangle representing the cell footprint.
        center : Tuple[float, float]
            (x, y) center of the cell.
        beamport_id : int
            Beam port identifier (1, 2, 3, 4, or 5). Beam ports 1 and 5 map to
            the same beam port geometry.

        axial_bounds : Optional[Tuple[float, float]]
            Lower and upper axial bounds (cm) for the cell.

        Returns
        -------
        bool
            True if the cell intersects the beam port rectangle.
        """
        beamport = self._beamport_geometry(beamport_id)
        if axial_bounds is not None and not self._axial_bounds_intersect(
            axial_bounds, self.beamport_axial_bounds[beamport_id]
        ):
            return False
        beam_rect = Rectangle(beamport.geometry.length,
                              beamport.geometry.outer_radius*2.0)
        beam_center = (beamport.translation[0], beamport.translation[1])
        beam_rotation = beamport.rotation

        half_w = 0.5 * cell.w
        half_h = 0.5 * cell.h
        cell_corners = [(center[0] - half_w, center[1] - half_h),
                        (center[0] + half_w, center[1] - half_h),
                        (center[0] - half_w, center[1] + half_h),
                        (center[0] + half_w, center[1] + half_h)]
        if any(beam_rect.contains_point(corner, beam_center, beam_rotation)
               for corner in cell_corners):
            return True
        return False


    def _beamport_geometry(self, beamport_id: int) -> BeamPort:
        """Return beam port geometry for the given beam port ID.

        Parameters
        ----------
        beamport_id : int
            Beam port identifier (1, 2, 3, 4, or 5). Beam ports 1 and 5 map to
            the same beam port geometry.

        Returns
        -------
        Reactor.BeamPort
            The beam port geometry corresponding to the ID.
        """
        if beamport_id not in {1, 2, 3, 4, 5}:
            raise ValueError(f"Invalid beamport_id: {beamport_id}")
        if beamport_id in {1, 5}:
            return self.beam_port_1_5
        return {2: self.beam_port_2,
                3: self.beam_port_3,
                4: self.beam_port_4}[beamport_id]


    def any_beamport_intersects(self,
                                cell: Rectangle,
                                center: Tuple[float, float],
                                axial_bounds: Optional[Tuple[float, float]] = None) -> bool:
        """Check whether a cell intersects any beam port radial region.

        Parameters
        ----------
        cell : Rectangle
            Rectangle representing the cell footprint.
        center : Tuple[float, float]
            (x, y) center of the cell.

        axial_bounds : Optional[Tuple[float, float]]
            Lower and upper axial bounds (cm) for the cell.

        Returns
        -------
        bool
            True if the cell intersects any beam port radius.
        """
        return any(self.beamport_intersects(cell, center, beamport_id, axial_bounds)
                   for beamport_id in (1, 2, 3, 4))

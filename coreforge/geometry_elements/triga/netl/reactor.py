from __future__ import annotations

from typing import Tuple
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.triga.netl import (
    BeamPort               as BeamPortGeometry,
    Core                   as CoreGeometry,
    GridPlate              as GridPlateGeometry,
    Pool                   as PoolGeometry,
    Reflector              as ReflectorGeometry,
    RSRCavity              as RSRCavityGeometry,
    Shroud                 as ShroudGeometry,
)


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
    """

    class BeamPort:
        """Beam port geometry plus placement (rotation/translation) for the reactor.

        Parameters
        ----------
        geometry : BeamPortGeometry
            Beam port tube geometry definition.
        translation : tuple of float
            XYZ translation (cm) of the beam port centerline after rotation.
            Default: (0.0, 0.0, 0.0) - centered at the reactor core centerline.
        rotation : tuple of tuple of float
            3x3 rotation matrix applied before translation.
            Default alignment is along the y-axis ((0.0, 90.0, 90.0),
                                                   (90.0, 0.0, 90.0),
                                                   (90.0, 90.0, 0.0)).
        """
        def __init__(self,
                     geometry: BeamPortGeometry,
                     translation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                     rotation: Tuple[Tuple[float, float, float],
                                     Tuple[float, float, float],
                                     Tuple[float, float, float]] =
                                     ((0.0, 90.0, 90.0),
                                      (90.0, 0.0, 90.0),
                                      (90.0, 90.0, 0.0))) -> None:
            self._geometry = geometry
            self._rotation = rotation
            self._translation = translation

        @property
        def geometry(self) -> BeamPortGeometry:
            return self._geometry

        @property
        def rotation(self) -> Tuple[Tuple[float, float, float],
                                    Tuple[float, float, float],
                                    Tuple[float, float, float]]:
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
                all(isclose(a, b, rel_tol=TOL) for row_a, row_b in zip(self.rotation, other.rotation) for a, b in zip(row_a, row_b)) and
                all(isclose(a, b, rel_tol=TOL) for a, b in zip(self.translation, other.translation))
            )

        def __hash__(self) -> int:
            rounded_rot = tuple(tuple(relative_round(x, TOL) for x in row) for row in self.rotation)
            rounded_trans = tuple(relative_round(x, TOL) for x in self.translation)
            return hash((self.geometry, rounded_rot, rounded_trans))

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

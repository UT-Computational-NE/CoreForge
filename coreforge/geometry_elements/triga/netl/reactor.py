from __future__ import annotations

from abc import ABC
from typing import Tuple, TypeAlias
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.triga.netl import (
    BeamPort               as BeamPortGeometry,
    Core                   as CoreGeometry,
    FuelFollowerControlRod as FuelFollowerControlRodGeometry,
    GridPlate              as GridPlateGeometry,
    Pool                   as PoolGeometry,
    Reflector              as ReflectorGeometry,
    RSRCavity              as RSRCavityGeometry,
    Shroud                 as ShroudGeometry,
    TransientRod           as TransientRodGeometry,
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
    transient_rod : Reactor.TransientRod
        Transient rod geometry with mutable axial position.
    regulating_rod : Reactor.FuelFollowerControlRod
        Regulating rod geometry with mutable axial position.
    shim_1_rod : Reactor.FuelFollowerControlRod
        Shim 1 rod geometry with mutable axial position.
    shim_2_rod : Reactor.FuelFollowerControlRod
        Shim 2 rod geometry with mutable axial position.
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
            Default: (0.0, 0.0, 0.0)
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
        distance_from_core_centerline : float
            Axial distance (cm) from the core centerline to the plate's core-facing surface.
        """
        def __init__(self, geometry: GridPlateGeometry, distance_from_core_centerline: float) -> None:
            self._geometry = geometry
            self._distance_from_core_centerline = distance_from_core_centerline

        @property
        def geometry(self) -> GridPlateGeometry:
            return self._geometry

        @property
        def distance_from_core_centerline(self) -> float:
            return self._distance_from_core_centerline

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (
                isinstance(other, Reactor.GridPlate) and
                self.geometry == other.geometry and
                isclose(self.distance_from_core_centerline, other.distance_from_core_centerline, rel_tol=TOL)
            )

        def __hash__(self) -> int:
            return hash((self.geometry, relative_round(self.distance_from_core_centerline, TOL)))

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

    class ControlRod(ABC):
        """Abstract control rod placement with mutable axial position.

        Parameters
        ----------
        geometry : FuelFollowerControlRod or TransientRod
            Underlying control rod geometry.
        bottom_z : float
            Axial position (cm) of the rod bottom.
        """

        ControlRodGeometry: TypeAlias = FuelFollowerControlRodGeometry | TransientRodGeometry

        def __init(self, geometry: ControlRodGeometry, bottom_z: float) -> None:
            self._geometry = geometry
            self._bottom_z = bottom_z

        @property
        def bottom_z(self) -> float:
            return self._bottom_z

        @bottom_z.setter
        def bottom_z(self, value: float) -> None:
            self._bottom_z = value

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (
                isinstance(other, Reactor.ControlRod) and
                type(self) is type(other) and
                self.geometry == other.geometry and
                isclose(self.bottom_z, other.bottom_z, rel_tol=TOL)
            )

        def __hash__(self) -> int:
            return hash((self.geometry, relative_round(self.bottom_z, TOL)))

    class FuelFollowerControlRod(ControlRod):
        """Fuel follower control rod placement.

        Parameters
        ----------
        geometry : FuelFollowerControlRod
            Fuel follower control rod geometry definition.
        bottom_z : float
            Axial position (cm) of the rod bottom.
        """

        @property
        def geometry(self) -> FuelFollowerControlRodGeometry:
            return self._geometry

        def __init__(self, geometry: FuelFollowerControlRodGeometry, bottom_z: float) -> None:
            assert isinstance(geometry, FuelFollowerControlRodGeometry)
            super().__init(geometry, bottom_z)

    class TransientRod(ControlRod):
        """Transient rod placement.

        Parameters
        ----------
        geometry : TransientRod
            Transient control rod geometry definition.
        bottom_z : float
            Axial position (cm) of the rod bottom.
        """

        @property
        def geometry(self) -> TransientRodGeometry:
            return self._geometry

        def __init__(self, geometry: TransientRodGeometry, bottom_z: float) -> None:
            assert isinstance(geometry, TransientRodGeometry)
            super().__init__(geometry, bottom_z)

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
    def transient_rod(self) -> TransientRod:
        return self._transient_rod

    @property
    def regulating_rod(self) -> FuelFollowerControlRod:
        return self._regulating_rod

    @property
    def shim_1_rod(self) -> FuelFollowerControlRod:
        return self._shim_1_rod

    @property
    def shim_2_rod(self) -> FuelFollowerControlRod:
        return self._shim_2_rod

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
                 transient_rod:               TransientRod,
                 regulating_rod:              FuelFollowerControlRod,
                 shim_1_rod:                  FuelFollowerControlRod,
                 shim_2_rod:                  FuelFollowerControlRod,
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
        self._transient_rod               = transient_rod
        self._regulating_rod              = regulating_rod
        self._shim_1_rod                  = shim_1_rod
        self._shim_2_rod                  = shim_2_rod

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
            and self.transient_rod == other.transient_rod
            and self.regulating_rod == other.regulating_rod
            and self.shim_1_rod == other.shim_1_rod
            and self.shim_2_rod == other.shim_2_rod
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
            self.transient_rod,
            self.regulating_rod,
            self.shim_1_rod,
            self.shim_2_rod,
        ))

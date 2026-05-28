from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from math import isclose
from typing import List, Optional, Union

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Air, B4C, Material, SS304, UZrH, Water, Zr, unique_materials
from coreforge.shapes.utils import equal_volume_ring_radii


# pylint: disable=too-many-public-methods
class FuelFollowerControlRod(GeometryElement):
    """TRIGA NETL fuel-follower control rod definitions and pincell builders.

    Parameters
    ----------
    cladding : FuelFollowerControlRod.Cladding
        Cladding definition with thickness, outer radius, and material.
    absorber : FuelFollowerControlRod.Absorber
        Absorber definition with radius and material.
    fuel_follower : FuelFollowerControlRod.FuelFollower
        Fuel follower definition with inner/outer radii and material.
    zr_fill_rod : FuelFollowerControlRod.ZrFillRod
        Zr fill rod definition with radius and material.
    upper_element_plug : FuelFollowerControlRod.ElementPlug
        Upper element plug specification (axial metadata).
    upper_air_gap : FuelFollowerControlRod.AirGap
        Air gap above the upper Magneform fitting (axial metadata).
    upper_magneform_fitting : FuelFollowerControlRod.MagneformFitting
        Upper Magneform fitting specification (axial metadata).
    above_absorber_air_gap : FuelFollowerControlRod.AirGap
        Air gap above the absorber (axial metadata).
    middle_magneform_fitting : FuelFollowerControlRod.MagneformFitting
        Middle Magneform fitting specification (axial metadata).
    above_fuel_follower_air_gap : FuelFollowerControlRod.AirGap
        Air gap above the fuel follower (axial metadata).
    lower_magneform_fitting : FuelFollowerControlRod.MagneformFitting
        Lower Magneform fitting specification (axial metadata).
    lower_air_gap : FuelFollowerControlRod.AirGap
        Air gap below the lower element plug (axial metadata).
    lower_element_plug : FuelFollowerControlRod.ElementPlug
        Lower element plug specification (axial metadata).
    fill_gas : Material, optional
        Gap fill material (defaults to ``Air``).
    outer_material : Material, optional
        Exterior/coolant material (defaults to ``Water``).
    gap_tolerance : float, optional
        Minimum zone thickness to retain; thinner gaps are removed. Defaults to 1E-8.
    name : str, optional
        Name for this control rod.

    Attributes
    ----------
    length : float
        Length of the fuel-follower control rod [cm].
    cladding : FuelFollowerControlRod.Cladding
        Cladding specification.
    absorber : FuelFollowerControlRod.Absorber
        Absorber specification.
    fuel_follower : FuelFollowerControlRod.FuelFollower
        Fuel follower specification.
    zr_fill_rod : FuelFollowerControlRod.ZrFillRod
        Zirconium fill rod specification.
    upper_element_plug : FuelFollowerControlRod.ElementPlug
        Upper element plug specification.
    upper_air_gap : FuelFollowerControlRod.AirGap
        Air gap above the upper Magneform fitting.
    upper_magneform_fitting : FuelFollowerControlRod.MagneformFitting
        Upper Magneform fitting specification.
    above_absorber_air_gap : FuelFollowerControlRod.AirGap
        Air gap above the absorber.
    middle_magneform_fitting : FuelFollowerControlRod.MagneformFitting
        Middle Magneform fitting specification.
    above_fuel_follower_air_gap : FuelFollowerControlRod.AirGap
        Air gap above the fuel follower.
    lower_magneform_fitting : FuelFollowerControlRod.MagneformFitting
        Lower Magneform fitting specification.
    lower_air_gap : FuelFollowerControlRod.AirGap
        Air gap below the lower element plug.
    lower_element_plug : FuelFollowerControlRod.ElementPlug
        Lower element plug specification.
    fill_gas : Material
        Gap fill material.
    outer_material : Material
        Exterior/coolant material.
    gap_tolerance : float, optional
        Minimum zone thickness to retain.
    absorber_pincell : CylindricalPinCell
        Pincell representing the absorber region.
    fuel_follower_pincell : CylindricalPinCell
        Pincell representing the fuel-follower region.
    air_gap_pincell : CylindricalPinCell
        Pincell representing axial air gaps (shared geometry).
    upper_element_plug_pincell : CylindricalPinCell
        Pincell for the upper element plug.
    lower_element_plug_pincell : CylindricalPinCell
        Pincell for the lower element plug.
    upper_magneform_fitting_pincell : CylindricalPinCell
        Pincell for the upper Magneform fitting.
    middle_magneform_fitting_pincell : CylindricalPinCell
        Pincell for the middle Magneform fitting.
    lower_magneform_fitting_pincell : CylindricalPinCell
        Pincell for the lower Magneform fitting.
    """

    @dataclass(frozen=True)
    class Cladding:
        """Control-rod cladding specification.

        Parameters
        ----------
        thickness : float
            Cladding thickness [cm].
        outer_radius : float
            Cladding outer radius [cm].
        material : Material, optional
            Cladding material (defaults to ``SS304``).
        """
        thickness: float
        outer_radius: float
        inner_radius: float = field(init=False)
        material: Material = field(default_factory=SS304)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Cladding thickness must be positive."
            assert self.outer_radius > self.thickness, (
                "Cladding outer radius must exceed thickness."
            )
            object.__setattr__(self, "inner_radius", self.outer_radius - self.thickness)

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelFollowerControlRod.Cladding) and
                    isclose(self.thickness, other.thickness, rel_tol=TOL) and
                    isclose(self.outer_radius, other.outer_radius, rel_tol=TOL) and
                    isclose(self.inner_radius, other.inner_radius, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.thickness, TOL),
                         relative_round(self.outer_radius, TOL),
                         relative_round(self.inner_radius, TOL),
                         self.material))

    @dataclass(frozen=True)
    class Absorber:
        """Absorber specification.

        Parameters
        ----------
        radius : float
            Radius of the absorber [cm].
        length : float
            Length of the absorber [cm].
        material : Material, optional
            Absorber material. Defaults to ``B4C``.
        """
        radius: float
        length: float
        material: Material = field(default_factory=B4C)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Absorber radius must be positive."
            assert self.length > 0.0, "Absorber length must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelFollowerControlRod.Absorber) and
                    isclose(self.radius, other.radius, rel_tol=TOL) and
                    isclose(self.length, other.length, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.radius, TOL),
                         relative_round(self.length, TOL),
                         self.material))

    class FuelFollower:
        """Fuel follower specification.

        Parameters
        ----------
        length : float
            Length of the fuel follower [cm].
        inner_radius : float
            Inner radius of the fuel follower [cm].
        outer_radius : float
            Outer radius of the fuel follower [cm].
        material : Material or Sequence[Material], optional
            User-facing fuel material specification for this fuel follower. Pass a
            single ``Material`` for homogeneous fuel, or pass one material per
            region for regioned fuel. Regioned material sequences use axial-major
            order: top-to-bottom axial levels, with radial regions ordered
            inner-to-outer within each axial level. Defaults to ``UZrH``.
        num_radial_regions : int
            Number of equal-volume radial fuel material regions. Defaults to 1.
        num_axial_regions : int
            Number of equal-length axial fuel material regions. Defaults to 1.
        material_regions : List[Material]
            Normalized material-region list in axial-major order. Use this in
            geometry builders, meshing code, and any logic that needs explicit
            per-region materials; its length is always
            ``num_axial_regions * num_radial_regions``.
        """

        @property
        def length(self) -> float:
            return self._length

        @property
        def inner_radius(self) -> float:
            return self._inner_radius

        @property
        def outer_radius(self) -> float:
            return self._outer_radius

        @property
        def material(self) -> Union[Material, List[Material]]:
            if len(self._material_regions) == 1:
                return self._material_regions[0]
            return list(self._material_regions)

        @property
        def material_regions(self) -> List[Material]:
            return list(self._material_regions)

        @property
        def num_radial_regions(self) -> int:
            return self._num_radial_regions

        @property
        def num_axial_regions(self) -> int:
            return self._num_axial_regions

        def __init__(self,
                     length: float,
                     inner_radius: float,
                     outer_radius: float,
                     material: Optional[Union[Material, Sequence[Material]]] = None,
                     num_radial_regions: int = 1,
                     num_axial_regions: int = 1):
            assert length > 0.0, "Fuel follower length must be positive."
            assert inner_radius > 0.0, "Fuel follower inner radius must be positive."
            assert outer_radius > inner_radius, "Fuel follower outer radius must exceed inner radius."
            assert num_radial_regions > 0, "Fuel follower num_radial_regions must be positive."
            assert num_axial_regions > 0, "Fuel follower num_axial_regions must be positive."

            self._length             = length
            self._inner_radius       = inner_radius
            self._outer_radius       = outer_radius
            self._num_radial_regions = num_radial_regions
            self._num_axial_regions  = num_axial_regions

            material = material if material is not None else UZrH()
            num_material_regions = num_axial_regions * num_radial_regions
            if isinstance(material, Material):
                material = [material for _ in range(num_material_regions)]
            else:
                assert len(material) == num_material_regions, (
                    f"Fuel follower material sequence length must equal "
                    f"num_axial_regions * num_radial_regions ({num_material_regions}); "
                    f"got {len(material)}."
                )
            self._material_regions = list(material)

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelFollowerControlRod.FuelFollower) and
                    isclose(self.length, other.length, rel_tol=TOL) and
                    isclose(self.inner_radius, other.inner_radius, rel_tol=TOL) and
                    isclose(self.outer_radius, other.outer_radius, rel_tol=TOL) and
                    self.num_radial_regions == other.num_radial_regions and
                    self.num_axial_regions == other.num_axial_regions and
                    self._material_regions == other._material_regions)

        def __hash__(self) -> int:
            return hash((relative_round(self.length, TOL),
                         relative_round(self.inner_radius, TOL),
                         relative_round(self.outer_radius, TOL),
                         self.num_radial_regions,
                         self.num_axial_regions,
                         tuple(self._material_regions)))

    @dataclass(frozen=True)
    class ZrFillRod:
        """Zr fill rod specification inside the fuel follower.

        Parameters
        ----------
        radius : float
            Radius of the Zr fill rod [cm].
        material : Material, optional
            Fill-rod material (defaults to ``Zr``).
        """
        radius: float
        material: Material = field(default_factory=Zr)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Zr Fill Rod radius must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelFollowerControlRod.ZrFillRod) and
                    isclose(self.radius, other.radius, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.radius, TOL), self.material))

    @dataclass(frozen=True)
    class ElementPlug:
        """Element plug specification (axial metadata only).

        Parameters
        ----------
        thickness : float
            Axial thickness of the plug [cm].
        material : Material, optional
            Plug material (defaults to ``SS304``).
        """
        thickness: float
        material: Material = field(default_factory=SS304)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Element Plug thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelFollowerControlRod.ElementPlug) and
                    isclose(self.thickness, other.thickness, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.thickness, TOL), self.material))

    @dataclass(frozen=True)
    class MagneformFitting:
        """Magneform fitting specification (axial metadata only).

        Parameters
        ----------
        thickness : float
            Axial thickness of the fitting [cm].
        material : Material, optional
            Fitting material (defaults to ``SS304``).
        """
        thickness: float
        material: Material = field(default_factory=SS304)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Magneform Fitting thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelFollowerControlRod.MagneformFitting) and
                    isclose(self.thickness, other.thickness, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.thickness, TOL), self.material))

    @dataclass(frozen=True)
    class AirGap:
        """Axial air gap specification (thickness metadata).

        Parameters
        ----------
        thickness : float
            Axial thickness of the air gap [cm].
        """
        thickness: float

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Air gap thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelFollowerControlRod.AirGap) and
                    isclose(self.thickness, other.thickness, rel_tol=TOL))

        def __hash__(self) -> int:
            return hash(relative_round(self.thickness, TOL))

    @property
    def length(self) -> float:
        return self._length

    @property
    def cladding(self) -> Cladding:
        return self._cladding

    @property
    def absorber(self) -> Absorber:
        return self._absorber

    @property
    def fuel_follower(self) -> FuelFollower:
        return self._fuel_follower

    @property
    def zr_fill_rod(self) -> ZrFillRod:
        return self._zr_fill_rod

    @property
    def upper_element_plug(self) -> ElementPlug:
        return self._upper_element_plug

    @property
    def upper_air_gap(self) -> AirGap:
        return self._upper_air_gap

    @property
    def upper_magneform_fitting(self) -> MagneformFitting:
        return self._upper_magneform_fitting

    @property
    def above_absorber_air_gap(self) -> AirGap:
        return self._above_absorber_air_gap

    @property
    def middle_magneform_fitting(self) -> MagneformFitting:
        return self._middle_magneform_fitting

    @property
    def above_fuel_follower_air_gap(self) -> AirGap:
        return self._above_fuel_follower_air_gap

    @property
    def lower_magneform_fitting(self) -> MagneformFitting:
        return self._lower_magneform_fitting

    @property
    def lower_air_gap(self) -> AirGap:
        return self._lower_air_gap

    @property
    def lower_element_plug(self) -> ElementPlug:
        return self._lower_element_plug

    @property
    def fill_gas(self) -> Material:
        return self._fill_gas

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @property
    def gap_tolerance(self) -> Optional[float]:
        return self._gap_tolerance

    @property
    def absorber_pincell(self) -> CylindricalPinCell:
        return self._absorber_pincell

    @property
    def fuel_follower_pincell(self) -> CylindricalPinCell:
        assert len(self._fuel_follower_pincells) == 1, (
            "FuelFollowerControlRod.fuel_follower_pincell is only available for "
            "fuel followers with one axial region. Use "
            "FuelFollowerControlRod.fuel_follower_pincells for regioned fuel."
        )
        return self._fuel_follower_pincells[0]

    @property
    def fuel_follower_pincells(self) -> List[CylindricalPinCell]:
        return list(self._fuel_follower_pincells)

    @property
    def air_gap_pincell(self) -> CylindricalPinCell:
        return self._air_gap_pincell

    @property
    def upper_element_plug_pincell(self) -> CylindricalPinCell:
        return self._upper_element_plug_pincell

    @property
    def lower_element_plug_pincell(self) -> CylindricalPinCell:
        return self._lower_element_plug_pincell

    @property
    def upper_magneform_fitting_pincell(self) -> CylindricalPinCell:
        return self._upper_magneform_fitting_pincell

    @property
    def middle_magneform_fitting_pincell(self) -> CylindricalPinCell:
        return self._middle_magneform_fitting_pincell

    @property
    def lower_magneform_fitting_pincell(self) -> CylindricalPinCell:
        return self._lower_magneform_fitting_pincell

    def __init__(self,
                 cladding:                    Cladding,
                 absorber:                    Absorber,
                 fuel_follower:               FuelFollower,
                 zr_fill_rod:                 ZrFillRod,
                 upper_element_plug:          ElementPlug,
                 upper_air_gap:               AirGap,
                 upper_magneform_fitting:     MagneformFitting,
                 above_absorber_air_gap:      AirGap,
                 middle_magneform_fitting:    MagneformFitting,
                 above_fuel_follower_air_gap: AirGap,
                 lower_magneform_fitting:     MagneformFitting,
                 lower_air_gap:               AirGap,
                 lower_element_plug:          ElementPlug,
                 fill_gas:                    Optional[Material] = None,
                 outer_material:              Optional[Material] = None,
                 gap_tolerance:               Optional[float] = 1e-8,
                 name:                        str = "fuel_follower_control_rod"):
        super().__init__(name)
        self._cladding = cladding
        self._absorber = absorber
        self._fuel_follower = fuel_follower
        self._zr_fill_rod = zr_fill_rod
        self._upper_element_plug = upper_element_plug
        self._upper_air_gap = upper_air_gap
        self._upper_magneform_fitting = upper_magneform_fitting
        self._above_absorber_air_gap = above_absorber_air_gap
        self._middle_magneform_fitting = middle_magneform_fitting
        self._above_fuel_follower_air_gap = above_fuel_follower_air_gap
        self._lower_magneform_fitting = lower_magneform_fitting
        self._lower_air_gap = lower_air_gap
        self._lower_element_plug = lower_element_plug
        self._fill_gas = fill_gas or Air()
        self._outer_material = outer_material or Water()
        self._gap_tolerance = gap_tolerance

        self._length = (self.lower_element_plug.thickness +
                        self.lower_air_gap.thickness +
                        self.lower_magneform_fitting.thickness +
                        self.fuel_follower.length +
                        self.above_fuel_follower_air_gap.thickness +
                        self.middle_magneform_fitting.thickness +
                        self.absorber.length +
                        self.above_absorber_air_gap.thickness +
                        self.upper_magneform_fitting.thickness +
                        self.upper_air_gap.thickness +
                        self.upper_element_plug.thickness)

        self._absorber_pincell = self.build_absorber_pincell(
            cladding=self.cladding,
            absorber=self.absorber,
            fill_gas=self.fill_gas,
            outer_material=self.outer_material,
            gap_tolerance=self.gap_tolerance,
            name=self.name + "_absorber_pincell",
        )
        self._fuel_follower_pincells = self.build_fuel_follower_pincells(
            cladding=self.cladding,
            fuel_follower=self.fuel_follower,
            zr_fill_rod=self.zr_fill_rod,
            fill_gas=self.fill_gas,
            outer_material=self.outer_material,
            gap_tolerance=self.gap_tolerance,
            name=self.name + "_fuel_follower_pincell",
        )
        self._upper_element_plug_pincell = self.build_element_plug_pincell(
            cladding=self.cladding,
            plug=self.upper_element_plug,
            outer_material=self.outer_material,
            name=self.name + "_upper_element_plug_pincell",
        )
        self._lower_element_plug_pincell = self.build_element_plug_pincell(
            cladding=self.cladding,
            plug=self.lower_element_plug,
            outer_material=self.outer_material,
            name=self.name + "_lower_element_plug_pincell",
        )
        self._upper_magneform_fitting_pincell = self.build_magneform_fitting_pincell(
            cladding=self.cladding,
            fitting=self.upper_magneform_fitting,
            outer_material=self.outer_material,
            name=self.name + "_upper_magneform_fitting_pincell",
        )
        self._middle_magneform_fitting_pincell = self.build_magneform_fitting_pincell(
            cladding=self.cladding,
            fitting=self.middle_magneform_fitting,
            outer_material=self.outer_material,
            name=self.name + "_middle_magneform_fitting_pincell",
        )
        self._lower_magneform_fitting_pincell = self.build_magneform_fitting_pincell(
            cladding=self.cladding,
            fitting=self.lower_magneform_fitting,
            outer_material=self.outer_material,
            name=self.name + "_lower_magneform_fitting_pincell",
        )
        self._air_gap_pincell = self.build_air_gap_pincell(
            cladding=self.cladding,
            fill_gas=self.fill_gas,
            outer_material=self.outer_material,
            name=self.name + "_air_gap_pincell",
        )

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, FuelFollowerControlRod):
            return False
        return (
            self.cladding == other.cladding and
            self.absorber == other.absorber and
            self.fuel_follower == other.fuel_follower and
            self.zr_fill_rod == other.zr_fill_rod and
            self.upper_element_plug == other.upper_element_plug and
            self.upper_air_gap == other.upper_air_gap and
            self.upper_magneform_fitting == other.upper_magneform_fitting and
            self.above_absorber_air_gap == other.above_absorber_air_gap and
            self.middle_magneform_fitting == other.middle_magneform_fitting and
            self.above_fuel_follower_air_gap == other.above_fuel_follower_air_gap and
            self.lower_magneform_fitting == other.lower_magneform_fitting and
            self.lower_air_gap == other.lower_air_gap and
            self.lower_element_plug == other.lower_element_plug and
            self.fill_gas == other.fill_gas and
            self.outer_material == other.outer_material and
            ((self.gap_tolerance is None and other.gap_tolerance is None) or
             (self.gap_tolerance is not None and other.gap_tolerance is not None and
              isclose(self.gap_tolerance, other.gap_tolerance, rel_tol=TOL)))
        )

    def __hash__(self) -> int:
        return hash((
            self.cladding,
            self.absorber,
            self.fuel_follower,
            self.zr_fill_rod,
            self.upper_element_plug,
            self.upper_air_gap,
            self.upper_magneform_fitting,
            self.above_absorber_air_gap,
            self.middle_magneform_fitting,
            self.above_fuel_follower_air_gap,
            self.lower_magneform_fitting,
            self.lower_air_gap,
            self.lower_element_plug,
            self.fill_gas,
            self.outer_material,
            None if self.gap_tolerance is None else relative_round(self.gap_tolerance, TOL),
        ))

    def get_materials(self) -> List[Material]:
        materials = [
            self.cladding.material,
            self.absorber.material,
            *self.fuel_follower.material_regions,
            self.zr_fill_rod.material,
            self.upper_element_plug.material,
            self.lower_element_plug.material,
            self.upper_magneform_fitting.material,
            self.middle_magneform_fitting.material,
            self.lower_magneform_fitting.material,
            self.fill_gas,
            self.outer_material,
        ]
        return unique_materials(materials)

    def as_stack(self, bottom_pos: float = 0.0) -> Stack:
        """ A method for getting a copy of the Fuel Follower Control Rod as a Stack

        Parameters
        ----------
        bottom_pos : float
            The axial position of the bottom of the stack (cm)

        Returns
        -------
        Stack
            The Fuel Follower Control Rod as a Stack
        """

        fuel_region_thickness = self.fuel_follower.length / self.fuel_follower.num_axial_regions
        fuel_segments = [Stack.Segment(pincell, fuel_region_thickness)
                         for pincell in reversed(self.fuel_follower_pincells)]

        return Stack( name       = self.name,
                      bottom_pos = bottom_pos,
                      segments   = [
            Stack.Segment(self.lower_element_plug_pincell, self.lower_element_plug.thickness),
            Stack.Segment(self.air_gap_pincell, self.lower_air_gap.thickness),
            Stack.Segment(self.lower_magneform_fitting_pincell, self.lower_magneform_fitting.thickness),
            *fuel_segments,
            Stack.Segment(self.air_gap_pincell, self.above_fuel_follower_air_gap.thickness),
            Stack.Segment(self.middle_magneform_fitting_pincell, self.middle_magneform_fitting.thickness),
            Stack.Segment(self.absorber_pincell, self.absorber.length),
            Stack.Segment(self.air_gap_pincell, self.above_absorber_air_gap.thickness),
            Stack.Segment(self.upper_magneform_fitting_pincell, self.upper_magneform_fitting.thickness),
            Stack.Segment(self.air_gap_pincell, self.upper_air_gap.thickness),
            Stack.Segment(self.upper_element_plug_pincell, self.upper_element_plug.thickness)
            ],
        )

    @staticmethod
    def build_absorber_pincell(cladding:       Cladding,
                               absorber:       Absorber,
                               fill_gas:       Optional[Material] = None,
                               outer_material: Optional[Material] = None,
                               gap_tolerance:  Optional[float] = None,
                               name:           str = "fuel_follower_control_rod_absorber") -> CylindricalPinCell:
        """Build a pincell for the absorber region with concentric cladding.

        Parameters
        ----------
        cladding : FuelFollowerControlRod.Cladding
            Cladding definition with inner/outer radii and material.
        absorber : FuelFollowerControlRod.Absorber
            Absorber definition with radius and material.
        fill_gas : Material, optional
            Gap fill material between absorber and cladding (defaults to ``Air``).
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        gap_tolerance : float, optional
            Minimum zone thickness to retain (defaults to ``None`` for no filtering).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the absorber stack.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()

        radii = [absorber.radius, cladding.inner_radius, cladding.outer_radius]
        materials = [absorber.material, fill_gas, cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance or 0.0)

    @staticmethod
    def build_fuel_follower_pincell(cladding:       Cladding,
                                    fuel_follower:  FuelFollower,
                                    zr_fill_rod:    ZrFillRod,
                                    fill_gas:       Optional[Material] = None,
                                    outer_material: Optional[Material] = None,
                                    gap_tolerance:  Optional[float] = None,
                                    name:           str = "fuel_follower_control_rod_follower",
                                    axial_level:    int = 0) -> CylindricalPinCell:
        """Build a pincell for the fuel-follower region with Zr fill rod.

        Parameters
        ----------
        cladding : FuelFollowerControlRod.Cladding
            Cladding definition with inner/outer radii and material.
        fuel_follower : FuelFollowerControlRod.FuelFollower
            Fuel follower definition with inner/outer radii and material.
        zr_fill_rod : FuelFollowerControlRod.ZrFillRod
            Zr fill rod definition.
        fill_gas : Material, optional
            Gap fill material between Zr rod and follower, and follower and cladding (defaults to ``Air``).
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        gap_tolerance : float, optional
            Minimum zone thickness to retain (defaults to ``None`` for no filtering).
        name : str, optional
            Name for the pincell.
        axial_level : int, optional
            Fuel follower axial level to build, indexed from top to bottom. Defaults to 0.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the follower stack.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()
        assert 0 <= axial_level < fuel_follower.num_axial_regions, (
            f"axial_level = {axial_level}, "
            f"fuel_follower.num_axial_regions = {fuel_follower.num_axial_regions}"
        )

        fuel_radii = equal_volume_ring_radii(
            inner_radius = fuel_follower.inner_radius,
            outer_radius = fuel_follower.outer_radius,
            num_regions  = fuel_follower.num_radial_regions,
        )
        material_start = axial_level * fuel_follower.num_radial_regions
        material_stop  = material_start + fuel_follower.num_radial_regions
        fuel_materials = fuel_follower.material_regions[material_start:material_stop]

        radii = [
            zr_fill_rod.radius,
            fuel_follower.inner_radius,
            *fuel_radii,
            cladding.inner_radius,
            cladding.outer_radius,
        ]
        materials = [
            zr_fill_rod.material,
            fill_gas,
            *fuel_materials,
            fill_gas,
            cladding.material,
            outer_material,
        ]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance or 0.0)

    @staticmethod
    def build_fuel_follower_pincells(cladding:       Cladding,
                                     fuel_follower:  FuelFollower,
                                     zr_fill_rod:    ZrFillRod,
                                     fill_gas:       Optional[Material] = None,
                                     outer_material: Optional[Material] = None,
                                     gap_tolerance:  Optional[float] = None,
                                     name:           str = "fuel_follower_control_rod_follower") -> List[CylindricalPinCell]:
        """Build fuel follower pincells for each axial material level.

        Parameters
        ----------
        cladding : FuelFollowerControlRod.Cladding
            Cladding definition with inner/outer radii and material.
        fuel_follower : FuelFollowerControlRod.FuelFollower
            Fuel follower definition with inner/outer radii, region counts, and
            material region specification.
        zr_fill_rod : FuelFollowerControlRod.ZrFillRod
            Zr fill rod definition.
        fill_gas : Material, optional
            Gap fill material between Zr rod and follower, and follower and cladding.
            Defaults to ``Air``.
        outer_material : Material, optional
            Exterior/coolant material; defaults to ``Water``.
        gap_tolerance : float, optional
            Minimum zone thickness to retain (defaults to ``None`` for no filtering).
        name : str, optional
            Base name for the pincells. For multiple axial regions, the axial
            level index is appended to this name.

        Returns
        -------
        List[CylindricalPinCell]
            Fuel follower pincells ordered from top to bottom, matching
            ``FuelFollower.material_regions`` axial-major ordering.
        """
        pincells = []
        for axial_level in range(fuel_follower.num_axial_regions):
            pincell_name = name
            if fuel_follower.num_axial_regions > 1:
                pincell_name = f"{name}_axial_{axial_level}"
            pincells.append(FuelFollowerControlRod.build_fuel_follower_pincell(
                cladding       = cladding,
                fuel_follower  = fuel_follower,
                zr_fill_rod    = zr_fill_rod,
                fill_gas       = fill_gas,
                outer_material = outer_material,
                gap_tolerance  = gap_tolerance,
                name           = pincell_name,
                axial_level    = axial_level,
            ))
        return pincells

    @staticmethod
    def build_element_plug_pincell(cladding:       Cladding,
                                   plug:           ElementPlug,
                                   outer_material: Optional[Material] = None,
                                   name:           str = "fuel_follower_control_rod_plug") -> CylindricalPinCell:
        """Build a pincell for plug regions (solid inside cladding).

        Parameters
        ----------
        cladding : FuelFollowerControlRod.Cladding
            Cladding definition with inner/outer radii and material.
        plug : FuelFollowerControlRod.ElementPlug
            Plug material and axial metadata.
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the plug region.
        """
        outer_material = outer_material or Water()
        radii = [cladding.inner_radius, cladding.outer_radius]
        materials = [plug.material, cladding.material, outer_material]
        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=None)

    @staticmethod
    def build_magneform_fitting_pincell(cladding:       Cladding,
                                        fitting:        MagneformFitting,
                                        outer_material: Optional[Material] = None,
                                        name:           str = "fuel_follower_control_rod_magneform") -> CylindricalPinCell:
        """Build a pincell for Magneform fitting regions (solid inside cladding).

        Parameters
        ----------
        cladding : FuelFollowerControlRod.Cladding
            Cladding definition with inner/outer radii and material.
        fitting : FuelFollowerControlRod.MagneformFitting
            Fitting material and axial metadata.
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the Magneform fitting region.
        """
        outer_material = outer_material or Water()
        radii = [cladding.inner_radius, cladding.outer_radius]
        materials = [fitting.material, cladding.material, outer_material]
        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=None)

    @staticmethod
    def build_air_gap_pincell(cladding:       Cladding,
                              fill_gas:       Optional[Material] = None,
                              outer_material: Optional[Material] = None,
                              name:           str = "fuel_follower_control_rod_air_gap") -> CylindricalPinCell:
        """Build a pincell for air-gap regions (uses fill_gas core).

        Parameters
        ----------
        cladding : FuelFollowerControlRod.Cladding
            Cladding definition with inner/outer radii and material.
        fill_gas : Material, optional
            Air-gap material (defaults to ``Air``).
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing an air-gap region.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()
        radii = [cladding.inner_radius, cladding.outer_radius]
        materials = [fill_gas, cladding.material, outer_material]
        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=None)

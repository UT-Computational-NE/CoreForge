from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Air, Graphite, Material, Mo, SS304, UZrH, Water, Zr


class FuelElement(GeometryElement):
    """TRIGA fuel element definitions and pincell builder.

    Parameters
    ----------
    cladding : FuelElement.Cladding
        Cladding definition with thickness, outer radius, and material.
    fill_gas : Optional[Material]
        Gas filling any radial gaps (between Zr rod and fuel meat, or meat and cladding).
        Defaults to ``Air``.
    outer_material : Optional[Material]
        Exterior/coolant material surrounding the cladding.
        Defaults to ``Water``.
    upper_end_fitting : FuelElement.EndFitting
        Upper end fitting geometry and material (cone approximation).
    upper_air_gap : FuelElement.AirGap
        Axial air gap above the upper graphite reflector.
    upper_graphite_reflector : FuelElement.GraphiteReflector
        Upper graphite reflector geometry and material.
    zr_fill_rod : FuelElement.ZrFillRod
        Zirconium fill rod geometry and material.
    fuel_meat : FuelElement.FuelMeat
        Fuel meat geometry (inner/outer radii, length) and material.
    moly_disc : FuelElement.MolyDisc
        Molybdenum disc geometry and material.
    lower_graphite_reflector : FuelElement.GraphiteReflector
        Lower graphite reflector geometry and material.
    lower_end_fitting : FuelElement.EndFitting
        Lower end fitting geometry and material (cone approximation).
    gap_tolerance : float, optional
        Minimum thickness to retain a radial gap; thinner gaps are removed. Defaults to 1e-8.


    Attributes
    ----------
    cladding : FuelElement.Cladding
        Cladding specification.
    fill_gas : Material
        Gas filling any radial gaps.
    outer_material : Material
        Exterior/coolant material.
    upper_end_fitting : FuelElement.EndFitting
        Upper end fitting specification.
    upper_air_gap : FuelElement.AirGap
        Axial air gap above the upper graphite reflector.
    upper_graphite_reflector : FuelElement.GraphiteReflector
        Upper graphite reflector specification.
    zr_fill_rod : FuelElement.ZrFillRod
        Zirconium fill rod specification.
    fuel_meat : FuelElement.FuelMeat
        Fuel meat specification.
    moly_disc : FuelElement.MolyDisc
        Molybdenum disc specification.
    lower_graphite_reflector : FuelElement.GraphiteReflector
        Lower graphite reflector specification.
    lower_end_fitting : FuelElement.EndFitting
        Lower end fitting specification.
    interior_length : float
        Axial length from the bottom of the lower graphite reflector to the top
        of the upper air gap.
    length : float
        Total axial length including upper and lower end fittings.
    gap_tolerance : float, optional
        Minimum thickness to retain a radial gap (defaults to 1e-8).
    fuel_pincell : CylindricalPinCell
        Pincell representing the fuel meat radial region.
    moly_disc_pincell : CylindricalPinCell
        Pincell representing the molybdenum disc region.
    upper_reflector_pincell : CylindricalPinCell
        Pincell representing the upper graphite reflector region.
    lower_reflector_pincell : CylindricalPinCell
        Pincell representing the lower graphite reflector region.
    air_gap_pincell : CylindricalPinCell
        Pincell representing the upper air gap region.

    References
    ----------
    .. [1] D. R. Redhouse, et al., "Radiation Characterization Summary: NETL Beam Port
           1/5 Free-Field Environment at the 128-inch Core Centerline Adjacent Location,
           (NETL-FF-BP1/5-128-cca).", Nov. 2022. https://doi.org/10.2172/1898256
    """

    @dataclass(frozen=True)
    class ZrFillRod:
        """Zirconium fill rod specification.

        Attributes
        ----------
        radius : float
            Radius of the Zr fill rod [cm].
        material : Material
            Rod material (defaults to ``Zr``).
        """
        radius: float
        material: Material = field(default_factory=Zr)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Zr Fill Rod radius must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelElement.ZrFillRod) and
                    isclose(self.radius, other.radius, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.radius, TOL), self.material))

    @dataclass(frozen=True)
    class FuelMeat:
        """Fuel meat specification.

        Attributes
        ----------
        inner_radius : float
            Inner radius of the fuel meat [cm].
        outer_radius : float
            Outer radius of the fuel meat [cm].
        length : float
            Axial length of the fuel meat [cm].
        material : Material
            Fuel material (defaults to ``UZrH``).
        """
        inner_radius: float
        outer_radius: float
        length: float
        material: Material = field(default_factory=UZrH)

        def __post_init__(self) -> None:
            assert self.inner_radius > 0.0, "Fuel Meat inner radius must be positive."
            assert self.outer_radius > self.inner_radius, (
                "Fuel Meat outer radius must exceed inner radius."
            )
            assert self.length > 0.0, "Fuel Meat length must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelElement.FuelMeat) and
                    isclose(self.inner_radius, other.inner_radius, rel_tol=TOL) and
                    isclose(self.outer_radius, other.outer_radius, rel_tol=TOL) and
                    isclose(self.length, other.length, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.inner_radius, TOL),
                         relative_round(self.outer_radius, TOL),
                         relative_round(self.length, TOL),
                         self.material))

    @dataclass(frozen=True)
    class Cladding:
        """Cladding specification.

        Attributes
        ----------
        thickness : float
            Cladding thickness [cm].
        outer_radius : float
            Cladding outer radius [cm].
        inner_radius : float
            Derived inner radius (outer minus thickness) [cm].
        material : Material
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
            return (isinstance(other, FuelElement.Cladding) and
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
    class GraphiteReflector:
        """Graphite reflector specification.

        Attributes
        ----------
        radius : float
            Reflector radius [cm].
        thickness : float
            Axial thickness of the reflector [cm].
        material : Material
            Reflector material Defaults to ``Graphite`` at 1.6 g/cc (Ref. [1]_ pg. 50).
        """
        radius: float
        thickness: float
        material: Material = field(default_factory=lambda: Graphite(graphite_density=1.6))

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Graphite Reflector radius must be positive."
            assert self.thickness > 0.0, "Graphite Reflector thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelElement.GraphiteReflector) and
                    isclose(self.radius, other.radius, rel_tol=TOL) and
                    isclose(self.thickness, other.thickness, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.radius, TOL),
                         relative_round(self.thickness, TOL),
                         self.material))

    @dataclass(frozen=True)
    class MolyDisc:
        """Molybdenum disc specification.

        Attributes
        ----------
        radius : float
            Disc radius [cm].
        thickness : float
            Disc thickness [cm].
        material : Material
            Disc material (defaults to ``Mo``).
        """
        radius: float
        thickness: float
        material: Material = field(default_factory=Mo)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Moly Disc radius must be positive."
            assert self.thickness > 0.0, "Moly Disc thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelElement.MolyDisc) and
                    isclose(self.radius, other.radius, rel_tol=TOL) and
                    isclose(self.thickness, other.thickness, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.radius, TOL),
                         relative_round(self.thickness, TOL),
                         self.material))

    @dataclass(frozen=True)
    class AirGap:
        """Axial air gap specification above the upper reflector.

        Attributes
        ----------
        thickness : float
            Gap thickness [cm].
        """
        thickness: float

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Air Gap thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelElement.AirGap) and
                    isclose(self.thickness, other.thickness, rel_tol=TOL))

        def __hash__(self) -> int:
            return hash(relative_round(self.thickness, TOL))

    @dataclass(frozen=True)
    class EndFitting:
        """End fitting specification, approximated as a cone.

        Attributes
        ----------
        length : float
            Cone length (base to apex) [cm].
        direction : {'up', 'down'}
            Orientation of the fitting.
        material : Material
            Fitting material (defaults to ``SS304``).
        """
        length: float
        direction: Literal["up", "down"]
        material: Material = field(default_factory=SS304)

        def __post_init__(self) -> None:
            assert self.length > 0.0, "End Fitting length must be positive."
            assert self.direction in ("up", "down"), (
                "End Fitting direction must be either 'up' or 'down'."
            )

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, FuelElement.EndFitting) and
                    isclose(self.length, other.length, rel_tol=TOL) and
                    self.direction == other.direction and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.length, TOL),
                         self.direction,
                         self.material))

    @property
    def cladding(self) -> Cladding:
        return self._cladding

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
    def upper_end_fitting(self) -> EndFitting:
        return self._upper_end_fitting

    @property
    def upper_air_gap(self) -> AirGap:
        return self._upper_air_gap

    @property
    def upper_graphite_reflector(self) -> GraphiteReflector:
        return self._upper_graphite_reflector

    @property
    def zr_fill_rod(self) -> ZrFillRod:
        return self._zr_fill_rod

    @property
    def fuel_meat(self) -> FuelMeat:
        return self._fuel_meat

    @property
    def moly_disc(self) -> MolyDisc:
        return self._moly_disc

    @property
    def lower_graphite_reflector(self) -> GraphiteReflector:
        return self._lower_graphite_reflector

    @property
    def lower_end_fitting(self) -> EndFitting:
        return self._lower_end_fitting

    @property
    def interior_length(self) -> float:
        return self._interior_length

    @property
    def length(self) -> float:
        return self._length

    @property
    def fuel_pincell(self) -> CylindricalPinCell:
        return self._fuel_region_pincell

    @property
    def moly_disc_pincell(self) -> CylindricalPinCell:
        return self._moly_disc_region_pincell

    @property
    def upper_reflector_pincell(self) -> CylindricalPinCell:
        return self._upper_reflector_region_pincell

    @property
    def lower_reflector_pincell(self) -> CylindricalPinCell:
        return self._lower_reflector_region_pincell

    @property
    def air_gap_pincell(self) -> CylindricalPinCell:
        return self._air_gap_region_pincell


    def __init__(self,
                cladding:                 Cladding,
                upper_end_fitting:        EndFitting,
                upper_air_gap:            AirGap,
                upper_graphite_reflector: GraphiteReflector,
                zr_fill_rod:              ZrFillRod,
                fuel_meat:                FuelMeat,
                moly_disc:                MolyDisc,
                lower_graphite_reflector: GraphiteReflector,
                lower_end_fitting:        EndFitting,
                gap_tolerance:            Optional[float] = 1.0e-8,
                fill_gas:                 Optional[Material] = None,
                outer_material:           Optional[Material] = None,
                name:                     str = "fuel_element"):
        super().__init__(name)
        self._cladding                 = cladding
        self._fill_gas                 = fill_gas or Air()
        self._outer_material           = outer_material or Water()
        self._gap_tolerance            = gap_tolerance
        self._upper_end_fitting        = upper_end_fitting
        self._upper_air_gap            = upper_air_gap
        self._upper_graphite_reflector = upper_graphite_reflector
        self._zr_fill_rod              = zr_fill_rod
        self._fuel_meat                = fuel_meat
        self._moly_disc                = moly_disc
        self._lower_graphite_reflector = lower_graphite_reflector
        self._lower_end_fitting        = lower_end_fitting

        self._interior_length = (self._lower_graphite_reflector.thickness
                                 + self._moly_disc.thickness
                                 + self._fuel_meat.length
                                 + self._upper_graphite_reflector.thickness
                                 + self._upper_air_gap.thickness)
        self._length = (self._interior_length
                        + self._upper_end_fitting.length
                        + self._lower_end_fitting.length)

        self._fuel_region_pincell = self.build_fuel_meat_pincell(
            cladding       = self.cladding,
            fuel_meat      = self.fuel_meat,
            zr_fill_rod    = self.zr_fill_rod,
            fill_gas       = self.fill_gas,
            outer_material = self.outer_material,
            gap_tolerance  = self.gap_tolerance,
            name           = self.name + "_fuel_meat_pincell",
        )
        self._moly_disc_region_pincell = self.build_moly_disc_pincell(
            cladding       = self.cladding,
            moly_disc      = self.moly_disc,
            fill_gas       = self.fill_gas,
            outer_material = self.outer_material,
            gap_tolerance  = self.gap_tolerance,
            name           = self.name + "_moly_disc_pincell",
        )
        self._upper_reflector_region_pincell = self.build_graphite_reflector_pincell(
            cladding       = self.cladding,
            reflector      = self.upper_graphite_reflector,
            fill_gas       = self.fill_gas,
            outer_material = self.outer_material,
            gap_tolerance  = self.gap_tolerance,
            name           = self.name + "_upper_graphite_reflector_pincell",
        )
        self._lower_reflector_region_pincell = self.build_graphite_reflector_pincell(
            cladding       = self.cladding,
            reflector      = self.lower_graphite_reflector,
            fill_gas       = self.fill_gas,
            outer_material = self.outer_material,
            gap_tolerance  = self.gap_tolerance,
            name           = self.name + "_lower_graphite_reflector_pincell",
        )
        self._air_gap_region_pincell = self.build_air_gap_pincell(
            cladding       = self.cladding,
            fill_gas       = self.fill_gas,
            outer_material = self.outer_material,
            gap_tolerance  = self.gap_tolerance,
            name           = self.name + "_air_gap_pincell",
        )

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, FuelElement):
            return False
        return (
            self.cladding == other.cladding and
            self.fill_gas == other.fill_gas and
            self.outer_material == other.outer_material and
            self.upper_end_fitting == other.upper_end_fitting and
            self.upper_air_gap == other.upper_air_gap and
            self.upper_graphite_reflector == other.upper_graphite_reflector and
            self.zr_fill_rod == other.zr_fill_rod and
            self.fuel_meat == other.fuel_meat and
            self.moly_disc == other.moly_disc and
            self.lower_graphite_reflector == other.lower_graphite_reflector and
            self.lower_end_fitting == other.lower_end_fitting and
            ((self.gap_tolerance is None and other.gap_tolerance is None) or
             (self.gap_tolerance is not None and other.gap_tolerance is not None and
              isclose(self.gap_tolerance, other.gap_tolerance, rel_tol=TOL)))
        )

    def __hash__(self) -> int:
        return hash((
            self.cladding,
            self.fill_gas,
            self.outer_material,
            self.upper_end_fitting,
            self.upper_air_gap,
            self.upper_graphite_reflector,
            self.zr_fill_rod,
            self.fuel_meat,
            self.moly_disc,
            self.lower_graphite_reflector,
            self.lower_end_fitting,
            None if self.gap_tolerance is None else relative_round(self.gap_tolerance, TOL),
        ))


    @staticmethod
    def build_fuel_meat_pincell(cladding:       Cladding,
                                fuel_meat:      FuelMeat,
                                zr_fill_rod:    ZrFillRod,
                                fill_gas:       Optional[Material] = None,
                                outer_material: Optional[Material] = None,
                                gap_tolerance:  float = 1.0e-8,
                                name:           str = "fuel_meat_pincell") -> CylindricalPinCell:
        """Build a pincell for the fuel meat region.

        Parameters
        ----------
        cladding : FuelElement.Cladding
            Cladding definition with thickness, outer radius, and material.
        fuel_meat : FuelElement.FuelMeat
            Fuel meat definition with inner/outer radii and material.
        zr_fill_rod : FuelElement.ZrFillRod
            Zirconium fill rod definition.
        fill_gas : Material, optional
            Gap fill material; defaults to ``Air``.
        outer_material : Material, optional
            Exterior/coolant material; defaults to ``Water``.
        gap_tolerance : float, optional
            Minimum thickness to retain a zone; thinner zones are removed. Defaults to 1e-8.
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the fuel meat region.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()

        assert zr_fill_rod.radius <= fuel_meat.inner_radius, (
            "Zr fill rod must fit inside fuel meat inner radius.")
        assert fuel_meat.outer_radius <= cladding.inner_radius, (
            "Fuel meat must fit inside cladding.")

        radii = [zr_fill_rod.radius,
                 fuel_meat.inner_radius,
                 fuel_meat.outer_radius,
                 cladding.inner_radius,
                 cladding.outer_radius]

        materials = [zr_fill_rod.material,
                     fill_gas,
                     fuel_meat.material,
                     fill_gas,
                     cladding.material,
                     outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance)


    @staticmethod
    def build_moly_disc_pincell(cladding:       Cladding,
                                moly_disc:      MolyDisc,
                                fill_gas:       Optional[Material] = None,
                                outer_material: Optional[Material] = None,
                                gap_tolerance:  float = 1.0e-8,
                                name:           str = "moly_disc_pincell") -> CylindricalPinCell:
        """Build a pincell for the molybdenum disc region.

        Parameters
        ----------
        cladding : FuelElement.Cladding
            Cladding definition with thickness, outer radius, and material.
        moly_disc : FuelElement.MolyDisc
            Molybdenum disc definition (radius, material).
        fill_gas : Material, optional
            Gap fill material; defaults to ``Air``.
        outer_material : Material, optional
            Exterior/coolant material; defaults to ``Water``.
        gap_tolerance : float, optional
            Minimum thickness to retain a zone; thinner zones are removed. Defaults to 1e-8.
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the molybdenum disc region.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()

        assert moly_disc.radius <= cladding.inner_radius, "Moly disc must fit inside cladding."

        radii     = [moly_disc.radius,   cladding.inner_radius, cladding.outer_radius]
        materials = [moly_disc.material, fill_gas,              cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance)


    @staticmethod
    def build_graphite_reflector_pincell(cladding:       Cladding,
                                         reflector:      GraphiteReflector,
                                         fill_gas:       Optional[Material] = None,
                                         outer_material: Optional[Material] = None,
                                         gap_tolerance:  float = 1.0e-8,
                                         name:           Optional[str] = "graphite_reflector_pincell") -> CylindricalPinCell:
        """Build a pincell for the graphite reflector region.

        Parameters
        ----------
        cladding : FuelElement.Cladding
            Cladding definition with thickness, outer radius, and material.
        reflector : FuelElement.GraphiteReflector
            Graphite reflector definition (radius, material).
        fill_gas : Material, optional
            Gap fill material; defaults to ``Air``.
        outer_material : Material, optional
            Exterior/coolant material; defaults to ``Water``.
        gap_tolerance : float, optional
            Minimum thickness to retain a zone; thinner zones are removed. Defaults to 1e-8.
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the reflector region.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()

        assert reflector.radius <= cladding.inner_radius, "Reflector must fit inside cladding."

        radii     = [reflector.radius,   cladding.inner_radius, cladding.outer_radius]
        materials = [reflector.material, fill_gas,              cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance)


    @staticmethod
    def build_air_gap_pincell(cladding:       Cladding,
                              fill_gas:       Optional[Material] = None,
                              outer_material: Optional[Material] = None,
                              gap_tolerance:  float = 1.0e-8,
                              name:           str = "air_gap_pincell") -> CylindricalPinCell:
        """Build a pincell for the air gap region (uses fill_gas for core).

        Parameters
        ----------
        cladding : FuelElement.Cladding
            Cladding definition with thickness, outer radius, and material.
        fill_gas : Material, optional
            Gap fill material; defaults to ``Air``.
        outer_material : Material, optional
            Exterior/coolant material; defaults to ``Water``.
        gap_tolerance : float, optional
            Minimum thickness to retain a zone; thinner zones are removed. Defaults to 1e-8.
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the air-gap region.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()

        radii     = [cladding.inner_radius, cladding.outer_radius]
        materials = [fill_gas,              cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance)

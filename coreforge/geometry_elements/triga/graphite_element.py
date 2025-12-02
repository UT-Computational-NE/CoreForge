from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose
from typing import Literal, Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Air, Al6061T6, Graphite, Material, Water


class GraphiteElement(GeometryElement):
    """TRIGA graphite element definitions and pincell builder.

    Gaps are only added if wider than ``gap_tolerance``; otherwise the adjacent regions
    are considered in hard contact (prevents near-duplicate radii).

    Parameters
    ----------
    cladding : GraphiteElement.Cladding
        Cladding definition with thickness, outer radius, and material.
    graphite_meat : GraphiteElement.GraphiteMeat
        Graphite meat definition with radius, length, and material.
    upper_end_fitting : GraphiteElement.EndFitting
        Upper end fitting geometry and material (cone approximation).
    lower_end_fitting : GraphiteElement.EndFitting
        Lower end fitting geometry and material (cone approximation).
    gap_tolerance : float, optional
        Minimum thickness to retain a radial gap; thinner gaps are removed. Defaults to 1e-8.
    fill_gas : Optional[Material]
        Gas filling any radial gaps between meat and cladding. Defaults to ``Air``.
    outer_material : Optional[Material]
        Exterior/coolant material surrounding the cladding. Defaults to ``Water``.
    name : str, optional
        Name for the graphite element (also used for pincell naming).


    Attributes
    ----------
    cladding : GraphiteElement.Cladding
        Cladding specification.
    graphite_meat : GraphiteElement.GraphiteMeat
        Graphite meat specification.
    upper_end_fitting : GraphiteElement.EndFitting
        Upper end fitting specification.
    lower_end_fitting : GraphiteElement.EndFitting
        Lower end fitting specification.
    interior_length : float
        Axial length of the graphite meat.
    gap_tolerance : float, optional
        Minimum thickness to retain a radial gap.
    graphite_pincell : CylindricalPinCell
        Pincell representing the graphite meat radial region.
    """

    @dataclass(frozen=True)
    class GraphiteMeat:
        """Graphite meat specification.

        Attributes
        ----------
        outer_radius : float
            Outer radius of the graphite meat [cm].
        length : float
            Axial length of the graphite meat [cm].
        material : Material
            Graphite material. Defaults to ``Graphite`` at 1.6 g/cc (Ref. [1]_ pg. 50).
        """
        outer_radius: float
        length: float
        material: Material = field(default_factory=lambda: Graphite(graphite_density=1.6))

        def __post_init__(self) -> None:
            assert self.outer_radius > 0.0, "Graphite Meat outer radius must be positive."
            assert self.length > 0.0, "Graphite Meat length must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, GraphiteElement.GraphiteMeat) and
                    isclose(self.outer_radius, other.outer_radius, rel_tol=TOL) and
                    isclose(self.length, other.length, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.outer_radius, TOL),
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
            Cladding material (defaults to ``Al6061T6``).
        """
        thickness: float
        outer_radius: float
        inner_radius: float = field(init=False)
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Cladding thickness must be positive."
            assert self.outer_radius > self.thickness, (
                "Cladding outer radius must exceed thickness."
            )
            object.__setattr__(self, "inner_radius", self.outer_radius - self.thickness)

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, GraphiteElement.Cladding) and
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
    class EndFitting:
        """End fitting specification, approximated as a cone.

        Attributes
        ----------
        length : float
            Cone length (base to apex) [cm].
        direction : {'up', 'down'}
            Orientation of the fitting.
        material : Material
            Fitting material (defaults to ``Al6061T6``).
        """
        length: float
        direction: Literal["up", "down"]
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.length > 0.0, "End Fitting length must be positive."
            assert self.direction in ("up", "down"), (
                "End Fitting direction must be either 'up' or 'down'."
            )

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, GraphiteElement.EndFitting) and
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
    def graphite_meat(self) -> GraphiteMeat:
        return self._graphite_meat

    @property
    def fill_gas(self) -> Material:
        return self._fill_gas

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @property
    def gap_tolerance(self) -> float:
        return self._gap_tolerance

    @property
    def upper_end_fitting(self) -> EndFitting:
        return self._upper_end_fitting

    @property
    def lower_end_fitting(self) -> EndFitting:
        return self._lower_end_fitting

    @property
    def interior_length(self) -> float:
        return self._interior_length

    @property
    def graphite_pincell(self) -> CylindricalPinCell:
        return self._graphite_region_pincell

    def __init__(self,
                 cladding:          Cladding,
                 graphite_meat:     GraphiteMeat,
                 upper_end_fitting: EndFitting,
                 lower_end_fitting: EndFitting,
                 gap_tolerance:     float = 1.0e-8,
                 fill_gas:          Optional[Material] = None,
                 outer_material:    Optional[Material] = None,
                 name:              str = "triga_graphite_element"):
        super().__init__(name)
        self._cladding          = cladding
        self._graphite_meat     = graphite_meat
        self._upper_end_fitting = upper_end_fitting
        self._lower_end_fitting = lower_end_fitting
        self._gap_tolerance     = gap_tolerance
        self._fill_gas          = fill_gas or Air()
        self._outer_material    = outer_material or Water()

        self._interior_length = self._graphite_meat.length

        self._graphite_region_pincell = self.build_graphite_meat_pincell(
            cladding       = self.cladding,
            graphite_meat  = self.graphite_meat,
            fill_gas       = self.fill_gas,
            outer_material = self.outer_material,
            gap_tolerance  = self.gap_tolerance,
            name           = self.name + "_graphite_meat_pincell",
        )

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, GraphiteElement):
            return False
        return (
            self.cladding == other.cladding and
            self.graphite_meat == other.graphite_meat and
            self.upper_end_fitting == other.upper_end_fitting and
            self.lower_end_fitting == other.lower_end_fitting and
            self.fill_gas == other.fill_gas and
            self.outer_material == other.outer_material and
            isclose(self.gap_tolerance, other.gap_tolerance, rel_tol=TOL)
        )

    def __hash__(self) -> int:
        return hash((
            self.cladding,
            self.graphite_meat,
            self.upper_end_fitting,
            self.lower_end_fitting,
            self.fill_gas,
            self.outer_material,
            relative_round(self.gap_tolerance, TOL),
        ))

    @staticmethod
    def build_graphite_meat_pincell(cladding:       Cladding,
                                    graphite_meat:  GraphiteMeat,
                                    fill_gas:       Optional[Material] = None,
                                    outer_material: Optional[Material] = None,
                                    gap_tolerance:  float = 1.0e-8,
                                    name:           str = "graphite_meat_pincell") -> CylindricalPinCell:
        """Build a pincell for the graphite meat region.

        Parameters
        ----------
        cladding : GraphiteElement.Cladding
            Cladding definition with thickness, outer radius, and material.
        graphite_meat : GraphiteElement.GraphiteMeat
            Graphite meat definition with outer radius, length, and material.
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
            Concentric pincell representing the graphite element cross section.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()

        assert graphite_meat.outer_radius <= cladding.inner_radius, (
            "Graphite meat must fit inside cladding."
        )

        radii     = [graphite_meat.outer_radius, cladding.inner_radius, cladding.outer_radius]
        materials = [graphite_meat.material, fill_gas, cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance)

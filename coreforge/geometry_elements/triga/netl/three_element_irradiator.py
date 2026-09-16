from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose
from typing import List, Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.cylindrical_stack import CylindricalStack
from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Air, Al6061T6, Material, Water, unique_materials


class ThreeElementIrradiator(GeometryElement):
    """Conventional NETL three-element irradiation facility geometry.

    Parameters
    ----------
    outer_casing : ThreeElementIrradiator.OuterCasing
        Outer casing specification.
    inner_sleeve : ThreeElementIrradiator.InnerSleeve
        Inner sleeve specification.
    liner : ThreeElementIrradiator.Liner
        Liner specifications.
    fill_material : Material, optional
        Material filling the irradiator interior and interstitial spaces
    outer_material : Material, optional
        Material surrounding the outer casing.
    gap_tolerance : float, optional
        Minimum radial-zone thickness to retain. Defaults to ``None``.
    name : str, optional
        Name for the irradiator.
    """

    @dataclass(frozen=True)
    class OuterCasing:
        """Outer casing specification.

        Parameters
        ----------
        inner_radius : float
            Inner radius of the annular casing sidewall [cm].
        outer_radius : float
            Outer radius of the casing, including its solid ends [cm].
        length : float
            Overall casing length from the bottom of the solid lower end to
            the top of the solid upper end [cm].
        solid_upper_end_thickness : float
            Axial thickness of the solid upper end [cm].
        solid_lower_end_thickness : float
            Axial thickness of the solid lower end [cm].
        material : Material, optional
            Material assigned to the casing (defaults to ``Al6061T6``).
        """

        inner_radius: float
        outer_radius: float
        length: float
        solid_upper_end_thickness: float
        solid_lower_end_thickness: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.inner_radius > 0.0, "Outer casing inner radius must be positive."
            assert self.outer_radius > self.inner_radius, (
                "Outer casing outer radius must exceed its inner radius."
            )
            assert self.length > 0.0, "Outer casing length must be positive."
            assert self.solid_upper_end_thickness > 0.0, (
                "Outer casing solid upper-end thickness must be positive."
            )
            assert self.solid_lower_end_thickness > 0.0, (
                "Outer casing solid lower-end thickness must be positive."
            )
            assert self.solid_upper_end_thickness + self.solid_lower_end_thickness < self.length, (
                "Outer casing solid ends must not consume its full length."
            )

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, ThreeElementIrradiator.OuterCasing) and
                    isclose(self.inner_radius, other.inner_radius, rel_tol=TOL) and
                    isclose(self.outer_radius, other.outer_radius, rel_tol=TOL) and
                    isclose(self.length, other.length, rel_tol=TOL) and
                    isclose(self.solid_upper_end_thickness,
                            other.solid_upper_end_thickness, rel_tol=TOL) and
                    isclose(self.solid_lower_end_thickness,
                            other.solid_lower_end_thickness, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.inner_radius, TOL),
                         relative_round(self.outer_radius, TOL),
                         relative_round(self.length, TOL),
                         relative_round(self.solid_upper_end_thickness, TOL),
                         relative_round(self.solid_lower_end_thickness, TOL),
                         self.material))

    @dataclass(frozen=True)
    class InnerSleeve:
        """Inner sleeve specification.

        Parameters
        ----------
        inner_radius : float
            Inner radius of the annular sleeve sidewall [cm].
        outer_radius : float
            Outer radius of the sleeve sidewall and solid bottom [cm]. This
            radius also establishes the inner radius of the liner.
        sidewall_length : float
            Axial length of the annular sidewall above the sleeve bottom [cm].
        bottom_thickness : float
            Axial thickness of the solid sleeve bottom [cm].
        material : Material, optional
            Material assigned to the sleeve (defaults to ``Al6061T6``).
        """

        inner_radius: float
        outer_radius: float
        sidewall_length: float
        bottom_thickness: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.inner_radius > 0.0, "Inner sleeve inner radius must be positive."
            assert self.outer_radius > self.inner_radius, (
                "Inner sleeve outer radius must exceed its inner radius."
            )
            assert self.sidewall_length > 0.0, "Inner sleeve sidewall length must be positive."
            assert self.bottom_thickness > 0.0, "Inner sleeve bottom thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, ThreeElementIrradiator.InnerSleeve) and
                    isclose(self.inner_radius, other.inner_radius, rel_tol=TOL) and
                    isclose(self.outer_radius, other.outer_radius, rel_tol=TOL) and
                    isclose(self.sidewall_length, other.sidewall_length, rel_tol=TOL) and
                    isclose(self.bottom_thickness, other.bottom_thickness, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.inner_radius, TOL),
                         relative_round(self.outer_radius, TOL),
                         relative_round(self.sidewall_length, TOL),
                         relative_round(self.bottom_thickness, TOL),
                         self.material))

    @dataclass(frozen=True)
    class Liner:
        """Liner specification.

        Parameters
        ----------
        thickness : float
            Radial thickness of the liner sidewall [cm].
        sidewall_length : float
            Axial length of the annular liner sidewall above the liner bottom
            [cm].
        bottom_thickness : float
            Axial thickness of the solid liner bottom [cm].
        material : Material
            Material assigned to the liner.
        """

        thickness: float
        sidewall_length: float
        bottom_thickness: float
        material: Material

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Liner thickness must be positive."
            assert self.sidewall_length > 0.0, "Liner sidewall length must be positive."
            assert self.bottom_thickness > 0.0, "Liner bottom thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, ThreeElementIrradiator.Liner) and
                    isclose(self.thickness, other.thickness, rel_tol=TOL) and
                    isclose(self.sidewall_length, other.sidewall_length, rel_tol=TOL) and
                    isclose(self.bottom_thickness, other.bottom_thickness, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.thickness, TOL),
                         relative_round(self.sidewall_length, TOL),
                         relative_round(self.bottom_thickness, TOL),
                         self.material))

    @property
    def outer_casing(self) -> OuterCasing:
        return self._outer_casing

    @property
    def inner_sleeve(self) -> InnerSleeve:
        return self._inner_sleeve

    @property
    def liner(self) -> Liner:
        return self._liner

    @property
    def fill_material(self) -> Material:
        return self._fill_material

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @property
    def gap_tolerance(self) -> Optional[float]:
        return self._gap_tolerance

    @property
    def length(self) -> float:
        return self.outer_casing.length

    @property
    def solid_end_pincell(self) -> CylindricalPinCell:
        return self._solid_end_pincell

    @property
    def liner_bottom_pincell(self) -> CylindricalPinCell:
        return self._liner_bottom_pincell

    @property
    def inner_sleeve_bottom_pincell(self) -> CylindricalPinCell:
        return self._inner_sleeve_bottom_pincell

    @property
    def lined_pincell(self) -> CylindricalPinCell:
        return self._lined_pincell

    @property
    def inner_sleeve_pincell(self) -> CylindricalPinCell:
        return self._inner_sleeve_pincell

    @property
    def outer_casing_pincell(self) -> CylindricalPinCell:
        return self._outer_casing_pincell

    def __init__(self,
                 outer_casing:  OuterCasing,
                 inner_sleeve:  InnerSleeve,
                 liner:         Liner,
                 fill_material: Optional[Material] = None,
                 outer_material: Optional[Material] = None,
                 gap_tolerance: Optional[float] = None,
                 name:          str = "three_element_irradiator") -> None:
        super().__init__(name)
        liner_outer_radius = inner_sleeve.outer_radius + liner.thickness
        assert liner_outer_radius < outer_casing.inner_radius, (
            "Liner outer radius must be inside the outer casing inner radius."
        )
        assert liner.sidewall_length > inner_sleeve.bottom_thickness, (
            "Liner sidewall must extend above the inner sleeve bottom."
        )
        assert inner_sleeve.bottom_thickness + inner_sleeve.sidewall_length > liner.sidewall_length, (
            "Inner sleeve sidewall must extend above the liner sidewall."
        )
        casing_annular_length = (outer_casing.length -
                                 outer_casing.solid_lower_end_thickness -
                                 outer_casing.solid_upper_end_thickness)
        sleeve_top = (liner.bottom_thickness +
                      inner_sleeve.bottom_thickness +
                      inner_sleeve.sidewall_length)
        assert casing_annular_length > sleeve_top, (
            "Inner sleeve must terminate below the outer casing solid upper end."
        )
        if gap_tolerance is not None:
            assert gap_tolerance >= 0.0, "Three-element irradiator gap tolerance must be non-negative."

        self._outer_casing = outer_casing
        self._inner_sleeve = inner_sleeve
        self._liner = liner
        self._fill_material = fill_material or Air()
        self._outer_material = outer_material or Water()
        self._gap_tolerance = gap_tolerance

        def pincell(radii: List[float], materials: List[Material], suffix: str) -> CylindricalPinCell:
            return CylindricalPinCell(radii=radii,
                                      materials=materials,
                                      name=f"{self.name}_{suffix}_pincell",
                                      min_zone_thickness=self.gap_tolerance)

        self._solid_end_pincell = pincell(
            [outer_casing.outer_radius],
            [outer_casing.material, self.outer_material],
            "solid_end",
        )
        self._liner_bottom_pincell = pincell(
            [liner_outer_radius, outer_casing.inner_radius, outer_casing.outer_radius],
            [liner.material, self.fill_material, outer_casing.material, self.outer_material],
            "liner_bottom",
        )
        self._inner_sleeve_bottom_pincell = pincell(
            [inner_sleeve.outer_radius, liner_outer_radius,
             outer_casing.inner_radius, outer_casing.outer_radius],
            [inner_sleeve.material, liner.material, self.fill_material,
             outer_casing.material, self.outer_material],
            "inner_sleeve_bottom",
        )
        self._lined_pincell = pincell(
            [inner_sleeve.inner_radius, inner_sleeve.outer_radius, liner_outer_radius,
             outer_casing.inner_radius, outer_casing.outer_radius],
            [self.fill_material, inner_sleeve.material, liner.material,
             self.fill_material, outer_casing.material, self.outer_material],
            "lined",
        )
        self._inner_sleeve_pincell = pincell(
            [inner_sleeve.inner_radius, inner_sleeve.outer_radius,
             outer_casing.inner_radius, outer_casing.outer_radius],
            [self.fill_material, inner_sleeve.material, self.fill_material,
             outer_casing.material, self.outer_material],
            "inner_sleeve",
        )
        self._outer_casing_pincell = pincell(
            [outer_casing.inner_radius, outer_casing.outer_radius],
            [self.fill_material, outer_casing.material, self.outer_material],
            "outer_casing",
        )

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, ThreeElementIrradiator):
            return False
        return (self.outer_casing == other.outer_casing and
                self.inner_sleeve == other.inner_sleeve and
                self.liner == other.liner and
                self.fill_material == other.fill_material and
                self.outer_material == other.outer_material and
                ((self.gap_tolerance is None and other.gap_tolerance is None) or
                 (self.gap_tolerance is not None and other.gap_tolerance is not None and
                  isclose(self.gap_tolerance, other.gap_tolerance, rel_tol=TOL))))

    def __hash__(self) -> int:
        return hash((self.outer_casing,
                     self.inner_sleeve,
                     self.liner,
                     self.fill_material,
                     self.outer_material,
                     None if self.gap_tolerance is None else relative_round(self.gap_tolerance, TOL)))

    def get_materials(self) -> List[Material]:
        return unique_materials([
            self.outer_casing.material,
            self.inner_sleeve.material,
            self.liner.material,
            self.fill_material,
            self.outer_material,
        ])

    def as_stack(self, bottom_pos: float = 0.0) -> CylindricalStack:
        """Return the irradiator as a cylindrical stack, ordered bottom to top.

        Parameters
        ----------
        bottom_pos : float, optional
            Axial position of the stack bottom [cm]. Defaults to 0.0.
        """

        lined_length = self.liner.sidewall_length - self.inner_sleeve.bottom_thickness
        sleeve_only_length = (self.inner_sleeve.bottom_thickness +
                              self.inner_sleeve.sidewall_length -
                              self.liner.sidewall_length)
        casing_only_length = (self.outer_casing.length -
                              self.outer_casing.solid_lower_end_thickness -
                              self.liner.bottom_thickness -
                              self.inner_sleeve.bottom_thickness -
                              self.inner_sleeve.sidewall_length -
                              self.outer_casing.solid_upper_end_thickness)

        return CylindricalStack(
            segments=[
                Stack.Segment(self.solid_end_pincell,
                              self.outer_casing.solid_lower_end_thickness),
                Stack.Segment(self.liner_bottom_pincell,
                              self.liner.bottom_thickness),
                Stack.Segment(self.inner_sleeve_bottom_pincell,
                              self.inner_sleeve.bottom_thickness),
                Stack.Segment(self.lined_pincell, lined_length),
                Stack.Segment(self.inner_sleeve_pincell, sleeve_only_length),
                Stack.Segment(self.outer_casing_pincell, casing_only_length),
                Stack.Segment(self.solid_end_pincell,
                              self.outer_casing.solid_upper_end_thickness),
            ],
            name=self.name,
            bottom_pos=bottom_pos,
        )

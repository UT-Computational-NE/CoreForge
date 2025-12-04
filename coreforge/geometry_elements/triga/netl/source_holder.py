from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose
from typing import Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Air, Al6061T6, Material, Water


class SourceHolder(GeometryElement):
    """TRIGA NETL source holder cavity and pincell builder.

    Parameters
    ----------
    length : float
        Axial length of the source holder [cm].
    cavity : SourceHolder.Cavity
        Cavity definition (radius and material).
    cladding : SourceHolder.Cladding
        Cladding definition (outer radius and material).
    outer_material : Optional[Material]
        Material surrounding the cladding exterior. Defaults to ``Water``.
    gap_tolerance : float, optional
        Minimum thickness to retain a radial zone; thinner gaps are removed. Defaults to ``None`` (no filtering).
    name : str, optional
        Name for the source holder element.

    Attributes
    ----------
    length : float
        Axial length of the source holder [cm].
    cavity : SourceHolder.Cavity
        Cavity specification.
    cladding : SourceHolder.Cladding
        Cladding specification.
    outer_material : Material
        Exterior/coolant material.
    gap_tolerance : float, optional
        Minimum thickness to retain a radial zone (defaults to ``None`` for no filtering).
    cavity_pincell : CylindricalPinCell
        Pincell representing the cavity and cladding cross section.
    solid_pincell : CylindricalPinCell
        Pincell representing the solid cladding without a cavity.
    """

    @dataclass(frozen=True)
    class Cavity:
        """Source holder cavity specification.

        Parameters
        ----------
        radius : float
            Radius of the cavity [cm].
        length : float
            Axial length of the cavity [cm].
        axial_offset : float, optional
            Offset of the cavity centerline from the source holder centerline [cm].
            Positive values shift upward; negative values shift downward.
        material : Material, optional
            Filling material (defaults to ``Air``).
        """
        radius: float
        length: float
        axial_offset: float = 0.0
        material: Material = field(default_factory=Air)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Source Holder cavity radius must be positive."
            assert self.length > 0.0, "Source Holder cavity length must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, SourceHolder.Cavity) and
                    isclose(self.radius, other.radius, rel_tol=TOL) and
                    isclose(self.length, other.length, rel_tol=TOL) and
                    isclose(self.axial_offset, other.axial_offset, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.radius, TOL),
                         relative_round(self.length, TOL),
                         relative_round(self.axial_offset, TOL),
                         self.material))

    @dataclass(frozen=True)
    class Cladding:
        """Source holder cladding specification.

        Parameters
        ----------
        outer_radius : float
            Outer radius of the source holder cladding [cm].
        material : Material, optional
            Cladding material (defaults to ``Al6061T6``).
        """
        outer_radius: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.outer_radius > 0.0, "Source Holder cladding outer radius must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, SourceHolder.Cladding) and
                    isclose(self.outer_radius, other.outer_radius, rel_tol=TOL) and
                    self.material == other.material)

        def __hash__(self) -> int:
            return hash((relative_round(self.outer_radius, TOL), self.material))

    @property
    def length(self) -> float:
        return self._length

    @property
    def cavity(self) -> Cavity:
        return self._cavity

    @property
    def cladding(self) -> Cladding:
        return self._cladding

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @property
    def gap_tolerance(self) -> Optional[float]:
        return self._gap_tolerance

    @property
    def cavity_pincell(self) -> CylindricalPinCell:
        return self._cavity_pincell

    @property
    def solid_pincell(self) -> CylindricalPinCell:
        return self._solid_pincell

    def __init__(self,
                 length:         float,
                 cavity:         Cavity,
                 cladding:       Cladding,
                 outer_material: Optional[Material] = None,
                 gap_tolerance:  Optional[float] = None,
                 name:           str = "source_holder"):
        super().__init__(name)
        assert length > 0.0, "Source holder length must be positive."
        self._length = length
        self._cavity = cavity
        self._cladding = cladding
        self._outer_material = outer_material or Water()
        self._gap_tolerance = gap_tolerance

        self._cavity_pincell = self.build_cavity_pincell(
            cavity=self.cavity,
            cladding=self.cladding,
            outer_material=self.outer_material,
            gap_tolerance=self.gap_tolerance,
            name=self.name + "_cavity_pincell",
        )
        self._solid_pincell = self.build_solid_pincell(
            cladding=self.cladding,
            outer_material=self.outer_material,
            name=self.name + "_solid_pincell",
        )

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, SourceHolder):
            return False
        return (
            isclose(self.length, other.length, rel_tol=TOL) and
            self.cavity == other.cavity and
            self.cladding == other.cladding and
            self.outer_material == other.outer_material and
            ((self.gap_tolerance is None and other.gap_tolerance is None) or
             (self.gap_tolerance is not None and other.gap_tolerance is not None and
              isclose(self.gap_tolerance, other.gap_tolerance, rel_tol=TOL)))
        )

    def __hash__(self) -> int:
        return hash((
            relative_round(self.length, TOL),
            self.cavity,
            self.cladding,
            self.outer_material,
            None if self.gap_tolerance is None else relative_round(self.gap_tolerance, TOL),
        ))

    @staticmethod
    def build_cavity_pincell(cavity:         Cavity,
                             cladding:       Cladding,
                             outer_material: Optional[Material] = None,
                             gap_tolerance:  Optional[float] = None,
                             name:           str = "source_holder_cavity") -> CylindricalPinCell:
        """Build a pincell for the source holder cavity/cladding cross section.

        Parameters
        ----------
        cavity : SourceHolder.Cavity
            Cavity definition (radius and material).
        cladding : SourceHolder.Cladding
            Cladding definition (outer radius and material).
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        gap_tolerance : float, optional
            Minimum zone thickness to retain (defaults to ``None`` for no filtering).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the cavity plus cladding.
        """
        outer_material = outer_material or Water()

        assert cavity.radius <= cladding.outer_radius, "Cavity must fit inside the cladding."

        radii = [cavity.radius, cladding.outer_radius]
        materials = [cavity.material, cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance)

    @staticmethod
    def build_solid_pincell(cladding:       Cladding,
                            outer_material: Optional[Material] = None,
                            name:           str = "source_holder_solid") -> CylindricalPinCell:
        """Build a pincell for a solid source holder (no cavity).

        Parameters
        ----------
        cladding : SourceHolder.Cladding
            Cladding definition (outer radius and material).
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing a solid rod.
        """
        outer_material = outer_material or Water()

        radii = [cladding.outer_radius]
        materials = [cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name)

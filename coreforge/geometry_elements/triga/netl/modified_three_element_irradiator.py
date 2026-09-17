from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose
from typing import Dict, List, Optional, TypedDict

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.cylindrical_stack import CylindricalStack
from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Air, Al6061T6, Cd, Material, Water, unique_materials
from coreforge.utils import TolerantEqualityMixin


class ModifiedThreeElementIrradiator(GeometryElement):
    """Detailed NETL modified three-element irradiation facility geometry.

    The geometry follows the component topology of the detailed modified 3-EL
    specification. Its outer casing begins at the facility bottom, while the
    pneumatic system and filter canisters are positioned by their specified
    alignment with the top of casing Tube #1. The resulting stack contains the
    ~20 distinct axial regions of the detailed model.

    Parameters
    ----------
    outer_casing : ModifiedThreeElementIrradiator.OuterCasing
        Two-tube outer casing specification.
    pneumatic_system : ModifiedThreeElementIrradiator.PneumaticSystem
        Central pneumatic tube and sleeve specification.
    b4c_canister : ModifiedThreeElementIrradiator.B4CCanister
        Upper natural-B4C canister specification.
    b10_canister : ModifiedThreeElementIrradiator.B10Canister
        Lower enriched-boron canister and cadmium sleeve specification.
    silver_disk : ModifiedThreeElementIrradiator.Disk
        Silver disk below the B-10 canister.
    cadmium_disk : ModifiedThreeElementIrradiator.Disk
        Cadmium disk below the silver disk.
    hollow_spacer : ModifiedThreeElementIrradiator.HollowSpacer
        Air-filled aluminum spacer and solid upper cap specification.
    solid_spacer : ModifiedThreeElementIrradiator.SolidSpacer
        Solid aluminum lower spacer specification.
    fill_material : Material, optional
        Material filling interstitial spaces (defaults to ``Air``).
    outer_material : Material, optional
        Material surrounding the outer casing (defaults to ``Water``).
    gap_tolerance : float, optional
        Minimum radial-zone thickness to retain. Defaults to ``None``.
    name : str, optional
        Name for the irradiator.
    """

    @dataclass(frozen=True, eq=False)
    class OuterCasing(TolerantEqualityMixin):
        """Outer aluminum casing specification.

        Parameters
        ----------
        tube_1_inner_radius : float
            Tube #1 inner radius [cm].
        tube_1_outer_radius : float
            Tube #1 outer radius [cm].
        tube_1_length : float
            Tube #1 axial length from the facility bottom [cm].
        tube_2_outer_radius : float
            Tube #2 outer radius [cm]. Tube #2 shares the Tube #1 inner
            radius over its annular portion.
        tube_2_annulus_length : float
            Length over which Tube #2 surrounds the upper portion of Tube #1
            [cm].
        tube_2_end_cap_thickness : float
            Thickness of the solid Tube #2 region above Tube #1 [cm].
        material : Material, optional
            Material assigned to both tubes (defaults to ``Al6061T6``).
        """

        tube_1_inner_radius: float
        tube_1_outer_radius: float
        tube_1_length: float
        tube_2_outer_radius: float
        tube_2_annulus_length: float
        tube_2_end_cap_thickness: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert 0.0 < self.tube_1_inner_radius < self.tube_1_outer_radius, (
                "Tube #1 radii must be positive and increasing."
            )
            assert self.tube_2_outer_radius > self.tube_1_outer_radius, (
                "Tube #2 outer radius must exceed the Tube #1 outer radius."
            )
            assert self.tube_1_length > 0.0, "Tube #1 length must be positive."
            assert 0.0 < self.tube_2_annulus_length < self.tube_1_length, (
                "Tube #2 annulus length must be positive and shorter than Tube #1."
            )
            assert self.tube_2_end_cap_thickness > 0.0, (
                "Tube #2 end-cap thickness must be positive."
            )

    @dataclass(frozen=True, eq=False)
    class PneumaticSystem(TolerantEqualityMixin):
        """Central pneumatic tube and sleeve specification.

        Parameters
        ----------
        tube_inner_radius : float
            Pneumatic-tube inner radius [cm].
        tube_outer_radius : float
            Pneumatic-tube outer radius [cm].
        sleeve_inner_radius : float
            Pneumatic-sleeve inner radius [cm].
        sleeve_outer_radius : float
            Pneumatic-sleeve outer radius [cm].
        open_tube_length : float
            Length of the open pneumatic-tube passage below the top of Tube #1
            [cm].
        tube_lower_end_cap_thickness : float
            Pneumatic-tube lower-end-cap thickness [cm].
        sleeve_lower_end_cap_thickness : float
            Pneumatic-sleeve lower-end-cap thickness [cm].
        material : Material, optional
            Material assigned to the pneumatic tube and sleeve (defaults to
            ``Al6061T6``).
        fill_material : Material, optional
            Material filling the central passage and tube-to-sleeve gap
            (defaults to ``Air``).
        """

        tube_inner_radius: float
        tube_outer_radius: float
        sleeve_inner_radius: float
        sleeve_outer_radius: float
        open_tube_length: float
        tube_lower_end_cap_thickness: float
        sleeve_lower_end_cap_thickness: float
        material: Material = field(default_factory=Al6061T6)
        fill_material: Material = field(default_factory=Air)

        def __post_init__(self) -> None:
            assert 0.0 < self.tube_inner_radius < self.tube_outer_radius, (
                "Pneumatic-tube radii must be positive and increasing."
            )
            assert self.tube_outer_radius < self.sleeve_inner_radius, (
                "Pneumatic-sleeve inner radius must exceed the tube outer radius."
            )
            assert self.sleeve_inner_radius < self.sleeve_outer_radius, (
                "Pneumatic-sleeve outer radius must exceed its inner radius."
            )
            assert self.open_tube_length > 0.0, "Open-tube length must be positive."
            assert self.tube_lower_end_cap_thickness > 0.0, (
                "Pneumatic-tube lower-end-cap thickness must be positive."
            )
            assert self.sleeve_lower_end_cap_thickness > 0.0, (
                "Pneumatic-sleeve lower-end-cap thickness must be positive."
            )

    @dataclass(frozen=True, eq=False)
    class B4CCanister(TolerantEqualityMixin):
        """Upper natural-B4C canister specification.

        Parameters
        ----------
        b4c_region_inner_radius : float
            Inner radius of the natural-B4C annulus [cm].
        b4c_region_outer_radius : float
            Outer radius of the natural-B4C annulus [cm].
        canister_outer_radius : float
            Outer radius of the aluminum canister [cm].
        top_cap_thickness : float
            Top-cap axial thickness [cm].
        b4c_region_thickness : float
            B4C-region axial thickness [cm].
        bottom_cap_thickness : float
            Bottom-cap axial thickness [cm].
        b4c_material : Material
            Material assigned to the B4C region.
        canister_material : Material, optional
            Material assigned to the canister (defaults to ``Al6061T6``).
        """

        b4c_region_inner_radius: float
        b4c_region_outer_radius: float
        canister_outer_radius: float
        top_cap_thickness: float
        b4c_region_thickness: float
        bottom_cap_thickness: float
        b4c_material: Material
        canister_material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert 0.0 < self.b4c_region_inner_radius < self.b4c_region_outer_radius, (
                "B4C-region radii must be positive and increasing."
            )
            assert self.b4c_region_outer_radius < self.canister_outer_radius, (
                "B4C-region outer radius must be inside the canister."
            )
            assert self.top_cap_thickness > 0.0, "B4C top-cap thickness must be positive."
            assert self.b4c_region_thickness > 0.0, (
                "B4C-region axial thickness must be positive."
            )
            assert self.bottom_cap_thickness > 0.0, (
                "B4C bottom-cap thickness must be positive."
            )

        @property
        def length(self) -> float:
            """Return the complete canister length [cm]."""
            return (self.top_cap_thickness + self.b4c_region_thickness +
                    self.bottom_cap_thickness)

    @dataclass(frozen=True, eq=False)
    class B10Canister(TolerantEqualityMixin):
        """Lower enriched-boron canister and cadmium sleeve specification.

        Parameters
        ----------
        b10_annulus_inner_radius : float
            Inner radius of the annular B-10 regions and outer radius of the
            canister interior wall [cm].
        upper_b10_outer_radius : float
            Outer radius of the upper B-10 annulus [cm].
        lower_b10_outer_radius : float
            Outer radius of the lower B-10 region [cm].
        canister_exterior_wall_radius : float
            Outer radius of the canister exterior wall [cm].
        cadmium_sleeve_outer_radius : float
            Outer radius of the cadmium sleeve [cm].
        gap_to_b4c_canister : float
            Axial air gap between the B-10 and B4C canisters [cm].
        top_cap_thickness : float
            B-10 canister top-cap axial thickness [cm].
        upper_b10_region_thickness : float
            Upper annular B-10 region axial thickness [cm].
        lower_b10_region_thickness : float
            Complete lower B-10 region axial thickness [cm], including its
            solid lower portion.
        exterior_wall_lower_end_cap_thickness : float
            Solid canister lower-end-cap axial thickness [cm].
        lower_b10_solid_section_thickness : float
            Thickness of the solid lower portion of the B-10 region [cm].
        b10_material : Material
            Material assigned to the enriched-boron regions.
        canister_material : Material, optional
            Material assigned to the canister walls and caps (defaults to
            ``Al6061T6``).
        cadmium_sleeve_material : Material, optional
            Material assigned to the cadmium sleeve (defaults to ``Cd``).
        """

        b10_annulus_inner_radius: float
        upper_b10_outer_radius: float
        lower_b10_outer_radius: float
        canister_exterior_wall_radius: float
        cadmium_sleeve_outer_radius: float
        gap_to_b4c_canister: float
        top_cap_thickness: float
        upper_b10_region_thickness: float
        lower_b10_region_thickness: float
        exterior_wall_lower_end_cap_thickness: float
        lower_b10_solid_section_thickness: float
        b10_material: Material
        canister_material: Material = field(default_factory=Al6061T6)
        cadmium_sleeve_material: Material = field(default_factory=Cd)

        def __post_init__(self) -> None:
            assert self.b10_annulus_inner_radius > 0.0, (
                "B-10 annulus inner radius must be positive."
            )
            assert self.upper_b10_outer_radius > self.b10_annulus_inner_radius, (
                "Upper B-10 outer radius must exceed the annulus inner radius."
            )
            assert self.lower_b10_outer_radius > self.b10_annulus_inner_radius, (
                "Lower B-10 outer radius must exceed the annulus inner radius."
            )
            assert max(self.upper_b10_outer_radius, self.lower_b10_outer_radius) < \
                self.canister_exterior_wall_radius, (
                    "B-10 regions must fit inside the canister exterior wall."
                )
            assert self.canister_exterior_wall_radius < self.cadmium_sleeve_outer_radius, (
                "Cadmium-sleeve outer radius must exceed the canister radius."
            )
            assert self.gap_to_b4c_canister > 0.0, (
                "Gap to the B4C canister must be positive."
            )
            assert self.top_cap_thickness > 0.0, "B-10 top-cap thickness must be positive."
            assert self.upper_b10_region_thickness > 0.0, (
                "Upper B-10 region thickness must be positive."
            )
            assert self.lower_b10_region_thickness > 0.0, (
                "Lower B-10 region thickness must be positive."
            )
            assert self.exterior_wall_lower_end_cap_thickness > 0.0, (
                "Canister exterior-wall lower-end-cap thickness must be positive."
            )
            assert 0.0 < self.lower_b10_solid_section_thickness < \
                self.lower_b10_region_thickness, (
                    "Solid lower B-10 section must be positive and shorter than the lower region."
                )

    @dataclass(frozen=True, eq=False)
    class Disk(TolerantEqualityMixin):
        """Axial filter disk specification.

        Parameters
        ----------
        thickness : float
            Disk axial thickness [cm].
        material : Material
            Material assigned to the disk.
        """

        thickness: float
        material: Material

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Disk thickness must be positive."

    @dataclass(frozen=True, eq=False)
    class HollowSpacer(TolerantEqualityMixin):
        """Hollow aluminum spacer and solid upper-cap specification.

        Parameters
        ----------
        hollow_section_radius : float
            Radius of the air-filled hollow section [cm].
        hollow_section_thickness : float
            Hollow-section axial thickness [cm].
        solid_upper_cap_thickness : float
            Solid upper-cap axial thickness [cm].
        material : Material, optional
            Material assigned to the spacer (defaults to ``Al6061T6``).
        fill_material : Material, optional
            Material filling the hollow section (defaults to ``Air``).
        """

        hollow_section_radius: float
        hollow_section_thickness: float
        solid_upper_cap_thickness: float
        material: Material = field(default_factory=Al6061T6)
        fill_material: Material = field(default_factory=Air)

        def __post_init__(self) -> None:
            assert self.hollow_section_radius > 0.0, (
                "Hollow-spacer radius must be positive."
            )
            assert self.hollow_section_thickness > 0.0, (
                "Hollow-spacer section thickness must be positive."
            )
            assert self.solid_upper_cap_thickness > 0.0, (
                "Hollow-spacer upper-cap thickness must be positive."
            )

    @dataclass(frozen=True, eq=False)
    class SolidSpacer(TolerantEqualityMixin):
        """Solid lower spacer specification.

        Parameters
        ----------
        thickness : float
            Spacer axial thickness [cm].
        material : Material, optional
            Material assigned to the spacer (defaults to ``Al6061T6``).
        """

        thickness: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Solid-spacer thickness must be positive."

    class Pincell(TypedDict):
        """Final pincells for the detailed axial features, named bottom to top.

        Each list contains one pincell unless the Tube #2 lower end splits that
        feature, in which case it contains the below- and above-interface
        pincells in bottom-to-top order.
        """

        bottom_air: List[CylindricalPinCell]
        solid_spacer: List[CylindricalPinCell]
        hollow_spacer: List[CylindricalPinCell]
        hollow_spacer_upper_cap: List[CylindricalPinCell]
        cadmium_disk: List[CylindricalPinCell]
        silver_disk: List[CylindricalPinCell]
        b10_canister_lower_end_cap: List[CylindricalPinCell]
        lower_b10_solid_section: List[CylindricalPinCell]
        b10_interior_wall_lower_cap: List[CylindricalPinCell]
        pneumatic_sleeve_lower_cap: List[CylindricalPinCell]
        pneumatic_tube_lower_cap: List[CylindricalPinCell]
        lower_b10_region: List[CylindricalPinCell]
        upper_b10_region: List[CylindricalPinCell]
        b10_canister_top_cap: List[CylindricalPinCell]
        inter_canister_gap: List[CylindricalPinCell]
        b4c_canister_bottom_cap: List[CylindricalPinCell]
        b4c_region: List[CylindricalPinCell]
        b4c_canister_top_cap: List[CylindricalPinCell]
        outer_casing_solid_upper_end: List[CylindricalPinCell]

    @property
    def outer_casing(self) -> OuterCasing:
        return self._outer_casing

    @property
    def pneumatic_system(self) -> PneumaticSystem:
        return self._pneumatic_system

    @property
    def b4c_canister(self) -> B4CCanister:
        return self._b4c_canister

    @property
    def b10_canister(self) -> B10Canister:
        return self._b10_canister

    @property
    def silver_disk(self) -> Disk:
        return self._silver_disk

    @property
    def cadmium_disk(self) -> Disk:
        return self._cadmium_disk

    @property
    def hollow_spacer(self) -> HollowSpacer:
        return self._hollow_spacer

    @property
    def solid_spacer(self) -> SolidSpacer:
        return self._solid_spacer

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
        """Return the complete outer-casing length [cm]."""
        return self.outer_casing.tube_1_length + self.outer_casing.tube_2_end_cap_thickness

    @property
    def pincell(self) -> Pincell:
        """Return copies of the detailed axial-feature pincell lists."""
        return {
            "bottom_air": list(self._pincell["bottom_air"]),
            "solid_spacer": list(self._pincell["solid_spacer"]),
            "hollow_spacer": list(self._pincell["hollow_spacer"]),
            "hollow_spacer_upper_cap": list(self._pincell["hollow_spacer_upper_cap"]),
            "cadmium_disk": list(self._pincell["cadmium_disk"]),
            "silver_disk": list(self._pincell["silver_disk"]),
            "b10_canister_lower_end_cap": list(self._pincell["b10_canister_lower_end_cap"]),
            "lower_b10_solid_section": list(self._pincell["lower_b10_solid_section"]),
            "b10_interior_wall_lower_cap": list(self._pincell["b10_interior_wall_lower_cap"]),
            "pneumatic_sleeve_lower_cap": list(self._pincell["pneumatic_sleeve_lower_cap"]),
            "pneumatic_tube_lower_cap": list(self._pincell["pneumatic_tube_lower_cap"]),
            "lower_b10_region": list(self._pincell["lower_b10_region"]),
            "upper_b10_region": list(self._pincell["upper_b10_region"]),
            "b10_canister_top_cap": list(self._pincell["b10_canister_top_cap"]),
            "inter_canister_gap": list(self._pincell["inter_canister_gap"]),
            "b4c_canister_bottom_cap": list(self._pincell["b4c_canister_bottom_cap"]),
            "b4c_region": list(self._pincell["b4c_region"]),
            "b4c_canister_top_cap": list(self._pincell["b4c_canister_top_cap"]),
            "outer_casing_solid_upper_end": list(
                self._pincell["outer_casing_solid_upper_end"]
            ),
        }

    @property
    def axial_region_lengths(self) -> Dict[str, List[float]]:
        """Return copies of the detailed axial-feature subdivision lengths.

        Each list aligns one-to-one with the pincells under the corresponding
        key in :attr:`pincell`.
        """
        return {name: list(lengths) for name, lengths in self._axial_region_lengths.items()}

    def __init__(
        self,
        outer_casing: OuterCasing,
        pneumatic_system: PneumaticSystem,
        b4c_canister: B4CCanister,
        b10_canister: B10Canister,
        silver_disk: Disk,
        cadmium_disk: Disk,
        hollow_spacer: HollowSpacer,
        solid_spacer: SolidSpacer,
        fill_material: Optional[Material] = None,
        outer_material: Optional[Material] = None,
        gap_tolerance: Optional[float] = None,
        name: str = "modified_three_element_irradiator",
    ) -> None:
        super().__init__(name)
        if gap_tolerance is not None:
            assert gap_tolerance >= 0.0, (
                "Modified three-element irradiator gap tolerance must be non-negative."
            )

        self._outer_casing = outer_casing
        self._pneumatic_system = pneumatic_system
        self._b4c_canister = b4c_canister
        self._b10_canister = b10_canister
        self._silver_disk = silver_disk
        self._cadmium_disk = cadmium_disk
        self._hollow_spacer = hollow_spacer
        self._solid_spacer = solid_spacer
        self._fill_material = fill_material or Air()
        self._outer_material = outer_material or Water()
        self._gap_tolerance = gap_tolerance

        self._validate_radial_geometry()
        base_lengths = self._calculate_axial_region_lengths()
        base_pincell = self._build_base_pincell()
        self._pincell: ModifiedThreeElementIrradiator.Pincell
        self._axial_region_lengths: Dict[str, List[float]]
        self._pincell, self._axial_region_lengths = self._apply_tube_2(
            base_pincell,
            base_lengths,
        )

    def _validate_radial_geometry(self) -> None:
        casing = self.outer_casing
        pneumatic = self.pneumatic_system
        b4c = self.b4c_canister
        b10 = self.b10_canister

        assert pneumatic.sleeve_outer_radius < b4c.b4c_region_inner_radius, (
            "The pneumatic sleeve must fit inside the B4C canister inner wall."
        )
        assert pneumatic.sleeve_outer_radius < b10.b10_annulus_inner_radius, (
            "The pneumatic sleeve must fit inside the B-10 canister interior wall."
        )
        assert b4c.canister_outer_radius < casing.tube_1_inner_radius, (
            "The B4C canister must fit inside Tube #1."
        )
        assert b10.cadmium_sleeve_outer_radius < casing.tube_1_inner_radius, (
            "The cadmium sleeve must fit inside Tube #1."
        )
        assert self.hollow_spacer.hollow_section_radius < casing.tube_1_inner_radius, (
            "The hollow-section radius must be inside Tube #1."
        )

    def _calculate_axial_region_lengths(self) -> Dict[str, float]:
        casing = self.outer_casing
        pneumatic = self.pneumatic_system
        b4c = self.b4c_canister
        b10 = self.b10_canister

        tube_1_top = casing.tube_1_length
        b4c_bottom = tube_1_top - b4c.length
        b10_top = b4c_bottom - b10.gap_to_b4c_canister
        b10_top_cap_bottom = b10_top - b10.top_cap_thickness
        b10_upper_region_bottom = b10_top_cap_bottom - b10.upper_b10_region_thickness
        b10_lower_region_bottom = b10_upper_region_bottom - b10.lower_b10_region_thickness
        b10_solid_section_top = (b10_lower_region_bottom +
                                 b10.lower_b10_solid_section_thickness)
        b10_bottom = (b10_lower_region_bottom -
                      b10.exterior_wall_lower_end_cap_thickness)

        pneumatic_open_bottom = tube_1_top - pneumatic.open_tube_length
        pneumatic_tube_cap_bottom = (pneumatic_open_bottom -
                                     pneumatic.tube_lower_end_cap_thickness)
        pneumatic_sleeve_cap_bottom = (pneumatic_tube_cap_bottom -
                                       pneumatic.sleeve_lower_end_cap_thickness)
        interior_wall_lower_cap_thickness = (pneumatic_sleeve_cap_bottom -
                                             b10_solid_section_top)

        silver_disk_bottom = b10_bottom - self.silver_disk.thickness
        cadmium_disk_bottom = silver_disk_bottom - self.cadmium_disk.thickness
        hollow_spacer_cap_bottom = (cadmium_disk_bottom -
                                    self.hollow_spacer.solid_upper_cap_thickness)
        hollow_spacer_bottom = (hollow_spacer_cap_bottom -
                                self.hollow_spacer.hollow_section_thickness)
        solid_spacer_bottom = hollow_spacer_bottom - self.solid_spacer.thickness

        assert solid_spacer_bottom > 0.0, (
            "The lower components must leave a positive air region above the facility bottom."
        )
        assert b10_solid_section_top < pneumatic_sleeve_cap_bottom, (
            "The B-10 interior-wall lower cap must have positive thickness."
        )
        assert pneumatic_open_bottom < b10_upper_region_bottom, (
            "The open-pneumatic portion of the lower B-10 region must have positive thickness."
        )

        return {
            "bottom_air": solid_spacer_bottom,
            "solid_spacer": self.solid_spacer.thickness,
            "hollow_spacer": self.hollow_spacer.hollow_section_thickness,
            "hollow_spacer_upper_cap": self.hollow_spacer.solid_upper_cap_thickness,
            "cadmium_disk": self.cadmium_disk.thickness,
            "silver_disk": self.silver_disk.thickness,
            "b10_canister_lower_end_cap": b10.exterior_wall_lower_end_cap_thickness,
            "lower_b10_solid_section": b10.lower_b10_solid_section_thickness,
            "b10_interior_wall_lower_cap": interior_wall_lower_cap_thickness,
            "pneumatic_sleeve_lower_cap": pneumatic.sleeve_lower_end_cap_thickness,
            "pneumatic_tube_lower_cap": pneumatic.tube_lower_end_cap_thickness,
            "lower_b10_region": b10_upper_region_bottom - pneumatic_open_bottom,
            "upper_b10_region": b10.upper_b10_region_thickness,
            "b10_canister_top_cap": b10.top_cap_thickness,
            "inter_canister_gap": b10.gap_to_b4c_canister,
            "b4c_canister_bottom_cap": b4c.bottom_cap_thickness,
            "b4c_region": b4c.b4c_region_thickness,
            "b4c_canister_top_cap": b4c.top_cap_thickness,
            "outer_casing_solid_upper_end": casing.tube_2_end_cap_thickness,
        }

    def _build_base_pincell(self) -> Dict[str, CylindricalPinCell]:
        casing = self.outer_casing
        pneumatic = self.pneumatic_system
        b4c = self.b4c_canister
        b10 = self.b10_canister

        def pincell(
            radii: List[float],
            materials: List[Material],
            suffix: str,
        ) -> CylindricalPinCell:
            return CylindricalPinCell(
                radii=radii,
                materials=materials,
                name=f"{self.name}_{suffix}_pincell",
                min_zone_thickness=self.gap_tolerance,
            )

        def with_casing(
            interior_radii: List[float],
            interior_materials: List[Material],
            suffix: str,
        ) -> CylindricalPinCell:
            assert len(interior_radii) == len(interior_materials)
            assert interior_radii[-1] <= casing.tube_1_inner_radius or isclose(
                interior_radii[-1], casing.tube_1_inner_radius, rel_tol=TOL
            )

            radii = list(interior_radii)
            materials = list(interior_materials)
            if not isclose(radii[-1], casing.tube_1_inner_radius, rel_tol=TOL):
                radii.append(casing.tube_1_inner_radius)
                materials.append(self.fill_material)
            radii.append(casing.tube_1_outer_radius)
            materials.append(casing.material)
            materials.append(self.outer_material)
            return pincell(radii, materials, suffix)

        def open_pneumatic() -> tuple[List[float], List[Material]]:
            return (
                [pneumatic.tube_inner_radius,
                 pneumatic.tube_outer_radius,
                 pneumatic.sleeve_inner_radius,
                 pneumatic.sleeve_outer_radius],
                [pneumatic.fill_material,
                 pneumatic.material,
                 pneumatic.fill_material,
                 pneumatic.material],
            )

        def open_b10(
            b10_outer_radius: float,
            suffix: str,
        ) -> CylindricalPinCell:
            radii, materials = open_pneumatic()
            radii.extend([
                b10.b10_annulus_inner_radius,
                b10_outer_radius,
                b10.canister_exterior_wall_radius,
                b10.cadmium_sleeve_outer_radius,
            ])
            materials.extend([
                b10.canister_material,
                b10.b10_material,
                b10.canister_material,
                b10.cadmium_sleeve_material,
            ])
            return with_casing(radii, materials, suffix)

        regions: Dict[str, CylindricalPinCell] = {}
        regions["bottom_air"] = with_casing(
            [casing.tube_1_inner_radius],
            [self.fill_material],
            "bottom_air",
        )
        regions["solid_spacer"] = with_casing(
            [casing.tube_1_inner_radius],
            [self.solid_spacer.material],
            "solid_spacer",
        )
        regions["hollow_spacer"] = with_casing(
            [self.hollow_spacer.hollow_section_radius, casing.tube_1_inner_radius],
            [self.hollow_spacer.fill_material, self.hollow_spacer.material],
            "hollow_spacer",
        )
        regions["hollow_spacer_upper_cap"] = with_casing(
            [casing.tube_1_inner_radius],
            [self.hollow_spacer.material],
            "hollow_spacer_upper_cap",
        )
        regions["cadmium_disk"] = with_casing(
            [casing.tube_1_inner_radius],
            [self.cadmium_disk.material],
            "cadmium_disk",
        )
        regions["silver_disk"] = with_casing(
            [casing.tube_1_inner_radius],
            [self.silver_disk.material],
            "silver_disk",
        )
        regions["b10_canister_lower_end_cap"] = with_casing(
            [b10.canister_exterior_wall_radius],
            [b10.canister_material],
            "b10_canister_lower_end_cap",
        )
        regions["lower_b10_solid_section"] = with_casing(
            [b10.lower_b10_outer_radius,
             b10.canister_exterior_wall_radius,
             b10.cadmium_sleeve_outer_radius],
            [b10.b10_material, b10.canister_material, b10.cadmium_sleeve_material],
            "lower_b10_solid_section",
        )
        regions["b10_interior_wall_lower_cap"] = with_casing(
            [b10.b10_annulus_inner_radius,
             b10.lower_b10_outer_radius,
             b10.canister_exterior_wall_radius,
             b10.cadmium_sleeve_outer_radius],
            [b10.canister_material, b10.b10_material,
             b10.canister_material, b10.cadmium_sleeve_material],
            "b10_interior_wall_lower_cap",
        )
        regions["pneumatic_sleeve_lower_cap"] = with_casing(
            [pneumatic.sleeve_outer_radius,
             b10.b10_annulus_inner_radius,
             b10.lower_b10_outer_radius,
             b10.canister_exterior_wall_radius,
             b10.cadmium_sleeve_outer_radius],
            [pneumatic.material, b10.canister_material, b10.b10_material,
             b10.canister_material, b10.cadmium_sleeve_material],
            "pneumatic_sleeve_lower_cap",
        )
        regions["pneumatic_tube_lower_cap"] = with_casing(
            [pneumatic.tube_outer_radius,
             pneumatic.sleeve_inner_radius,
             pneumatic.sleeve_outer_radius,
             b10.b10_annulus_inner_radius,
             b10.lower_b10_outer_radius,
             b10.canister_exterior_wall_radius,
             b10.cadmium_sleeve_outer_radius],
            [pneumatic.material, pneumatic.fill_material,
             pneumatic.material, b10.canister_material, b10.b10_material,
             b10.canister_material, b10.cadmium_sleeve_material],
            "pneumatic_tube_lower_cap",
        )
        regions["lower_b10_region"] = open_b10(
            b10.lower_b10_outer_radius,
            "lower_b10_region",
        )
        regions["upper_b10_region"] = open_b10(
            b10.upper_b10_outer_radius,
            "upper_b10_region",
        )

        pneumatic_radii, pneumatic_materials = open_pneumatic()
        regions["b10_canister_top_cap"] = with_casing(
            pneumatic_radii + [b10.canister_exterior_wall_radius,
                               b10.cadmium_sleeve_outer_radius],
            pneumatic_materials + [b10.canister_material,
                                   b10.cadmium_sleeve_material],
            "b10_canister_top_cap",
        )
        regions["inter_canister_gap"] = with_casing(
            pneumatic_radii,
            pneumatic_materials,
            "inter_canister_gap",
        )
        regions["b4c_canister_bottom_cap"] = with_casing(
            pneumatic_radii + [b4c.canister_outer_radius],
            pneumatic_materials + [b4c.canister_material],
            "b4c_canister_bottom_cap",
        )
        regions["b4c_region"] = with_casing(
            pneumatic_radii + [b4c.b4c_region_inner_radius,
                               b4c.b4c_region_outer_radius,
                               b4c.canister_outer_radius],
            pneumatic_materials + [b4c.canister_material,
                                   b4c.b4c_material,
                                   b4c.canister_material],
            "b4c_region",
        )
        regions["b4c_canister_top_cap"] = with_casing(
            pneumatic_radii + [b4c.canister_outer_radius],
            pneumatic_materials + [b4c.canister_material],
            "b4c_canister_top_cap",
        )
        regions["outer_casing_solid_upper_end"] = pincell(
            [casing.tube_2_outer_radius],
            [casing.material, self.outer_material],
            "outer_casing_solid_upper_end",
        )
        return {
            "bottom_air": regions["bottom_air"],
            "solid_spacer": regions["solid_spacer"],
            "hollow_spacer": regions["hollow_spacer"],
            "hollow_spacer_upper_cap": regions["hollow_spacer_upper_cap"],
            "cadmium_disk": regions["cadmium_disk"],
            "silver_disk": regions["silver_disk"],
            "b10_canister_lower_end_cap": regions["b10_canister_lower_end_cap"],
            "lower_b10_solid_section": regions["lower_b10_solid_section"],
            "b10_interior_wall_lower_cap": regions["b10_interior_wall_lower_cap"],
            "pneumatic_sleeve_lower_cap": regions["pneumatic_sleeve_lower_cap"],
            "pneumatic_tube_lower_cap": regions["pneumatic_tube_lower_cap"],
            "lower_b10_region": regions["lower_b10_region"],
            "upper_b10_region": regions["upper_b10_region"],
            "b10_canister_top_cap": regions["b10_canister_top_cap"],
            "inter_canister_gap": regions["inter_canister_gap"],
            "b4c_canister_bottom_cap": regions["b4c_canister_bottom_cap"],
            "b4c_region": regions["b4c_region"],
            "b4c_canister_top_cap": regions["b4c_canister_top_cap"],
            "outer_casing_solid_upper_end": regions["outer_casing_solid_upper_end"],
        }

    def _build_tube_2_pincell(self, pincell: CylindricalPinCell) -> CylindricalPinCell:
        """Return a copy of a Tube #1 cross section surrounded by Tube #2."""

        radii = [zone.shape.outer_radius for zone in pincell.zones]
        materials = [zone.material for zone in pincell.zones]
        radii.append(self.outer_casing.tube_2_outer_radius)
        materials.extend([self.outer_casing.material, pincell.outer_material])
        return CylindricalPinCell(
            radii=radii,
            materials=materials,
            name=f"{pincell.name}_with_tube_2",
            x0=pincell.x0,
            y0=pincell.y0,
            min_zone_thickness=self.gap_tolerance,
        )

    def _apply_tube_2(
        self,
        base_pincell: Dict[str, CylindricalPinCell],
        base_lengths: Dict[str, float],
    ) -> tuple[Pincell, Dict[str, List[float]]]:
        """Apply Tube #2 to the base axial features at initialization."""

        tube_2_bottom = self.outer_casing.tube_1_length - self.outer_casing.tube_2_annulus_length
        pincells: Dict[str, List[CylindricalPinCell]] = {}
        lengths: Dict[str, List[float]] = {}
        feature_bottom = 0.0
        for name, base_feature_pincell in base_pincell.items():
            if name == "outer_casing_solid_upper_end":
                continue
            base_feature_length = base_lengths[name]
            feature_top = feature_bottom + base_feature_length
            if feature_top < tube_2_bottom or isclose(feature_top, tube_2_bottom, rel_tol=TOL):
                pincells[name] = [base_feature_pincell]
                lengths[name] = [base_feature_length]
            elif feature_bottom > tube_2_bottom or isclose(
                feature_bottom, tube_2_bottom, rel_tol=TOL
            ):
                pincells[name] = [self._build_tube_2_pincell(base_feature_pincell)]
                lengths[name] = [base_feature_length]
            else:
                pincells[name] = [
                    base_feature_pincell,
                    self._build_tube_2_pincell(base_feature_pincell),
                ]
                lengths[name] = [
                    tube_2_bottom - feature_bottom,
                    feature_top - tube_2_bottom,
                ]
            feature_bottom = feature_top

        pincells["outer_casing_solid_upper_end"] = [
            base_pincell["outer_casing_solid_upper_end"]
        ]
        lengths["outer_casing_solid_upper_end"] = [
            base_lengths["outer_casing_solid_upper_end"]
        ]

        return {
            "bottom_air": pincells["bottom_air"],
            "solid_spacer": pincells["solid_spacer"],
            "hollow_spacer": pincells["hollow_spacer"],
            "hollow_spacer_upper_cap": pincells["hollow_spacer_upper_cap"],
            "cadmium_disk": pincells["cadmium_disk"],
            "silver_disk": pincells["silver_disk"],
            "b10_canister_lower_end_cap": pincells["b10_canister_lower_end_cap"],
            "lower_b10_solid_section": pincells["lower_b10_solid_section"],
            "b10_interior_wall_lower_cap": pincells["b10_interior_wall_lower_cap"],
            "pneumatic_sleeve_lower_cap": pincells["pneumatic_sleeve_lower_cap"],
            "pneumatic_tube_lower_cap": pincells["pneumatic_tube_lower_cap"],
            "lower_b10_region": pincells["lower_b10_region"],
            "upper_b10_region": pincells["upper_b10_region"],
            "b10_canister_top_cap": pincells["b10_canister_top_cap"],
            "inter_canister_gap": pincells["inter_canister_gap"],
            "b4c_canister_bottom_cap": pincells["b4c_canister_bottom_cap"],
            "b4c_region": pincells["b4c_region"],
            "b4c_canister_top_cap": pincells["b4c_canister_top_cap"],
            "outer_casing_solid_upper_end": pincells["outer_casing_solid_upper_end"],
        }, lengths

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, ModifiedThreeElementIrradiator):
            return False
        return (
            self.outer_casing == other.outer_casing and
            self.pneumatic_system == other.pneumatic_system and
            self.b4c_canister == other.b4c_canister and
            self.b10_canister == other.b10_canister and
            self.silver_disk == other.silver_disk and
            self.cadmium_disk == other.cadmium_disk and
            self.hollow_spacer == other.hollow_spacer and
            self.solid_spacer == other.solid_spacer and
            self.fill_material == other.fill_material and
            self.outer_material == other.outer_material and
            ((self.gap_tolerance is None and other.gap_tolerance is None) or
             (self.gap_tolerance is not None and other.gap_tolerance is not None and
              isclose(self.gap_tolerance, other.gap_tolerance, rel_tol=TOL)))
        )

    def __hash__(self) -> int:
        return hash((
            self.outer_casing,
            self.pneumatic_system,
            self.b4c_canister,
            self.b10_canister,
            self.silver_disk,
            self.cadmium_disk,
            self.hollow_spacer,
            self.solid_spacer,
            self.fill_material,
            self.outer_material,
            None if self.gap_tolerance is None else relative_round(self.gap_tolerance, TOL),
        ))

    def get_materials(self) -> List[Material]:
        return unique_materials([
            self.outer_casing.material,
            self.pneumatic_system.material,
            self.pneumatic_system.fill_material,
            self.b4c_canister.b4c_material,
            self.b4c_canister.canister_material,
            self.b10_canister.b10_material,
            self.b10_canister.canister_material,
            self.b10_canister.cadmium_sleeve_material,
            self.silver_disk.material,
            self.cadmium_disk.material,
            self.hollow_spacer.material,
            self.hollow_spacer.fill_material,
            self.solid_spacer.material,
            self.fill_material,
            self.outer_material,
        ])

    def as_stack(self, bottom_pos: float = 0.0) -> CylindricalStack:
        """Return the detailed irradiator as a bottom-to-top cylindrical stack.

        Parameters
        ----------
        bottom_pos : float, optional
            Axial position of the facility bottom [cm]. Defaults to 0.0.
        """

        pincell = self.pincell
        lengths = self.axial_region_lengths
        segments: List[Stack.Segment] = []

        def extend(
            region_pincells: List[CylindricalPinCell],
            region_lengths: List[float],
        ) -> None:
            assert len(region_pincells) == len(region_lengths)
            segments.extend(
                Stack.Segment(region_pincell, region_length)
                for region_pincell, region_length in zip(region_pincells, region_lengths)
            )

        extend(pincell["bottom_air"], lengths["bottom_air"])
        extend(pincell["solid_spacer"], lengths["solid_spacer"])
        extend(pincell["hollow_spacer"], lengths["hollow_spacer"])
        extend(pincell["hollow_spacer_upper_cap"], lengths["hollow_spacer_upper_cap"])
        extend(pincell["cadmium_disk"], lengths["cadmium_disk"])
        extend(pincell["silver_disk"], lengths["silver_disk"])
        extend(pincell["b10_canister_lower_end_cap"], lengths["b10_canister_lower_end_cap"])
        extend(pincell["lower_b10_solid_section"], lengths["lower_b10_solid_section"])
        extend(pincell["b10_interior_wall_lower_cap"], lengths["b10_interior_wall_lower_cap"])
        extend(pincell["pneumatic_sleeve_lower_cap"], lengths["pneumatic_sleeve_lower_cap"])
        extend(pincell["pneumatic_tube_lower_cap"], lengths["pneumatic_tube_lower_cap"])
        extend(pincell["lower_b10_region"], lengths["lower_b10_region"])
        extend(pincell["upper_b10_region"], lengths["upper_b10_region"])
        extend(pincell["b10_canister_top_cap"], lengths["b10_canister_top_cap"])
        extend(pincell["inter_canister_gap"], lengths["inter_canister_gap"])
        extend(pincell["b4c_canister_bottom_cap"], lengths["b4c_canister_bottom_cap"])
        extend(pincell["b4c_region"], lengths["b4c_region"])
        extend(pincell["b4c_canister_top_cap"], lengths["b4c_canister_top_cap"])
        extend(
            pincell["outer_casing_solid_upper_end"],
            lengths["outer_casing_solid_upper_end"],
        )

        return CylindricalStack(
            segments=segments,
            name=self.name,
            bottom_pos=bottom_pos,
        )

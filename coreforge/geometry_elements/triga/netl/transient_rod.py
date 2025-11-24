from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Air, Al6061T6, B4C, Material, Water


class TransientRod:
    """TRIGA NETL transient rod definitions and pincell builders.

    Provides feature specifications (cladding, absorber, air follower) and nested
    pincells for the absorber and air-follower regions.
    """

    @dataclass(frozen=True)
    class Cladding:
        """Transient rod cladding specification.

        Parameters
        ----------
        thickness : float
            Cladding thickness [cm].
        outer_radius : float
            Cladding outer radius [cm].
        material : Material, optional
            Cladding material. Defaults to ``Al6061T6``.
        """
        thickness: float
        outer_radius: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Cladding thickness must be positive."
            assert self.outer_radius > self.thickness, (
                "Cladding outer radius must exceed thickness."
            )

    @dataclass(frozen=True)
    class Absorber:
        """Transient rod absorber specification.

        Parameters
        ----------
        radius : float
            Radius of the absorber [cm].
        material : Material, optional
            Absorber material. Defaults to ``B4C``.
        """
        radius: float
        material: Material = field(default_factory=B4C)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Absorber radius must be positive."

    class AbsorberPincell(CylindricalPinCell):
        """Absorber region pincell with concentric cladding.

        Parameters
        ----------
        cladding : TransientRod.Cladding
            Cladding definition with thickness, outer radius, and material.
        absorber : TransientRod.Absorber
            Absorber definition with radius and material.
        fill_gas : Material, optional
            Material filling any gap between absorber and cladding. Defaults to ``Air``.
        outer_material : Material, optional
            Coolant/exterior material outside the cladding. Defaults to ``Water``.
        name : str, optional
            Name for this pincell instance.
        """

        GAP_TOL = 1.0e-8

        @property
        def cladding(self) -> TransientRod.Cladding:
            return self._cladding

        @property
        def absorber(self) -> TransientRod.Absorber:
            return self._absorber

        @property
        def fill_gas(self) -> Material:
            return self._fill_gas

        @property
        def coolant(self) -> Material:
            return self._outer_material

        def __init__(
            self,
            cladding: TransientRod.Cladding,
            absorber: TransientRod.Absorber,
            fill_gas: Optional[Material] = None,
            outer_material: Optional[Material] = None,
            name: str = "triga_netl_transient_rod_absorber",
        ):
            self._cladding = cladding
            self._absorber = absorber
            self._fill_gas = fill_gas or Air()
            self._outer_material = outer_material or Water()

            radii, materials = self._build_radial_profile()
            super().__init__(radii=radii, materials=materials, name=name)

        def _build_radial_profile(self) -> tuple[List[float], List[Material]]:
            """Construct ordered radial boundaries and materials.

            Gaps are only added if wider than GAP_TOL; otherwise adjacent regions
            are considered in hard contact (prevents near-duplicate radii).

            Returns
            -------
            radii : List[float]
                Monotonic list of region outer radii from innermost to outermost solid.
            materials : List[Material]
                Materials aligned with ``radii`` plus the final outer/coolant material.
            """
            cladding_inner_radius = self.cladding.outer_radius - self.cladding.thickness
            assert self.absorber.radius < cladding_inner_radius + self.GAP_TOL, (
                "Absorber must be inside the cladding."
            )

            radii: List[float] = []
            materials: List[Material] = []

            def append_region(radius: float, material: Material) -> None:
                if radii:
                    assert radius - radii[-1] > self.GAP_TOL, (
                        "Region radii must be strictly increasing."
                    )
                radii.append(radius)
                materials.append(material)

            append_region(self.absorber.radius, self.absorber.material)

            gap_to_cladding = cladding_inner_radius - self.absorber.radius
            if gap_to_cladding > self.GAP_TOL:
                append_region(cladding_inner_radius, self.fill_gas)

            append_region(self.cladding.outer_radius, self.cladding.material)
            materials.append(self.coolant)
            return radii, materials

    class AirFollowerPincell(CylindricalPinCell):
        """Air follower region pincell with concentric cladding.

        Uses the cladding inner radius as the air-follower radius.

        Parameters
        ----------
        cladding : TransientRod.Cladding
            Cladding definition with thickness, outer radius, and material.
        fill_gas : Material, optional
            Material filling the air follower region. Defaults to ``Air``.
        outer_material : Material, optional
            Material surrounding the cladding exterior. Defaults to ``Water``.
        name : str, optional
            Name for this pincell instance.
        """

        GAP_TOL = 1.0e-8

        @property
        def cladding(self) -> TransientRod.Cladding:
            return self._cladding

        @property
        def fill_gas(self) -> Material:
            return self._fill_gas

        @property
        def coolant(self) -> Material:
            return self._outer_material

        def __init__(
            self,
            cladding: TransientRod.Cladding,
            fill_gas: Optional[Material] = None,
            outer_material: Optional[Material] = None,
            name: str = "triga_netl_transient_rod_air_follower",
        ):
            self._cladding = cladding
            self._fill_gas = fill_gas or Air()
            self._outer_material = outer_material or Water()

            radii, materials = self._build_radial_profile()
            super().__init__(radii=radii, materials=materials, name=name)

        def _build_radial_profile(self) -> tuple[List[float], List[Material]]:
            """Construct ordered radial boundaries and materials.

            Returns
            -------
            radii : List[float]
                Monotonic list of region outer radii from innermost to outermost solid.
            materials : List[Material]
                Materials aligned with ``radii`` plus the final outer/coolant material.
            """
            cladding_inner_radius = self.cladding.outer_radius - self.cladding.thickness
            assert cladding_inner_radius > 0.0, "Cladding inner radius must be positive."

            radii: List[float] = []
            materials: List[Material] = []

            def append_region(radius: float, material: Material) -> None:
                if radii:
                    assert radius - radii[-1] > self.GAP_TOL, (
                        "Region radii must be strictly increasing."
                    )
                radii.append(radius)
                materials.append(material)

            append_region(cladding_inner_radius, self.fill_gas)
            append_region(self.cladding.outer_radius, self.cladding.material)
            materials.append(self.coolant)
            return radii, materials

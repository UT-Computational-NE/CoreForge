from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Air, B4C, Material, SS304, UZrH, Water, Zr


class FuelFollowerControlRod:
    """TRIGA NETL fuel-follower control rod definitions and pincell builders.

    Provides feature specifications (cladding, absorber, follower fuel, Zr fill rod)
    and nested pincells for the absorber region and the fuel-follower region.
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
            Cladding material. Defaults to ``SS304``.
        """
        thickness: float
        outer_radius: float
        material: Material = field(default_factory=SS304)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Cladding thickness must be positive."
            assert self.outer_radius > self.thickness, (
                "Cladding outer radius must exceed thickness."
            )

    @dataclass(frozen=True)
    class Absorber:
        """Absorber specification.

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

    @dataclass(frozen=True)
    class FuelFollower:
        """Fuel follower specification.

        Parameters
        ----------
        inner_radius : float
            Inner radius of the fuel follower [cm].
        outer_radius : float
            Outer radius of the fuel follower [cm].
        material : Material, optional
            Fuel material. Defaults to ``UZrH``.
        """
        inner_radius: float
        outer_radius: float
        material: Material = field(default_factory=UZrH)

        def __post_init__(self) -> None:
            assert self.inner_radius > 0.0, "Fuel follower inner radius must be positive."
            assert self.outer_radius > self.inner_radius, "Fuel follower outer radius must exceed inner radius."

    @dataclass(frozen=True)
    class ZrFillRod:
        """Zr fill rod specification inside the fuel follower."""
        radius: float
        material: Material = field(default_factory=Zr)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Zr Fill Rod radius must be positive."

    class AbsorberPincell(CylindricalPinCell):
        """Absorber region pincell with concentric cladding.

        Parameters
        ----------
        cladding : FuelFollowerControlRod.Cladding
            Cladding definition with thickness, outer radius, and material.
        absorber : FuelFollowerControlRod.Absorber
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
        def cladding(self) -> FuelFollowerControlRod.Cladding:
            return self._cladding

        @property
        def absorber(self) -> FuelFollowerControlRod.Absorber:
            return self._absorber

        @property
        def fill_gas(self) -> Material:
            return self._fill_gas

        @property
        def coolant(self) -> Material:
            return self._outer_material

        def __init__(
            self,
            cladding: FuelFollowerControlRod.Cladding,
            absorber: FuelFollowerControlRod.Absorber,
            fill_gas: Optional[Material] = None,
            outer_material: Optional[Material] = None,
            name: str = "triga_netl_ffcr_absorber",
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

    class FuelFollowerPincell(CylindricalPinCell):
        """Fuel-follower region pincell with Zr rod and concentric cladding.

        Parameters
        ----------
        cladding : FuelFollowerControlRod.Cladding
            Cladding definition with thickness, outer radius, and material.
        fuel_follower : FuelFollowerControlRod.FuelFollower
            Fuel follower definition with inner radius and material.
        zr_fill_rod : FuelFollowerControlRod.ZrFillRod
            Zr fill rod definition with radius and material.
        fill_gas : Material, optional
            Material filling any gap between Zr rod and fuel follower. Defaults to ``Air``.
        outer_material : Material, optional
            Coolant/exterior material outside the cladding. Defaults to ``Water``.
        name : str, optional
            Name for this pincell instance.
        """

        GAP_TOL = 1.0e-8

        @property
        def cladding(self) -> FuelFollowerControlRod.Cladding:
            return self._cladding

        @property
        def fuel_follower(self) -> FuelFollowerControlRod.FuelFollower:
            return self._fuel_follower

        @property
        def zr_fill_rod(self) -> FuelFollowerControlRod.ZrFillRod:
            return self._zr_fill_rod

        @property
        def fill_gas(self) -> Material:
            return self._fill_gas

        @property
        def coolant(self) -> Material:
            return self._outer_material

        def __init__(
            self,
            cladding: FuelFollowerControlRod.Cladding,
            fuel_follower: FuelFollowerControlRod.FuelFollower,
            zr_fill_rod: FuelFollowerControlRod.ZrFillRod,
            fill_gas: Optional[Material] = None,
            outer_material: Optional[Material] = None,
            name: str = "triga_netl_ffcr_fuel_follower",
        ):
            self._cladding = cladding
            self._fuel_follower = fuel_follower
            self._zr_fill_rod = zr_fill_rod
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
            assert self.zr_fill_rod.radius < self.fuel_follower.inner_radius + self.GAP_TOL, (
                "Zr fill rod must not exceed follower inner radius."
            )
            assert self.fuel_follower.outer_radius < cladding_inner_radius + self.GAP_TOL, (
                "Follower must be inside the cladding."
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

            append_region(self.zr_fill_rod.radius, self.zr_fill_rod.material)

            gap_to_fuel = self.fuel_follower.inner_radius - self.zr_fill_rod.radius
            if gap_to_fuel > self.GAP_TOL:
                append_region(self.fuel_follower.inner_radius, self.fill_gas)

            append_region(self.fuel_follower.outer_radius, self.fuel_follower.material)

            gap_to_cladding = cladding_inner_radius - self.fuel_follower.outer_radius
            if gap_to_cladding > self.GAP_TOL:
                append_region(cladding_inner_radius, self.fill_gas)

            append_region(self.cladding.outer_radius, self.cladding.material)
            materials.append(self.coolant)
            return radii, materials

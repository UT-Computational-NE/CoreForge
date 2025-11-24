from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Air, Material, SS304, UZrH, Water, Zr


class FuelElementPincell(CylindricalPinCell):
    """TRIGA fuel element pincell with concentric radial features.

    Parameters
    ----------
    cladding : FuelElementPincell.Cladding
        Cladding definition with thickness, outer radius, and material.
    fuel_meat : FuelElementPincell.FuelMeat
        Fuel meat definition with inner/outer radii and material.
    zr_fill_rod : FuelElementPincell.ZrFillRod
        Zirconium fill rod definition with radius and material.
    fill_gas : Material, optional
        Material used to fill any gaps between solid regions. Defaults to ``Air``.
    outer_material : Material, optional
        Coolant or exterior material surrounding the cladding. Defaults to ``Water``.
    name : str, optional
        Name for this pincell instance.
    """

    # Gaps thinner than GAP_TOL are treated as zero and omitted from the region list.
    GAP_TOL = 1.0e-8

    @dataclass(frozen=True)
    class ZrFillRod:
        """Zirconium fill rod specification.

        Parameters
        ----------
        radius : float
            Radius of the Zr fill rod [cm].
        material : Material, optional
            Material filling the rod. Defaults to ``Zr``.
        """
        radius: float
        material: Material = field(default_factory=Zr)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Zr Fill Rod radius must be positive."

    @dataclass(frozen=True)
    class FuelMeat:
        """Fuel meat specification.

        Parameters
        ----------
        inner_radius : float
            Inner radius of the fuel meat [cm].
        outer_radius : float
            Outer radius of the fuel meat [cm].
        material : Material, optional
            Fuel material. Defaults to ``UZrH``.
        """
        inner_radius: float
        outer_radius: float
        material: Material = field(default_factory=UZrH)

        def __post_init__(self) -> None:
            assert self.inner_radius > 0.0, "Fuel Meat inner radius must be positive."
            assert self.outer_radius > self.inner_radius, (
                "Fuel Meat outer radius must exceed inner radius."
            )

    @dataclass(frozen=True)
    class Cladding:
        """Cladding specification.

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

    def __init__(
        self,
        cladding: Cladding,
        fuel_meat: FuelMeat,
        zr_fill_rod: ZrFillRod,
        fill_gas: Optional[Material] = None,
        outer_material: Optional[Material] = None,
        name: str = "triga_fuel_element",
    ):
        self._cladding = cladding
        self._fuel_meat = fuel_meat
        self._zr_fill_rod = zr_fill_rod
        self._fill_gas = fill_gas or Air()
        self._outer_material = outer_material or Water()

        radii, materials = self._build_radial_profile()
        super().__init__(radii=radii, materials=materials, name=name)

    @property
    def cladding(self) -> Cladding:
        return self._cladding

    @property
    def fuel_meat(self) -> FuelMeat:
        return self._fuel_meat

    @property
    def zr_fill_rod(self) -> ZrFillRod:
        return self._zr_fill_rod

    @property
    def fill_gas(self) -> Material:
        return self._fill_gas

    @property
    def coolant(self) -> Material:
        return self._outer_material

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
        assert self.zr_fill_rod.radius < self.fuel_meat.outer_radius, (
            "Zr Fill Rod must be inside fuel meat."
        )
        assert self.fuel_meat.outer_radius < cladding_inner_radius + self.GAP_TOL, (
            "Fuel meat outer radius must be inside the cladding."
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

        # Gaps are only added if wider than GAP_TOL; otherwise the adjacent regions
        # are considered in hard contact (prevents near-duplicate radii).
        gap_to_fuel = self.fuel_meat.inner_radius - self.zr_fill_rod.radius
        if gap_to_fuel > self.GAP_TOL:
            append_region(self.fuel_meat.inner_radius, self.fill_gas)

        append_region(self.fuel_meat.outer_radius, self.fuel_meat.material)

        gap_to_cladding = cladding_inner_radius - self.fuel_meat.outer_radius
        if gap_to_cladding > self.GAP_TOL:
            append_region(cladding_inner_radius, self.fill_gas)

        append_region(self.cladding.outer_radius, self.cladding.material)

        materials.append(self.coolant)
        return radii, materials

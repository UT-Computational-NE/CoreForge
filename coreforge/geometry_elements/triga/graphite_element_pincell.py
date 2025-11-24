from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Air, Al6061T6, Graphite, Material, Water


class GraphiteElementPincell(CylindricalPinCell):
    """TRIGA graphite element pincell with concentric radial features.

    Gaps are only added if wider than GAP_TOL; otherwise the adjacent regions
    are considered in hard contact (prevents near-duplicate radii).

    Parameters
    ----------
    cladding : GraphiteElementPincell.Cladding
        Cladding definition with thickness, outer radius, and material.
    graphite_meat : GraphiteElementPincell.GraphiteMeat
        Graphite meat definition with outer radius and material.
    fill_gas : Material, optional
        Material used to fill any gaps between solid regions. Defaults to ``Air``.
    outer_material : Material, optional
        Coolant or exterior material surrounding the cladding. Defaults to ``Water``.
    name : str, optional
        Name for this pincell instance.

    References
    ----------
    .. [1] D. R. Redhouse, et al., "Radiation Characterization Summary: NETL Beam Port
           1/5 Free-Field Environment at the 128-inch Core Centerline Adjacent Location,
           (NETL-FF-BP1/5-128-cca).", Nov. 2022. https://doi.org/10.2172/1898256
    """

    # Gaps thinner than GAP_TOL are treated as zero and omitted from the region list.
    GAP_TOL = 1.0e-8

    @dataclass(frozen=True)
    class GraphiteMeat:
        """Graphite meat specification.

        Parameters
        ----------
        outer_radius : float
            Outer radius of the graphite meat [cm].
        material : Material, optional
            Graphite material. Defaults to ``Graphite`` at 1.6 g/cc (Ref. [1]_ pg. 50).
        """
        outer_radius: float
        material: Material = field(default_factory=lambda: Graphite(graphite_density=1.6))

        def __post_init__(self) -> None:
            assert self.outer_radius > 0.0, "Graphite Meat outer radius must be positive."

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
            Cladding material. Defaults to ``Al6061T6``.
        """
        thickness: float
        outer_radius: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Cladding thickness must be positive."
            assert self.outer_radius > self.thickness, (
                "Cladding outer radius must exceed thickness.")

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
    def coolant(self) -> Material:
        return self._outer_material

    def __init__(self,
                 cladding:       Cladding,
                 graphite_meat:  GraphiteMeat,
                 fill_gas:       Optional[Material] = None,
                 outer_material: Optional[Material] = None,
                 name:           str = "triga_graphite_element"):

        self._cladding       = cladding
        self._graphite_meat  = graphite_meat
        self._fill_gas       = fill_gas or Air()
        self._outer_material = outer_material or Water()

        radii, materials = self._build_radial_profile()
        super().__init__(radii=radii, materials=materials, name=name)

    def _build_radial_profile(self) -> tuple[List[float], List[Material]]:
        """Construct ordered radial boundaries and materials.

        Gaps are only added if wider than GAP_TOL; otherwise the adjacent regions
        are considered in hard contact (prevents near-duplicate radii)

        Returns
        -------
        radii : List[float]
            Monotonic list of region outer radii from innermost to outermost solid.
        materials : List[Material]
            Materials aligned with ``radii`` plus the final outer/coolant material.
        """
        cladding_inner_radius = self.cladding.outer_radius - self.cladding.thickness
        assert self.graphite_meat.outer_radius < cladding_inner_radius + self.GAP_TOL, (
            "Graphite meat outer radius must be inside the cladding."
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

        append_region(self.graphite_meat.outer_radius, self.graphite_meat.material)

        gap_to_cladding = cladding_inner_radius - self.graphite_meat.outer_radius
        if gap_to_cladding > self.GAP_TOL:
            append_region(cladding_inner_radius, self.fill_gas)

        append_region(self.cladding.outer_radius, self.cladding.material)

        materials.append(self.coolant)
        return radii, materials

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Air, Al6061T6, Material, Water


class SourceHolder:
    """TRIGA NETL source holder definitions and cavity pincell builder.

    The pincell represents only the cavity region (fill + cladding), not axial
    positioning; axial length/offset can be added later.

    References
    ----------
    .. [1] D. R. Redhouse, et al., "Radiation Characterization Summary: NETL Beam Port
           1/5 Free-Field Environment at the 128-inch Core Centerline Adjacent Location,
           (NETL-FF-BP1/5-128-cca).", Nov. 2022. https://doi.org/10.2172/1898256
    """

    @dataclass(frozen=True)
    class Cavity:
        """Source holder cavity specification.

        Parameters
        ----------
        radius : float
            Radius of the cavity [cm].
        material : Material, optional
            Material filling the cavity. Defaults to ``Air``.
        """
        radius: float
        material: Material = field(default_factory=Air)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Source Holder Cavity radius must be positive."

    @dataclass(frozen=True)
    class Cladding:
        """Source holder cladding specification.

        Parameters
        ----------
        outer_radius : float
            Outer radius of the source holder cladding [cm].
        material : Material, optional
            Cladding material. Defaults to ``Al6061T6``.
        """
        outer_radius: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.outer_radius > 0.0, "Source Holder Cladding outer radius must be positive."

    class Pincell(CylindricalPinCell):
        """Source holder cavity pincell.

        Parameters
        ----------
        cavity : SourceHolder.Cavity
            Cavity definition (radius and material).
        cladding : SourceHolder.Cladding
            Cladding definition (outer radius and material).
        outer_material : Material, optional
            Material surrounding the cladding exterior. Defaults to ``Water``.
        name : str, optional
            Name for this pincell instance.
        """

        GAP_TOL = 1.0e-8

        @property
        def cavity(self) -> SourceHolder.Cavity:
            return self._cavity

        @property
        def cladding(self) -> SourceHolder.Cladding:
            return self._cladding

        @property
        def coolant(self) -> Material:
            return self._outer_material

        def __init__(
            self,
            cavity: SourceHolder.Cavity,
            cladding: SourceHolder.Cladding,
            outer_material: Optional[Material] = None,
            name: str = "triga_netl_source_holder_cavity",
        ):
            self._cavity = cavity
            self._cladding = cladding
            self._outer_material = outer_material or Water()

            radii, materials = self._build_radial_profile()
            super().__init__(radii=radii, materials=materials, name=name)

        def _build_radial_profile(self) -> tuple[List[float], List[Material]]:
            """Construct ordered radial boundaries and materials.

            Assumes the cavity is immediately adjacent to the cladding (no explicit gap).

            Returns
            -------
            radii : List[float]
                Monotonic list of region outer radii from innermost to outermost solid.
            materials : List[Material]
                Materials aligned with ``radii`` plus the final outer/coolant material.
            """
            radii: List[float] = []
            materials: List[Material] = []

            def append_region(radius: float, material: Material) -> None:
                if radii:
                    assert radius - radii[-1] > self.GAP_TOL, (
                        "Region radii must be strictly increasing."
                    )
                radii.append(radius)
                materials.append(material)

            append_region(self.cavity.radius, self.cavity.material)
            append_region(self.cladding.outer_radius, self.cladding.material)

            materials.append(self.coolant)
            return radii, materials

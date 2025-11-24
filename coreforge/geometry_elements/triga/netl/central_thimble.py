from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Al6061T6, Material, Water


class CentralThimble:
    """TRIGA NETL central thimble definitions and pincell builder.

    Provides the thimble wall specification and a nested ``Pincell`` class that
    constructs the concentric cylindrical model.

    References
    ----------
    .. [1] D. R. Redhouse, et al., "Radiation Characterization Summary: NETL Beam Port
           1/5 Free-Field Environment at the 128-inch Core Centerline Adjacent Location,
           (NETL-FF-BP1/5-128-cca).", Nov. 2022. https://doi.org/10.2172/1898256
    """

    @dataclass(frozen=True)
    class Cladding:
        """Central thimble wall specification.

        Parameters
        ----------
        inner_radius : float
            Inner radius of the thimble [cm].
        outer_radius : float
            Outer radius of the thimble [cm].
        material : Material, optional
            Cladding material. Defaults to ``Al6061T6``.
        """
        inner_radius: float
        outer_radius: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.inner_radius > 0.0, "Thimble inner radius must be positive."
            assert self.outer_radius > self.inner_radius, (
                "Thimble outer radius must be larger than inner radius."
            )

    class Pincell(CylindricalPinCell):
        """Central thimble pincell.

        Parameters
        ----------
        cladding : CentralThimble.Cladding
            Thimble cladding wall definition.
        fill_material : Material, optional
            Material filling the thimble interior. Defaults to ``Water``.
        outer_material : Material, optional
            Material surrounding the thimble exterior. Defaults to ``Water``.
        name : str, optional
            Name for this pincell instance.
        """

        @property
        def cladding(self) -> CentralThimble.Cladding:
            return self._cladding

        @property
        def fill_material(self) -> Material:
            return self._fill_material

        def __init__(
            self,
            cladding: CentralThimble.Cladding,
            fill_material: Optional[Material] = None,
            outer_material: Optional[Material] = None,
            name: str = "triga_netl_central_thimble",
        ):
            self._cladding = cladding
            self._fill_material = fill_material or Water()
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
            radii: List[float] = []
            materials: List[Material] = []

            def append_region(radius: float, material: Material) -> None:
                if radii:
                    assert radius > radii[-1], "Region radii must be strictly increasing."
                radii.append(radius)
                materials.append(material)

            append_region(self.cladding.inner_radius, self.fill_material)
            append_region(self.cladding.outer_radius, self.cladding.material)
            materials.append(self._outer_material)

            return radii, materials

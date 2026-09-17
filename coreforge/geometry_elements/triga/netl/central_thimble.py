from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TypedDict

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.cylindrical_stack import CylindricalStack
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Al6061T6, Material, Water, unique_materials
from coreforge.utils import TolerantEqualityMixin


class CentralThimble(GeometryElement):
    """TRIGA NETL central thimble definitions and pincell builder.

    Parameters
    ----------
    cladding : CentralThimble.Cladding
        Thimble wall definition with thickness, outer radius, and material.
    length : float
        The length of the thimble [cm].
    fill_material : Optional[Material]
        Material filling the thimble interior (defaults to ``Water``).
    outer_material : Optional[Material]
        Coolant/exterior material outside the thimble (defaults to ``Water``).
    name : str, optional
        Name for the central thimble element.

    Attributes
    ----------
    cladding : CentralThimble.Cladding
        Thimble wall specification.
    length : float
        The length of the thimble [cm].
    fill_material : Material
        Material filling the thimble interior.
    outer_material : Material
        Coolant/exterior material.
    pincell : CentralThimble.Pincell
        Pincells keyed by axial feature.
    """

    @dataclass(frozen=True, eq=False)
    class Cladding(TolerantEqualityMixin):
        """Central thimble wall specification.

        Attributes
        ----------
        thickness : float
            Thimble wall thickness [cm].
        outer_radius : float
            Outer radius of the thimble [cm].
        inner_radius : float
            Derived inner radius (outer minus thickness) [cm].
        material : Material
            Cladding material. Defaults to ``Al6061T6``.
        """
        thickness: float
        outer_radius: float
        inner_radius: float = field(init=False)
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Thimble wall thickness must be positive."
            assert self.outer_radius > self.thickness, (
                "Thimble outer radius must exceed thickness."
            )
            object.__setattr__(self, "inner_radius", self.outer_radius - self.thickness)

    class Pincell(TypedDict):
        """Pincells used to construct the central-thimble axial stack."""

        thimble: CylindricalPinCell

    @property
    def cladding(self) -> Cladding:
        return self._cladding

    @property
    def length(self) -> float:
        return self._length

    @property
    def fill_material(self) -> Material:
        return self._fill_material

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @property
    def pincell(self) -> Pincell:
        return self._pincell.copy()

    def __init__(self,
                 cladding:       Cladding,
                 length:         float,
                 fill_material:  Optional[Material] = None,
                 outer_material: Optional[Material] = None,
                 name:           str = "central_thimble"):
        super().__init__(name)
        self._cladding = cladding
        self._length = length
        self._fill_material = fill_material or Water()
        self._outer_material = outer_material or Water()

        thimble_pincell = self.build_thimble_pincell(
            cladding=self.cladding,
            fill_material=self.fill_material,
            outer_material=self.outer_material,
            name=self.name + "_pincell",
        )
        self._pincell: CentralThimble.Pincell = {"thimble": thimble_pincell}

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, CentralThimble):
            return False
        return (
            self.cladding == other.cladding and
            self.length == other.length and
            self.fill_material == other.fill_material and
            self.outer_material == other.outer_material
        )

    def __hash__(self) -> int:
        return hash((
            self.cladding,
            relative_round(self.length, TOL),
            self.fill_material,
            self.outer_material,
        ))

    def get_materials(self) -> List[Material]:
        materials = [
            self.cladding.material,
            self.fill_material,
            self.outer_material,
        ]
        return unique_materials(materials)

    def as_stack(self, bottom_pos: float = 0.0) -> CylindricalStack:
        """ A method for getting a copy of the Central Thimble as a Stack

        Parameters
        ----------
        bottom_pos : float
            The axial position of the bottom of the stack (cm)

        Returns
        -------
        CylindricalStack
            The Central Thimble as a Stack
        """

        return CylindricalStack(segments   = [Stack.Segment(self.pincell["thimble"], self.length)],
                                name       = self.name,
                                bottom_pos = bottom_pos)

    @staticmethod
    def build_thimble_pincell(cladding:       Cladding,
                              fill_material:  Optional[Material] = None,
                              outer_material: Optional[Material] = None,
                              name:           str = "central_thimble") -> CylindricalPinCell:
        """Build a pincell for the central thimble cross section.

        Parameters
        ----------
        cladding : CentralThimble.Cladding
            Thimble wall definition with thickness, outer radius, and material.
        fill_material : Material, optional
            Material filling the thimble interior (defaults to ``Water``).
        outer_material : Material, optional
            Coolant/exterior material outside the thimble (defaults to ``Water``).
        gap_tolerance : float, optional
            Minimum thickness to retain a radial zone; thinner gaps are removed.
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the thimble cross section.
        """
        fill_material = fill_material or Water()
        outer_material = outer_material or Water()

        radii = [cladding.inner_radius, cladding.outer_radius]
        materials = [fill_material, cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name)

from __future__ import annotations

from math import isclose
from typing import Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Al6061T6, Air, Material


class BeamPort(GeometryElement):
    """TRIGA NETL beam port geometry element (cylindrical tube).

    Parameters
    ----------
    inner_radius : float
        Inner radius of the beam port tube [cm].
    outer_radius : float
        Outer radius of the beam port tube [cm].
    length : float
        Axial length of the beam port [cm].
    tube_material : Material, optional
        Material of the beam port tube (defaults to ``Al6061T6``).
    fill_material : Material, optional
        Material filling the beam port (defaults to ``Air``).
    name : str, optional
        Name for this beam port element.
    """

    @property
    def inner_radius(self) -> float:
        return self._inner_radius

    @property
    def outer_radius(self) -> float:
        return self._outer_radius

    @property
    def tube_material(self) -> Material:
        return self._tube_material

    @property
    def fill_material(self) -> Material:
        return self._fill_material

    @property
    def length(self) -> float:
        return self._length

    def __init__(self,
                 inner_radius: float,
                 outer_radius: float,
                 length: float,
                 tube_material: Optional[Material] = None,
                 fill_material: Optional[Material] = None,
                 name: str = "beam_port") -> None:
        super().__init__(name)
        assert inner_radius > 0.0, "Beam Port inner radius must be positive."
        assert outer_radius > inner_radius, "Beam Port outer radius must exceed the inner radius."
        assert length > 0.0, "Beam Port length must be positive."

        self._inner_radius = inner_radius
        self._outer_radius = outer_radius
        self._length = length
        self._tube_material = tube_material or Al6061T6()
        self._fill_material = fill_material or Air()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, BeamPort) and
            isclose(self.inner_radius, other.inner_radius, rel_tol=TOL) and
            isclose(self.outer_radius, other.outer_radius, rel_tol=TOL) and
            isclose(self.length, other.length, rel_tol=TOL) and
            self.tube_material == other.tube_material and
            self.fill_material == other.fill_material
        )

    def __hash__(self) -> int:
        return hash((
            relative_round(self.inner_radius, TOL),
            relative_round(self.outer_radius, TOL),
            relative_round(self.length, TOL),
            self.tube_material,
            self.fill_material,
        ))

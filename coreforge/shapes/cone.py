from math import pi, sqrt, isclose
from typing import Any

import openmc
import openmc.model
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.shape import Shape_3D


class Cone(Shape_3D):
    """A concrete two-sided cone shape class.

    The cone has its lower base centered at (0, 0, 0) and apex at (0, 0, h).

    Inner radius is 0 due to the apex

    Parameters
    ----------
    r : float
        The radius of the cone base (cm)
    h : float
        The height from base to apex (cm)

    Attributes
    ----------
    r : float
        The radius of the cone base (cm)
    h : float
        The height from base to apex (cm)
    """

    @property
    def r(self) -> float:
        return self._r

    @property
    def h(self) -> float:
        return self._h

    def __init__(self, r: float, h: float):
        assert r > 0.0, f"r = {r}"
        assert h > 0.0, f"h = {h}"

        self._r = r
        self._h = h

        super().__init__(inner_radius = 0.0,
                         outer_radius = sqrt(r*r + h*h),
                         volume       = (2.0 / 3.0) * pi * r*r*h)

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Cone) and
                isclose(self.r, other.r, rel_tol=TOL) and
                isclose(self.h, other.h, rel_tol=TOL))

    def __hash__(self) -> int:
        return hash((relative_round(self.r, TOL), relative_round(self.h, TOL)))

    def make_region(self) -> openmc.Region:
        """Create a two-sided cone region.

        Returns
        -------
        openmc.Region
            A region representing the two-sided cone with base at z=0 and apex at z=h.
        """
        return openmc.ZCone(z0=self.h, r2=(self.r / self.h)**2)


class OneSidedCone(Shape_3D):
    """A concrete one-sided cone shape class.

    The cone has its base centered at (0, 0, 0) and apex at (0, 0, h).
    This creates a one-sided cone extending only in one direction from the base.

    Parameters
    ----------
    r : float
        The radius of the cone base (cm)
    h : float
        The height from base to apex (cm)

    Attributes
    ----------
    r : float
        The radius of the cone base (cm)
    h : float
        The height from base to apex (cm)
    """

    @property
    def r(self) -> float:
        return self._r

    @property
    def h(self) -> float:
        return self._h

    def __init__(self, r: float, h: float):
        assert r > 0.0, f"r = {r}"
        assert h > 0.0, f"h = {h}"

        self._r = r
        self._h = h

        super().__init__(inner_radius = (r*h) / (sqrt(r*r + h*h) + r),
                         outer_radius = r if r >= h else (r*r + h*h) / (2*h),
                         volume       = (1.0 / 3.0) * pi * r*r*h)

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, OneSidedCone) and
                isclose(self.r, other.r, rel_tol=TOL) and
                isclose(self.h, other.h, rel_tol=TOL))

    def __hash__(self) -> int:
        return hash((relative_round(self.r, TOL), relative_round(self.h, TOL)))

    def make_region(self) -> openmc.Region:
        """Create a one-sided cone region.

        Returns
        -------
        openmc.Region
            A region representing the one-sided cone with base at z=0 and apex at z=h.
        """
        return openmc.model.ZConeOneSided(z0=self.h, r2=(self.r / self.h)**2)

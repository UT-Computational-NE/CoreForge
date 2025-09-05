from math import pi, asin, sqrt, isclose
from typing import Any

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes.shape import Shape_3D



class Cap(Shape_3D):
    """ An abstract shape class for caps

    Notes
    -----
    A cap here is any shape that has a circular base
    and some raised 'crown' surface, such as a spherical cap [1]_.

    References
    ----------
    .. [1] "Spherical Cap." MathWorld--A Wolfram Web Resource, Wolfram Research.
           Accessed 05/01/2024. https://mathworld.wolfram.com/SphericalCap.html

    Attributes
    ----------
    D : float
        Base diameter (cm)
    h : float
        Height (i.e. highest point of the cap) (cm)
    """

    @property
    def D(self) -> float:
        return self._D

    @property
    def h(self) -> float:
        return self._h

    def __init__(self, inner_radius: float, outer_radius: float, volume: float, D: float, h: float):
        assert D > 0.0, f"D = {D}"
        assert h > 0.0, f"h = {h}"
        self._D = D
        self._h = h
        super().__init__(inner_radius, outer_radius, volume)

class Torispherical_Dome(Cap):
    """ A concrete torispherical dome cap class

    Parameters
    ----------
    R : float
        Crown Radius (cm)
    a : float
        Knuckle Radius (cm)
    c : float
        Distance from center of torus to center of torus tube (cm)

    Attributes
    ----------
    R : float
        Crown Radius (cm)
    a : float
        Knuckle Radius (cm)
    c : float
        Distance from center of torus to center of torus tube (cm)
    r : float
        Critical radius at which cap curve transitions from spherical to torus (cm)

    Notes
    -----
    Details on torispherical dome geometries can be found on
    the Wolfram Web Resources [1]_

    References
    ----------
    .. [1] Weisstein, E. W. "Torispherical Dome." MathWorld--A Wolfram Web Resource, Wolfram Research.
           Accessed 05/01/2024. https://mathworld.wolfram.com/TorisphericalDome.html
    """

    @property
    def R(self) -> float:
        return self._R

    @property
    def a(self) -> float:
        return self._a

    @property
    def c(self) -> float:
        return self._c

    @property
    def r(self) -> float:
        return self._r

    def __init__(self, R: float, a: float, c: float):
        assert R > 0.
        assert a >= 0.
        assert a <= c
        assert a+c <= R

        self._R = R
        self._a = a
        self._c = c
        self._r = c * (1 + (1./(R/a - 1)))

        h = R - sqrt((a+c-R) * (a-c-R))
        super().__init__(inner_radius = min(h, a+c),
                         outer_radius = max(h, a+c),
                         volume       = pi/3. * (2*h*R**2 -
                                        (2*a**2 + c**2 + 2*a*R) * (R-h) +
                                        3*(a**2)*c*asin((R-h)/(R-a))),
                         D            = (a+c) * 2.,
                         h            = h)

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Torispherical_Dome)  and
                isclose(self.R, other.R, rel_tol=TOL)  and
                isclose(self.a, other.a, rel_tol=TOL)  and
                isclose(self.c, other.c, rel_tol=TOL))

    def __hash__(self) -> int:
        return hash((relative_round(self.R, TOL),
                     relative_round(self.a, TOL),
                     relative_round(self.c, TOL)))

    def make_region(self) -> openmc.Region:
        base_plane   = openmc.ZPlane(z0=0.0)
        critical_cyl = openmc.ZCylinder(r=self.r)
        outer_cyl    = openmc.ZCylinder(r=self.a + self.c)
        sphere       = openmc.Sphere(z0=self.R - self.h, r=self.R)
        torus        = openmc.ZTorus(z0=0.0, a=self.c, b=self.a, c=self.a)

        crown = -sphere & -critical_cyl
        knuckle = -torus & +critical_cyl
        return +base_plane & -outer_cyl & (crown | knuckle)


class ASME_Flanged_Dished_Dome(Torispherical_Dome):
    """ A concrete shape class for creating a dome shape of an ASME flanged and dished head

    This shape itself is still a solid Torispherical Dome (i.e. is not a shell), but follows
    the geometric dimensionality constraints of a ASME flanged and dished head.

    Parameters
    ----------
    D : float
        Dome Diameter (cm)

    Notes
    -----
    Though the details of ASME flanged and dished heads are retrievable
    in the appropriate ASME standards [1]_, a more readily accessible
    reference is available in Thulukkanam's textbook [2]_.  In this textbook
    an ASME flanged and dished head is defined such that

    :math:`R = D`

    and

    :math:`a = 0.06D`

    References
    ----------
    .. [1] BPVC Section VIII-Rules for Construction of Pressure Vessels Division 1
           https://www.asme.org/codes-standards/find-codes-standards/bpvc-viii-1-bpvc-section-viii-rules-construction-pressure-vessels-division-1-(3)/2023/print-book
    .. [2] Thulukkanam, K. Heat Exchangers: Mechanical Design,
           Materials Selection, Nondestructive Testing, and Manufacturing
           Methods. CRC Press, 2023. Taylor & Francis,
           https://doi.org/10.1201/9781003352051.
    """

    def __init__(self, D: float):
        R = D
        a = 0.06*D
        c = D*0.5 - a
        super().__init__(R, a, c)

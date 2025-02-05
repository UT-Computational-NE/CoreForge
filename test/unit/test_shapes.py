import pytest
from math import isclose, pi, sqrt, asin

from coreforge.shape.circle import Circle
from coreforge.shape.rectangle import Rectangle, Square
from coreforge.shape.stadium import Stadium
from coreforge.shape.hexagon import Hexagon
from coreforge.shape.cap import Torispherical_Dome, ASME_Flanged_Dished_Head
from mpactpy.utils import ROUNDING_RELATIVE_TOLERANCE

TOL = ROUNDING_RELATIVE_TOLERANCE * 1E-2

def test_circle():
    r = 3.
    circle = Circle(r=r)
    assert(isclose(circle.i_r,  r))
    assert(isclose(circle.o_r,  r))
    assert(isclose(circle.area, pi*r*r))

    equal_circle     = Circle(r=r*(1+TOL))
    not_equal_circle = Circle(r=r*2)

    assert circle == equal_circle
    assert circle != not_equal_circle
    assert hash(circle) == hash(equal_circle)
    assert hash(circle) != hash(not_equal_circle)



def test_rectangle():
    w = 2.
    rectangle = Rectangle(w=w)
    assert(isclose(rectangle.i_r,  w * 0.5))
    assert(isclose(rectangle.o_r,  sqrt(2*w*w)))
    assert(isclose(rectangle.area, w*w))

    h = 1.
    rectangle = Rectangle(w=w, h=h)
    assert(isclose(rectangle.i_r,  1 * 0.5))
    assert(isclose(rectangle.o_r,  sqrt(h*h + w*w)))
    assert(isclose(rectangle.area, h*w))

    equal_rectangle     = Rectangle(w=w*(1+TOL), h=h*(1+TOL))
    not_equal_rectangle = Rectangle(w=w*3, h=h*2)

    assert rectangle == equal_rectangle
    assert rectangle != not_equal_rectangle
    assert hash(rectangle) == hash(equal_rectangle)
    assert hash(rectangle) != hash(not_equal_rectangle)



def test_square():
    s = 3.
    square = Square(s=s)
    assert(isclose(square.i_r,  s * 0.5))
    assert(isclose(square.o_r,  sqrt(2*s*s)))
    assert(isclose(square.area, s*s))


def test_stadium():
    r = 0.5
    a = 2.
    stadium = Stadium(r=r, a=a)
    assert(isclose(stadium.i_r,  r))
    assert(isclose(stadium.o_r,  a*0.5 + r))
    assert(isclose(stadium.area, pi*r*r + 2*r*a))

    equal_stadium     = Stadium(r=r*(1+TOL), a=a*(1+TOL))
    not_equal_stadium = Stadium(r=r*2, a=a*4)

    assert stadium == equal_stadium
    assert stadium != not_equal_stadium
    assert hash(stadium) == hash(equal_stadium)
    assert hash(stadium) != hash(not_equal_stadium)



def test_hexagon():
    r = 5.
    hexagon = Hexagon(r=r)
    assert(isclose(hexagon.i_r,  r))
    assert(isclose(hexagon.o_r,  r * 2 / sqrt(3.)))
    assert(isclose(hexagon.area, 3*hexagon.o_r*hexagon.i_r))

    equal_hexagon     = Hexagon(r=r*(1+TOL))
    not_equal_hexagon = Hexagon(r=r, orientation='x')

    assert hexagon == equal_hexagon
    assert hexagon != not_equal_hexagon
    assert hash(hexagon) == hash(equal_hexagon)
    assert hash(hexagon) != hash(not_equal_hexagon)



def test_cap():
    D = 100.
    R = D
    a = 0.06*D
    c = D*0.5 - a

    cap = Torispherical_Dome(R=R, a=a, c=c)
    assert(isclose(cap.r, c * (1 + (1./(R/a - 1)))))
    assert(isclose(cap.h, R - sqrt((a+c-R) * (a-c-R))))
    assert(isclose(cap.D, D))
    assert(isclose(cap.i_r, cap.h))
    assert(isclose(cap.o_r, a+c))

    h = cap.h
    expected_volume = pi/3. * (2*h*R**2 -
                               (2*a**2 + c**2 + 2*a*R) * (R-h) +
                               3*(a**2)*c*asin((R-h)/(R-a)))
    assert(isclose(cap.volume, expected_volume))

    equal_cap     = Torispherical_Dome(R=R*(1+TOL), a=a*(1+TOL), c=c*(1+TOL))
    not_equal_cap = Torispherical_Dome(R=R*1.1, a=a, c=c)

    assert cap == equal_cap
    assert cap != not_equal_cap
    assert hash(cap) == hash(equal_cap)
    assert hash(cap) != hash(not_equal_cap)

    cap = ASME_Flanged_Dished_Head(D)
    assert(isclose(cap.R, R))
    assert(isclose(cap.a, a))
    assert(isclose(cap.c, c))
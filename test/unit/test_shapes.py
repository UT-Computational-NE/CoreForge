import pytest
from math import isclose, pi, sqrt, asin

from coreforge.shapes import Circle, Rectangle, Square, Stadium, Hexagon, \
                            Torispherical_Dome, ASME_Flanged_Dished_Dome
from mpactpy.utils import ROUNDING_RELATIVE_TOLERANCE

TOL = ROUNDING_RELATIVE_TOLERANCE * 1E-2

def test_circle():
    r = 3.
    circle = Circle(r=r)
    assert(isclose(circle.inner_radius,  r))
    assert(isclose(circle.outer_radius,  r))
    assert(isclose(circle.area, pi*r*r))

    equal_circle     = Circle(r=r*(1+TOL))
    not_equal_circle = Circle(r=r*2)

    assert circle == equal_circle
    assert circle != not_equal_circle
    assert hash(circle) == hash(equal_circle)
    assert hash(circle) != hash(not_equal_circle)



def test_rectangle():
    w = 2.
    h = 1.
    rectangle = Rectangle(w=w, h=h)
    assert(isclose(rectangle.inner_radius,  1 * 0.5))
    assert(isclose(rectangle.outer_radius,  0.5*sqrt(h*h + w*w)))
    assert(isclose(rectangle.area, h*w))

    equal_rectangle     = Rectangle(w=w*(1+TOL), h=h*(1+TOL))
    not_equal_rectangle = Rectangle(w=w*3, h=h*2)

    assert rectangle == equal_rectangle
    assert rectangle != not_equal_rectangle
    assert hash(rectangle) == hash(equal_rectangle)
    assert hash(rectangle) != hash(not_equal_rectangle)



def test_square():
    a = 3.
    square = Square(length=a)
    assert(isclose(square.inner_radius,  a*0.5))
    assert(isclose(square.outer_radius,  0.5*sqrt(2*a*a)))
    assert(isclose(square.area, a*a))


def test_stadium():
    r = 0.5
    a = 2.
    stadium = Stadium(r=r, a=a)
    assert(isclose(stadium.inner_radius,  r))
    assert(isclose(stadium.outer_radius,  a*0.5 + r))
    assert(isclose(stadium.area, pi*r*r + 2*r*a))

    equal_stadium     = Stadium(r=r*(1+TOL), a=a*(1+TOL))
    not_equal_stadium = Stadium(r=r*2, a=a*4)

    assert stadium == equal_stadium
    assert stadium != not_equal_stadium
    assert hash(stadium) == hash(equal_stadium)
    assert hash(stadium) != hash(not_equal_stadium)



def test_hexagon():
    r = 5.
    hexagon = Hexagon(inner_radius=r)
    assert(isclose(hexagon.inner_radius,  r))
    assert(isclose(hexagon.outer_radius,  r * 2 / sqrt(3.)))
    assert(isclose(hexagon.area, 3*hexagon.outer_radius*hexagon.inner_radius))

    equal_hexagon     = Hexagon(inner_radius=r*(1+TOL))
    not_equal_hexagon = Hexagon(inner_radius=r, orientation='x')

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
    assert(isclose(cap.inner_radius, cap.h))
    assert(isclose(cap.outer_radius, a+c))

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

    cap = ASME_Flanged_Dished_Dome(D)
    assert(isclose(cap.R, R))
    assert(isclose(cap.a, a))
    assert(isclose(cap.c, c))
import pytest
from math import isclose, pi, sqrt, asin

from coreforge.shapes import Circle, Rectangle, Square, Stadium, Hexagon, \
                            Torispherical_Dome, ASME_Flanged_Dished_Dome, \
                            Cone, OneSidedCone
from coreforge.shapes.utils import is_convex, equal_volume_ring_radii
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

    region = circle.make_region()
    assert region is not None



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

    region = rectangle.make_region()
    assert region is not None


def test_contains_point_circle():
    circle = Circle(r=1.0)
    assert circle.contains_point((0.5, 0.0))
    assert circle.contains_point((1.0, 0.0))
    assert circle.contains_point((0.5, 0.0), rotation=45.0)
    assert not circle.contains_point((1.1, 0.0))


def test_contains_point_rectangle_rotation():
    rectangle = Rectangle(w=2.0, h=1.0)
    assert rectangle.contains_point((0.9, 0.0))
    assert not rectangle.contains_point((0.9, 0.0), rotation=90.0)
    assert rectangle.contains_point((0.0, 0.4), rotation=90.0)


def test_contains_point_hexagon():
    hexagon = Hexagon(inner_radius=1.0, orientation='y')
    assert hexagon.contains_point((0.0, 0.0))
    assert all(hexagon.contains_point(point) for point in hexagon.boundary_points())
    assert not hexagon.contains_point((2.0, 0.0))


def test_contains_point_stadium():
    stadium = Stadium(r=0.5, a=2.0)
    assert stadium.contains_point((0.0, 0.4))
    assert not stadium.contains_point((0.0, 0.6))


def test_contains_rectangle_in_circle():
    circle = Circle(r=1.0)
    rectangle = Rectangle(w=1.0, h=1.0)

    assert circle.contains(rectangle)
    assert circle.contains(rectangle, other_center=(0.2, 0.0))
    assert not circle.contains(rectangle, other_center=(0.5, 0.0))


def test_contains_rectangle_in_rectangle():
    outer = Rectangle(w=2.0, h=1.0)
    inner = Rectangle(w=0.5, h=0.5)

    assert outer.contains(inner)
    assert not outer.contains(inner, other_center=(0.0, 0.6))
    assert outer.contains(inner, other_center=(0.0, 0.6), self_rotation=90.0)


def test_contains_rotated_rectangle():
    outer = Rectangle(w=2.0, h=2.0)
    inner = Rectangle(w=1.0, h=1.0)
    larger_inner = Rectangle(w=1.6, h=1.6)

    assert outer.contains(inner, other_rotation=45.0)
    assert not outer.contains(larger_inner, other_rotation=45.0)


def test_contains_rectangle_in_rotated_hexagon():
    hexagon = Hexagon(inner_radius=1.0, orientation='y')
    rectangle = Rectangle(w=0.1, h=0.1)

    assert hexagon.contains(rectangle)
    assert not hexagon.contains(rectangle, other_center=(1.0, 0.0))
    assert hexagon.contains(rectangle, other_center=(0.0, 0.9), self_rotation=30.0)


def test_contains_unsupported_boundary_points():
    rectangle = Rectangle(w=2.0, h=2.0)
    circle = Circle(r=0.5)

    assert rectangle.contains(circle) is NotImplemented


def test_convex_utils():
    square = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    concave = [(-1.0, -1.0), (1.0, -1.0), (0.0, 0.0), (1.0, 1.0), (-1.0, 1.0)]

    assert is_convex(square)
    assert not is_convex(concave)


def test_equal_volume_ring_radii():
    # Test Disk
    radii = equal_volume_ring_radii(outer_radius=2.0, num_regions=4)
    expected = [1.0, sqrt(2.0), sqrt(3.0), 2.0]

    assert len(radii) == len(expected)
    assert all(isclose(radii[i], expected[i]) for i in range(len(expected)))

    # Test Annulus
    radii = equal_volume_ring_radii(outer_radius=3.0, num_regions=2, inner_radius=1.0)
    expected = [sqrt(5.0), 3.0]

    assert len(radii) == len(expected)
    assert all(isclose(radii[i], expected[i]) for i in range(len(expected)))

    ring_area_1 = radii[0] * radii[0] - 1.0
    ring_area_2 = radii[1] * radii[1] - radii[0] * radii[0]
    assert isclose(ring_area_1, ring_area_2)

    # Invalid Inputs
    with pytest.raises(AssertionError):
        equal_volume_ring_radii(outer_radius=1.0, num_regions=1, inner_radius=-1.0)

    with pytest.raises(AssertionError):
        equal_volume_ring_radii(outer_radius=1.0, num_regions=1, inner_radius=1.0)

    with pytest.raises(AssertionError):
        equal_volume_ring_radii(outer_radius=1.0, num_regions=0)


def test_circle_rectangle_intersection():
    rectangle = Rectangle(w=2.0, h=1.0)
    circle = Circle(r=0.4)

    assert rectangle.intersects(circle)
    assert circle.intersects(rectangle)

    outside_circle = Circle(r=0.4)
    assert not rectangle.intersects(outside_circle, other_center=(2.0, 0.0))
    assert not outside_circle.intersects(rectangle, self_center=(2.0, 0.0))

    touching_circle = Circle(r=0.4)
    assert rectangle.intersects(touching_circle, other_center=(1.4, 0.0))
    assert touching_circle.intersects(rectangle, self_center=(1.4, 0.0))

    small_circle = Circle(r=0.1)
    assert not rectangle.intersects(small_circle, other_center=(0.0, 0.9))
    assert rectangle.intersects(small_circle, other_center=(0.0, 0.9), self_rotation=90.0)
    assert small_circle.intersects(rectangle, self_center=(0.0, 0.9), other_rotation=90.0)


def test_circle_hexagon_intersection():
    hexagon = Hexagon(inner_radius=1.0, orientation='y')
    circle = Circle(r=0.2)

    assert hexagon.intersects(circle)
    assert circle.intersects(hexagon)
    assert not hexagon.intersects(circle, other_center=(2.0, 0.0))
    assert not circle.intersects(hexagon, self_center=(2.0, 0.0))

    touching_circle = Circle(r=0.2)
    assert hexagon.intersects(touching_circle, other_center=(1.2, 0.0))
    assert touching_circle.intersects(hexagon, self_center=(1.2, 0.0))
    assert hexagon.intersects(touching_circle, other_center=(0.0, 1.2), self_rotation=30.0)


def test_rectangle_rectangle_intersection():
    rectangle = Rectangle(w=2.0, h=1.0)
    small_rectangle = Rectangle(w=0.5, h=0.5)

    assert rectangle.intersects(small_rectangle)
    assert small_rectangle.intersects(rectangle)
    assert not rectangle.intersects(small_rectangle, other_center=(2.0, 0.0))

    assert rectangle.intersects(small_rectangle, other_center=(1.25, 0.0))

    horizontal = Rectangle(w=2.0, h=0.2)
    vertical = Rectangle(w=0.2, h=2.0)
    assert horizontal.intersects(vertical)

    bar = Rectangle(w=2.0, h=0.2)
    assert bar.intersects(bar, other_rotation=90.0)
    assert bar.intersects(bar, other_center=(0.0, 0.9), other_rotation=90.0)
    assert not bar.intersects(bar, other_center=(0.0, 1.2), other_rotation=90.0)


def test_hexagon_rectangle_intersection():
    hexagon = Hexagon(inner_radius=1.0, orientation='y')
    rectangle = Rectangle(w=0.5, h=0.5)

    assert hexagon.intersects(rectangle)
    assert rectangle.intersects(hexagon)
    assert not hexagon.intersects(rectangle, other_center=(2.0, 0.0))
    assert not rectangle.intersects(hexagon, self_center=(2.0, 0.0))

    bar = Rectangle(w=2.0, h=0.2)
    assert hexagon.intersects(bar, other_center=(0.0, 1.0), other_rotation=30.0)
    assert not hexagon.intersects(bar, other_center=(0.0, 2.0), other_rotation=30.0)


def test_hexagon_hexagon_intersection():
    hexagon = Hexagon(inner_radius=1.0, orientation='y')
    small_hexagon = Hexagon(inner_radius=0.5, orientation='x')

    assert hexagon.intersects(small_hexagon)
    assert small_hexagon.intersects(hexagon)
    assert hexagon.intersects(small_hexagon, other_center=(1.0, 0.0))
    assert not hexagon.intersects(small_hexagon, other_center=(3.0, 0.0))
    assert hexagon.intersects(small_hexagon, other_center=(0.0, 1.0), other_rotation=30.0)


def test_square():
    a = 3.
    square = Square(length=a)
    assert(isclose(square.inner_radius,  a*0.5))
    assert(isclose(square.outer_radius,  0.5*sqrt(2*a*a)))
    assert(isclose(square.area, a*a))

    region = square.make_region()
    assert region is not None


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

    region = stadium.make_region()
    assert region is not None



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

    region = hexagon.make_region()
    assert region is not None



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

    # Test that the region is created properly
    region = cap.make_region()
    assert region is not None

    cap = ASME_Flanged_Dished_Dome(D)
    assert(isclose(cap.R, R))
    assert(isclose(cap.a, a))
    assert(isclose(cap.c, c))

    # Test that the region is created properly
    region = cap.make_region()
    assert region is not None


def test_cone():
    r = 5.0
    h = 10.0
    cone = Cone(r=r, h=h)

    assert isclose(cone.r, r)
    assert isclose(cone.h, h)
    assert isclose(cone.inner_radius, 0.0)
    assert isclose(cone.outer_radius, sqrt(r*r + h*h))
    assert isclose(cone.volume, (2.0 / 3.0) * pi * r*r*h)

    equal_cone = Cone(r=r * (1 + TOL), h=h * (1 + TOL))
    not_equal_cone = Cone(r=r * 2, h=h * 2)

    assert cone == equal_cone
    assert cone != not_equal_cone
    assert hash(cone) == hash(equal_cone)
    assert hash(cone) != hash(not_equal_cone)

    region = cone.make_region()
    assert region is not None


def test_onesided_cone():
    r = 5.0
    h = 10.0
    cone = OneSidedCone(r=r, h=h)

    assert isclose(cone.r, r)
    assert isclose(cone.h, h)
    assert isclose(cone.inner_radius, (r*h) / (sqrt(r*r + h*h) + r))
    assert isclose(cone.outer_radius, (r*r + h*h) / (2*h))
    assert isclose(cone.volume, (1.0 / 3.0) * pi * r*r*h)

    equal_cone = OneSidedCone(r=r * (1 + TOL), h=h * (1 + TOL))
    not_equal_cone = OneSidedCone(r=r * 2, h=h * 2)

    assert cone == equal_cone
    assert cone != not_equal_cone
    assert hash(cone) == hash(equal_cone)
    assert hash(cone) != hash(not_equal_cone)

    region = cone.make_region()
    assert region is not None

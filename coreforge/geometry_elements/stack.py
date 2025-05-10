from __future__ import annotations
from typing import List, Any
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement

class Stack(GeometryElement):
    """ A class for Z-axis aligned segments (i.e. stacks)

    Here, a stack is a collection of Z-axis aligned 'segments' which
    are 'stacked' atop one another.  The origin for a stack is located at radial
    center of the segements.

    When building MPACT Core geometries, the segments must be 2D z-axis
    extrudable radial profile.  As such, the geometry element to be extruded must
    be a 2D element, in that it's corresponding MPACT core geometry produced using
    make_mpact_core must be a single MPACT Assembly with a single MPACT Lattice with
    MPACT modules that are only a single MPACT Pin in the z-dimension.

    Attributes
    ----------
    segments : List[Segment]
        The collection of segments which comprise the stack, ordered from bottom to top
    bottom_pos : float
        The axial position of the bottom of the stack (cm)
    length : float
        The total length of the stack
    """

    class Segment():
        """ A class for the segments which comprise a Stack

        Attributes
        ----------
        element : GeometryElement
            The geometry element which occupies the segment
        length : float
            The length of the segment
        """

        @property
        def element(self) -> GeometryElement:
            return self._element

        @element.setter
        def element(self, element: GeometryElement) -> None:
            self._element = element

        @property
        def length(self) -> float:
            return self._length

        @length.setter
        def length(self, length: float) -> None:
            assert length > 0., f"length = {length}"
            self._length = length

        def __init__(self,
                     element: GeometryElement,
                     length:  float):
            self.element           = element
            self.length            = length

        def __eq__(self, other: Any) -> bool:
            if self is other:
                return True
            return (isinstance(other, Stack.Segment) and
                    self.element == other.element    and
                    isclose(self.length, other.length, rel_tol=TOL)
                   )

        def __hash__(self) -> int:
            return hash((self.element, relative_round(self.length, TOL)))


    @property
    def segments(self) -> List[Segment]:
        return self._segments

    @segments.setter
    def segments(self, segments: List[Segment]) -> None:
        assert len(segments) > 0, f"len(segments) = {len(segments)}"
        self._segments = segments
        self._length   = sum(segment.length for segment in segments)

    @property
    def bottom_pos(self) -> float:
        return self._bottom_pos

    @bottom_pos.setter
    def bottom_pos(self, bottom_pos: float) -> None:
        self._bottom_pos = bottom_pos

    @property
    def length(self) -> float:
        return self._length

    def __init__(self, segments: List[Segment], name: str = 'stack', bottom_pos: float = 0.):
        super().__init__(name)
        self.segments   = segments
        self.bottom_pos = bottom_pos

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        return (isinstance(other, Stack)                                and
                isclose(self.bottom_pos, other.bottom_pos, rel_tol=TOL) and
                len(self.segments) == len(other.segments)               and
                all(self.segments[i] == other.segments[i] for i in range(len(self.segments)))
               )

    def __hash__(self) -> int:
        return hash((relative_round(self.bottom_pos, TOL), tuple(self.segments)))

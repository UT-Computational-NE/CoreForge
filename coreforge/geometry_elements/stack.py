from __future__ import annotations
from typing import List, Any, Optional, Tuple
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell

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

    def __add__(self, other: Stack) -> Stack:
        assert isinstance(other, Stack), f"Can only add Stack to Stack (got {type(other)})"
        return Stack(segments   = self.segments + other.segments,
                     name       = self.name,
                     bottom_pos = self.bottom_pos)

    def unionize_radial_mesh(self) -> Stack:
        """Return a new Stack with unionized radial material meshes across all segments.

        Returns
        -------
        Stack
            A new stack with segments rebuilt to share a common
            set of radii derived from the union of all segment radii.

        Notes
        -----
        This currently supports only stacks whose segments are CylindricalPinCell
        elements. Each rebuilt pincell uses the unionized radii and assigns the
        material for each radius based on the original segment's zones. Radii
        beyond the original zones are filled with the segment's outer material.
        """
        assert all(isinstance(segment.element, CylindricalPinCell) for segment in self.segments), \
            "All stack segments must be CylindricalPinCell to unionize radial mesh."

        union_radii = sorted(set(
            radius
            for segment in self.segments
            for radius in [zone.shape.outer_radius for zone in segment.element.zones]))

        def material_for_radius(pincell: CylindricalPinCell, radius: float):
            for zone in pincell.zones:
                if radius <= zone.shape.outer_radius or isclose(radius, zone.shape.outer_radius, rel_tol=TOL):
                    return zone.material
            return pincell.outer_material

        segments = []
        for segment in self.segments:
            materials = [material_for_radius(segment.element, radius) for radius in union_radii]
            materials.append(segment.element.outer_material)
            pincell = CylindricalPinCell(radii     = union_radii,
                                         materials = materials,
                                         name      = segment.element.name)
            segments.append(Stack.Segment(element = pincell,
                                          length  = segment.length))

        return Stack(segments=segments, name=self.name, bottom_pos=self.bottom_pos)

    def get_axial_slice_with_origins(self,
                                     start_pos: float,
                                     stop_pos:  float,
    ) -> Optional[Tuple[Stack, List[Stack.Segment]]]:
        """Return a new Stack from an axial slice with segment origins.

        Parameters
        ----------
        start_pos : float
            Starting axial position of the slice (cm), in the same coordinate
            system as ``bottom_pos``.  Will snap to the bottom of the stack if
            ``start_pos`` is below the stack.
        stop_pos : float
            Stopping axial position of the slice (cm), in the same coordinate
            system as ``bottom_pos``.  Will snap to the top of the stack if
            ``stop_pos`` is above the stack.

        Returns
        -------
        Optional[Tuple[Stack, List[Stack.Segment]]]
            A new stack representing the overlap with the slice bounds and a
            list of the original segments from which the sliced segments were derived.
            Order of the original segments corresponds to the order of the sliced
            stack's segments. Returns ``None`` if there is no overlap.
        """
        assert stop_pos > start_pos, "stop_pos must be greater than start_pos."

        stack_start = self.bottom_pos
        stack_stop = self.bottom_pos + self.length

        if stop_pos <= stack_start or isclose(stop_pos, stack_start, rel_tol=TOL) or \
           start_pos >= stack_stop or isclose(start_pos, stack_stop, rel_tol=TOL):
            return None

        start_pos = max(start_pos, stack_start)
        stop_pos = min(stop_pos, stack_stop)

        segments = []
        origins = []
        cursor = stack_start
        for segment in self.segments:
            seg_start = cursor
            seg_end = cursor + segment.length
            overlap_start = max(seg_start, start_pos)
            overlap_end = min(seg_end, stop_pos)
            if overlap_end > overlap_start and not isclose(overlap_end, overlap_start, rel_tol=TOL):
                sliced_segment = Stack.Segment(segment.element, overlap_end - overlap_start)
                segments.append(sliced_segment)
                origins.append(segment)
            cursor = seg_end

        if not segments:
            return None

        sliced_stack = Stack(segments=segments, name=self.name, bottom_pos=start_pos)
        return sliced_stack, origins


    def get_axial_slice(self, start_pos: float, stop_pos: float) -> Optional[Stack]:
        """Return a new Stack from the axial slice of this stack.

        Parameters
        ----------
        start_pos : float
            Starting axial position of the slice (cm), in the same coordinate
            system as ``bottom_pos``.  Will snap to the bottom of the stack if
            ``start_pos`` is below the stack.
        stop_pos : float
            Stopping axial position of the slice (cm), in the same coordinate
            system as ``bottom_pos``.  Will snap to the top of the stack if
            ``stop_pos`` is above the stack.

        Returns
        -------
        Optional[Stack]
            A new stack representing the overlap with the slice bounds. Returns
            ``None`` if there is no overlap.
        """
        result = self.get_axial_slice_with_origins(start_pos, stop_pos)
        if result is None:
            return None
        sliced_stack, _ = result
        return sliced_stack

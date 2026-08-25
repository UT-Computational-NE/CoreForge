from __future__ import annotations

from math import isclose
from typing import List

from mpactpy.utils import ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.stack import Stack


class CylindricalStack(Stack):
    """A stack composed entirely of cylindrical pin-cell segments.

    Attributes
    ----------
    segments : List[Segment]
        The collection of cylindrical pin-cell segments which comprise the stack,
        ordered from bottom to top
    bottom_pos : float
        The axial position of the bottom of the stack (cm)
    length : float
        The total length of the stack
    """

    @Stack.segments.setter
    def segments(self, segments: List[Stack.Segment]) -> None:
        assert len(segments) > 0, f"len(segments) = {len(segments)}"
        assert all(isinstance(segment.element, CylindricalPinCell) for segment in segments), \
            "All CylindricalStack segments must contain a CylindricalPinCell."
        self._segments = segments
        self._length = sum(segment.length for segment in segments)


    def unionize_radial_mesh(self) -> CylindricalStack:
        """Return a stack with a common radial mesh across all segments.

        The radial mesh is formed from the sorted union of the zone radii in
        every segment. Each segment is rebuilt on that common mesh using the
        material occupying each radius in its original pin cell. Radii beyond
        the original zones use the original pin cell's outer material.

        Returns
        -------
        CylindricalStack
            New stack whose segments share the same radial mesh.
        """

        union_radii = sorted(set(
            zone.shape.outer_radius
            for segment in self.segments
            for zone in segment.element.zones
        ))

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

        return CylindricalStack(segments   = segments,
                                name       = self.name,
                                bottom_pos = self.bottom_pos)

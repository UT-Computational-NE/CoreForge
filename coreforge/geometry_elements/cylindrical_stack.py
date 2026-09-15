from __future__ import annotations

from math import isclose
from typing import List

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Material


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
    outer_material : Material
        The common outer material of all cylindrical pin-cell segments
    """

    @property
    def outer_material(self) -> Material:
        """Return the common outer material of all stack segments.

        Returns
        -------
        Material
            The common outer material of all cylindrical pin-cell segments.

        Raises
        ------
        AssertionError
            If the segments do not all have the same outer material.
        """

        assert self._outer_material is not None, \
            "CylindricalStack segments must share a common outer material."
        return self._outer_material

    @Stack.segments.setter
    def segments(self, segments: List[Stack.Segment]) -> None:
        assert len(segments) > 0, f"len(segments) = {len(segments)}"
        assert all(isinstance(segment.element, CylindricalPinCell) for segment in segments), \
            "All CylindricalStack segments must contain a CylindricalPinCell."
        self._segments = segments
        self._length = sum(segment.length for segment in segments)
        outer_material = segments[0].element.outer_material
        self._outer_material = outer_material if all(
            segment.element.outer_material == outer_material for segment in segments
        ) else None


    def translate(self, x0: float, y0: float) -> CylindricalStack:
        """Return a translated copy of this cylindrical stack.

        The supplied offsets are added to the existing center coordinates of
        every cylindrical pin cell. The original stack and its segments are
        not modified.

        Parameters
        ----------
        x0 : float
            Translation along the x-axis [cm].
        y0 : float
            Translation along the y-axis [cm].

        Returns
        -------
        CylindricalStack
            A copied stack with translated cylindrical pin cells.
        """

        segments = []
        for segment in self.segments:
            pincell = segment.element
            translated_pincell = CylindricalPinCell(
                zones          = list(pincell.zones),
                outer_material = pincell.outer_material,
                name           = pincell.name,
                x0             = pincell.x0 + x0,
                y0             = pincell.y0 + y0)
            segments.append(Stack.Segment(element = translated_pincell,
                                          length  = segment.length))

        return type(self)(segments   = segments,
                          name       = self.name,
                          bottom_pos = self.bottom_pos)


    def unionize_radial_mesh(self) -> CylindricalStack:
        """Return a stack with common radial meshes among coaxial segments.

        Segments are grouped by their cylindrical pin-cell center. The radial
        mesh for each group is formed from the sorted union of the zone radii
        in its coaxial segments. Each segment is rebuilt on its group's common
        mesh using the material occupying each radius in its original pin cell.
        Radii beyond the original zones use the original pin cell's outer
        material. Noncoaxial groups retain independent radial meshes because a
        single cylindrical pin cell cannot represent circles with different
        centers.

        Returns
        -------
        CylindricalStack
            New stack whose coaxial segment groups share their respective
            radial meshes.
        """

        radii_by_center = {}
        for segment in self.segments:
            pincell = segment.element
            center = (relative_round(pincell.x0, TOL),
                      relative_round(pincell.y0, TOL))
            radii_by_center.setdefault(center, set()).update(
                zone.shape.outer_radius for zone in pincell.zones
            )

        def material_for_radius(pincell: CylindricalPinCell, radius: float):
            for zone in pincell.zones:
                if radius <= zone.shape.outer_radius or isclose(radius, zone.shape.outer_radius, rel_tol=TOL):
                    return zone.material
            return pincell.outer_material

        segments = []
        for segment in self.segments:
            original_pincell = segment.element
            center = (relative_round(original_pincell.x0, TOL),
                      relative_round(original_pincell.y0, TOL))
            union_radii = sorted(radii_by_center[center])
            materials = [material_for_radius(original_pincell, radius) for radius in union_radii]
            materials.append(original_pincell.outer_material)
            pincell = CylindricalPinCell(radii     = union_radii,
                                         materials = materials,
                                         name      = original_pincell.name,
                                         x0        = original_pincell.x0,
                                         y0        = original_pincell.y0)
            segments.append(Stack.Segment(element = pincell,
                                          length  = segment.length))

        return CylindricalStack(segments   = segments,
                                name       = self.name,
                                bottom_pos = self.bottom_pos)

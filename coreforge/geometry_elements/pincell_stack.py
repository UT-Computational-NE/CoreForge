from __future__ import annotations

from copy import deepcopy
from math import isclose
from typing import List

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.pincell import PinCell
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Material
from coreforge.shapes import Circle, Shape_2D


class PinCellStack(Stack):
    """A stack of z-aligned pin-cell segments.

    All pin cells share the same radial center.

    Parameters
    ----------
    segments : List[Stack.Segment]
        Nonempty collection of pin-cell segments, ordered from bottom to top.
        All pin cells must have the same ``x0`` and ``y0`` coordinates.
    name : str
        A name for the geometry element.
    bottom_pos : float
        The axial position of the bottom of the stack [cm].

    Attributes
    ----------
    segments : List[Stack.Segment]
        Pin-cell segments, ordered from bottom to top.
    bottom_pos : float
        The axial position of the bottom of the stack [cm].
    length : float
        The total length of the stack [cm].
    x0 : float
        The common radial center's x-coordinate [cm]. Setting this updates
        every segment's pin cell.
    y0 : float
        The common radial center's y-coordinate [cm]. Setting this updates
        every segment's pin cell.
    outer_material : Material
        The common outer material of all pin-cell segments.
    footprint : Shape_2D
        The outermost zone shape with the largest outer radius across all
        segments, centered at its local origin. Its outcircle bounds the
        radial footprint of the stack.
    """

    @property
    def x0(self) -> float:
        """The common radial center's x-coordinate [cm]."""
        return self.segments[0].element.x0

    @x0.setter
    def x0(self, x0: float) -> None:
        for segment in self.segments:
            segment.element.x0 = x0

    @property
    def y0(self) -> float:
        """The common radial center's y-coordinate [cm]."""
        return self.segments[0].element.y0

    @y0.setter
    def y0(self, y0: float) -> None:
        for segment in self.segments:
            segment.element.y0 = y0

    @property
    def footprint(self) -> Shape_2D:
        return self._footprint

    @property
    def outer_material(self) -> Material:
        """Return the common outer material of all stack segments.

        Returns
        -------
        Material
            The common background material of the pin cells.

        Raises
        ------
        AssertionError
            If the segments do not all have the same outer material.
        """
        assert self._outer_material is not None, \
            "PinCellStack segments must share a common outer material."
        return self._outer_material

    @Stack.segments.setter
    def segments(self, segments: List[Stack.Segment]) -> None:
        assert len(segments) > 0, f"len(segments) = {len(segments)}"
        assert all(isinstance(segment.element, PinCell) for segment in segments), \
            "All PinCellStack segments must contain a PinCell."
        center = segments[0].element
        assert all(isclose(segment.element.x0, center.x0, rel_tol=TOL) and
                   isclose(segment.element.y0, center.y0, rel_tol=TOL)
                   for segment in segments), \
            "All PinCellStack pin cells must share the same radial center."
        self._segments = segments
        self._length = sum(segment.length for segment in segments)
        self._footprint = max((segment.element.zones[-1].shape for segment in segments),
                              key=lambda shape: shape.outer_radius)
        outer_material = segments[0].element.outer_material
        self._outer_material = outer_material if all(
            segment.element.outer_material == outer_material for segment in segments
        ) else None

    def translate(self,
                  dx: float = 0.0,
                  dy: float = 0.0,
                  dz: float = 0.0) -> PinCellStack:
        """Return a translated copy of this pin-cell stack.

        Radial offsets are applied to deep-copied pin cells, and the axial offset is
        added to ``bottom_pos``. The original stack and pin cells are not
        modified. The stack's concrete type is retained, and segments, pin
        cells, zones, shapes, and materials are deep-copied.

        Parameters
        ----------
        dx : float
            Translation along the x-axis [cm].
        dy : float
            Translation along the y-axis [cm].
        dz : float
            Translation along the z-axis [cm].

        Returns
        -------
        PinCellStack
            A new stack with translated pin cells, unchanged segment lengths,
            and the translated bottom axial position.
        """
        translated = deepcopy(self)
        translated.x0 += dx
        translated.y0 += dy
        translated.bottom_pos += dz
        return translated

    def unionize_radial_mesh(self) -> PinCellStack:
        """Return a new stack whose segments share a common radial mesh.

        The mesh is the sorted union of the segments' shape-rotation pairs.
        Each new zone retains the material occupying that region in its
        original pin cell. Interfaces beyond the original finite zones use
        that pin cell's outer material, extending its explicit finite region
        to the common outermost interface.

        Returns
        -------
        PinCellStack
            A new stack with common radial interfaces and unchanged segment
            lengths, pin-cell centers, and axial position.

        Raises
        ------
        AssertionError
            If an inner interface's outer radius exceeds the next outer
            interface's inner radius. This conservative restriction applies
            regardless of rotation; more general nested shapes are not yet
            supported.
        """
        interface_map = {
            (zone.shape, 0.0 if isinstance(zone.shape, Circle)
             else relative_round(zone.rotation, TOL)): (zone.shape, zone.rotation)
            for segment in self.segments for zone in segment.element.zones
        }
        interfaces = sorted(interface_map.values(), key=lambda interface: interface[0].outer_radius)
        assert all(inner[0].outer_radius <= outer[0].inner_radius
                   for inner, outer in zip(interfaces, interfaces[1:])), \
            "Radial unionization requires each inner shape's outer radius " \
            "not to exceed the next outer shape's inner radius."
        cylindrical_mesh = all(isinstance(shape, Circle) for shape, _ in interfaces)

        segments = []
        for segment in self.segments:
            original = segment.element
            zones = []
            for shape, rotation in interfaces:
                source_zone = next((zone for zone in original.zones
                                    if shape.outer_radius <= zone.shape.outer_radius or
                                    isclose(shape.outer_radius, zone.shape.outer_radius, rel_tol=TOL)),
                                   None)
                zones.append(PinCell.Zone(shape=shape,
                                          material=source_zone.material if source_zone else original.outer_material,
                                          name=source_zone.name if source_zone else 'zone',
                                          rotation=rotation))

            pincell_type = type(original)
            if isinstance(original, CylindricalPinCell) and not cylindrical_mesh:
                pincell_type = PinCell
            pincell = pincell_type(zones=zones, outer_material=original.outer_material,
                                   name=original.name, x0=original.x0, y0=original.y0)
            segments.append(Stack.Segment(element=pincell, length=segment.length))

        return type(self)(segments=segments, name=self.name, bottom_pos=self.bottom_pos)

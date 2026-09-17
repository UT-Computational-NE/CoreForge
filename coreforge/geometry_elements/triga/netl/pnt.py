from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose
from typing import List, Optional, TypedDict

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.cylindrical_stack import CylindricalStack
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Air, Al6061T6, Material, Water, unique_materials
from coreforge.utils import TolerantEqualityMixin


class PNT(GeometryElement):
    """TRIGA NETL pneumatic neutron transport system geometry.

    Parameters
    ----------
    tube : PNT.Tube
        Inner transport tube specification.
    terminus : CylindricalStack
        Cylindrical segments below the transport tube, ordered from bottom to top.
        The terminus ``bottom_pos`` and outer material are ignored.
    bottom_pos : float, optional
        Axial position of the bottom of the complete PNT [cm]. Defaults to 0.0.
    wrapper : PNT.Wrapper, optional
        Concentric wrapper around the lower portion of the transport tube.
    outer_material : Material, optional
        Material surrounding the PNT (defaults to ``Water``).
    gap_tolerance : float, optional
        Minimum radial-zone thickness to retain. Defaults to ``None`` (no filtering).
    name : str, optional
        Name for the PNT element.

    Attributes
    ----------
    tube : PNT.Tube
        Inner transport tube specification.
    terminus : CylindricalStack
        Cylindrical terminus segments.
    bottom_pos : float
        Axial position of the bottom of the complete PNT [cm].
    wrapper : PNT.Wrapper, optional
        Optional wrapper specification.
    outer_material : Material
        Exterior/coolant material.
    gap_tolerance : float, optional
        Minimum radial-zone thickness to retain.
    length : float
        Total PNT length, including the terminus and transport tube [cm].
    pincell : PNT.Pincell
        Pincells keyed by axial feature.
    """

    @dataclass(frozen=True, eq=False)
    class Tube(TolerantEqualityMixin):
        """PNT transport tube specification.

        Parameters
        ----------
        inner_radius : float
            Tube inner radius [cm].
        outer_radius : float
            Tube outer radius [cm].
        length : float
            Tube axial length [cm].
        material : Material, optional
            Tube material (defaults to ``Al6061T6``).
        fill_material : Material, optional
            Material filling the tube bore (defaults to ``Air``).
        """

        inner_radius: float
        outer_radius: float
        length: float
        material: Material = field(default_factory=Al6061T6)
        fill_material: Material = field(default_factory=Air)

        def __post_init__(self) -> None:
            assert self.inner_radius > 0.0, "PNT tube inner radius must be positive."
            assert self.outer_radius > self.inner_radius, (
                "PNT tube outer radius must exceed its inner radius."
            )
            assert self.length > 0.0, "PNT tube length must be positive."

    @dataclass(frozen=True)
    class Wrapper:
        """Concentric wrapper around the lower portion of the transport tube.

        The cross section defines only the concentric regions outside the
        transport tube. Its innermost zone material begins at the transport
        tube outer radius. The cross section's outer material is ignored; the
        enclosing :class:`PNT` supplies the exterior material.

        Parameters
        ----------
        length : float
            Wrapped axial length [cm].
        cross_section : CylindricalPinCell
            Radial zones outside the transport tube. The first zone boundary
            must be larger than the transport tube outer radius.
        """

        length: float
        cross_section: CylindricalPinCell

        def __post_init__(self) -> None:
            assert self.length > 0.0, "PNT wrapper length must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (isinstance(other, PNT.Wrapper) and
                    isclose(self.length, other.length, rel_tol=TOL) and
                    self.cross_section.zones == other.cross_section.zones)

        def __hash__(self) -> int:
            return hash((relative_round(self.length, TOL),
                         tuple(self.cross_section.zones)))

    class Pincell(TypedDict):
        """Pincells used to construct the PNT axial stack."""

        tube: CylindricalPinCell
        wrapped_tube: Optional[CylindricalPinCell]

    @property
    def tube(self) -> Tube:
        return self._tube

    @property
    def terminus(self) -> CylindricalStack:
        return self._terminus

    @property
    def bottom_pos(self) -> float:
        return self._bottom_pos

    @property
    def wrapper(self) -> Optional[Wrapper]:
        return self._wrapper

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @property
    def gap_tolerance(self) -> Optional[float]:
        return self._gap_tolerance

    @property
    def length(self) -> float:
        return self._length

    @property
    def pincell(self) -> Pincell:
        return self._pincell.copy()

    def __init__(self,
                 tube:           Tube,
                 terminus:       CylindricalStack,
                 bottom_pos:     float = 0.0,
                 wrapper:        Optional[Wrapper] = None,
                 outer_material: Optional[Material] = None,
                 gap_tolerance:  Optional[float] = None,
                 name:           str = "pnt") -> None:
        super().__init__(name)
        if wrapper is not None:
            assert wrapper.length <= tube.length, (
                "PNT wrapper length must not exceed the tube length."
            )
            first_wrapper_radius = wrapper.cross_section.zones[0].shape.outer_radius
            assert first_wrapper_radius > tube.outer_radius, (
                "PNT wrapper cross-section innermost radius must exceed the tube outer radius."
            )
        if gap_tolerance is not None:
            assert gap_tolerance >= 0.0, "PNT gap tolerance must be non-negative."

        self._tube = tube
        self._bottom_pos = bottom_pos
        self._wrapper = wrapper
        self._outer_material = outer_material or Water()
        self._gap_tolerance = gap_tolerance
        self._terminus = self.build_terminus_stack(
            terminus=terminus,
            outer_material=self.outer_material,
            name=terminus.name,
        )
        self._length = self.terminus.length + self.tube.length

        tube_pincell = self.build_tube_pincell(
            tube=self.tube,
            outer_material=self.outer_material,
            gap_tolerance=self.gap_tolerance,
            name=self.name + "_tube_pincell",
        )
        wrapped_tube_pincell = None
        if self.wrapper is not None:
            wrapped_tube_pincell = self.build_wrapped_tube_pincell(
                tube=self.tube,
                wrapper=self.wrapper,
                outer_material=self.outer_material,
                gap_tolerance=self.gap_tolerance,
                name=self.name + "_wrapped_tube_pincell",
            )
        self._pincell: PNT.Pincell = {
            "tube": tube_pincell,
            "wrapped_tube": wrapped_tube_pincell,
        }

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, PNT):
            return False
        return (
            self.tube == other.tube and
            self.terminus.segments == other.terminus.segments and
            isclose(self.bottom_pos, other.bottom_pos, rel_tol=TOL) and
            self.wrapper == other.wrapper and
            self.outer_material == other.outer_material and
            ((self.gap_tolerance is None and other.gap_tolerance is None) or
             (self.gap_tolerance is not None and other.gap_tolerance is not None and
              isclose(self.gap_tolerance, other.gap_tolerance, rel_tol=TOL)))
        )

    def __hash__(self) -> int:
        return hash((
            self.tube,
            tuple(self.terminus.segments),
            relative_round(self.bottom_pos, TOL),
            self.wrapper,
            self.outer_material,
            None if self.gap_tolerance is None else relative_round(self.gap_tolerance, TOL),
        ))

    def get_materials(self) -> List[Material]:
        materials = list(self.terminus.get_materials())
        materials.extend([
            self.tube.fill_material,
            self.tube.material,
        ])
        if self.wrapper is not None:
            materials.extend(zone.material for zone in self.wrapper.cross_section.zones)
        materials.append(self.outer_material)
        return unique_materials(materials)

    def as_stack(self) -> CylindricalStack:
        """Return the PNT as a cylindrical stack.

        Returns
        -------
        CylindricalStack
            PNT segments ordered from bottom to top.
        """

        segments = [Stack.Segment(segment.element, segment.length)
                    for segment in self.terminus.segments]

        pincell = self.pincell
        if self.wrapper is None:
            segments.append(Stack.Segment(pincell["tube"], self.tube.length))
        else:
            wrapped_tube = pincell["wrapped_tube"]
            assert wrapped_tube is not None
            segments.append(Stack.Segment(wrapped_tube, self.wrapper.length))
            if self.wrapper.length < self.tube.length:
                segments.append(Stack.Segment(
                    pincell["tube"],
                    self.tube.length - self.wrapper.length,
                ))

        return CylindricalStack(segments=segments, name=self.name, bottom_pos=self.bottom_pos)

    @staticmethod
    def build_tube_pincell(tube:           Tube,
                           outer_material: Optional[Material] = None,
                           gap_tolerance:  Optional[float] = None,
                           name:           str = "pnt_tube") -> CylindricalPinCell:
        """Build the unwrapped PNT tube cross section.

        Parameters
        ----------
        tube : PNT.Tube
            Inner transport tube specification.
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        gap_tolerance : float, optional
            Minimum radial-zone thickness to retain (defaults to ``None``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the unwrapped transport tube.
        """

        outer_material = outer_material or Water()
        radii = [tube.inner_radius, tube.outer_radius]
        materials = [tube.fill_material, tube.material, outer_material]
        return CylindricalPinCell(
            radii=radii,
            materials=materials,
            name=name,
            min_zone_thickness=gap_tolerance,
        )

    @staticmethod
    def build_wrapped_tube_pincell(tube:           Tube,
                                   wrapper:        Wrapper,
                                   outer_material: Optional[Material] = None,
                                   gap_tolerance:  Optional[float] = None,
                                   name:           str = "pnt_wrapped_tube") -> CylindricalPinCell:
        """Build the wrapped PNT tube cross section.

        Parameters
        ----------
        tube : PNT.Tube
            Inner transport tube specification.
        wrapper : PNT.Wrapper
            Wrapper specification containing the radial zones outside the
            transport tube.
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        gap_tolerance : float, optional
            Minimum radial-zone thickness to retain (defaults to ``None``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the wrapped transport tube.
        """

        outer_material = outer_material or Water()
        first_wrapper_radius = wrapper.cross_section.zones[0].shape.outer_radius
        assert first_wrapper_radius > tube.outer_radius, (
            "PNT wrapper cross-section innermost radius must exceed the tube outer radius."
        )
        radii = [tube.inner_radius, tube.outer_radius]
        radii.extend(zone.shape.outer_radius for zone in wrapper.cross_section.zones)
        materials = [tube.fill_material, tube.material]
        materials.extend(zone.material for zone in wrapper.cross_section.zones)
        materials.append(outer_material)
        return CylindricalPinCell(
            radii=radii,
            materials=materials,
            name=name,
            min_zone_thickness=gap_tolerance,
        )

    @staticmethod
    def build_terminus_stack(terminus:       CylindricalStack,
                             outer_material: Optional[Material] = None,
                             name:           str = "pnt_terminus") -> CylindricalStack:
        """Build a PNT-local copy of the terminus.

        Parameters
        ----------
        terminus : CylindricalStack
            Source terminus segments. Its ``bottom_pos`` and segment outer
            materials are ignored.
        outer_material : Material, optional
            Exterior/coolant material assigned to every segment (defaults to
            ``Water``).
        name : str, optional
            Name for the terminus stack.

        Returns
        -------
        CylindricalStack
            Terminus with its original bounded zones and lengths, a zero local
            bottom position, and the supplied common outer material.
        """

        outer_material = outer_material or Water()
        segments = []
        for segment in terminus.segments:
            radii = [zone.shape.outer_radius for zone in segment.element.zones]
            materials = [zone.material for zone in segment.element.zones]
            materials.append(outer_material)
            pincell = CylindricalPinCell(
                radii=radii,
                materials=materials,
                name=segment.element.name,
            )
            segments.append(Stack.Segment(pincell, segment.length))

        return CylindricalStack(segments=segments, name=name, bottom_pos=0.0)

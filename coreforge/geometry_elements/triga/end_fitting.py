from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt
from typing import List, Literal, Optional

from mpactpy.utils import (
    equal_thickness_ndivs,
    relative_round,
    ROUNDING_RELATIVE_TOLERANCE as TOL,
)

from coreforge.geometry_elements.cone import OneSidedCone
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.cylindrical_stack import CylindricalStack
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Material


@dataclass(frozen=True, eq=False)
class EndFitting:
    """TRIGA end fitting specification, approximated as a clipped cone.

    Parameters
    ----------
    length : float
        Cone length from base to apex [cm].
    r2 : float
        Square of the cone slope ``(dr/dz)^2``.
    direction : {'up', 'down'}
        Orientation of the fitting in a bottom-to-top stack.
    material : Material
        Fitting material.
    """

    length: float
    r2: float
    direction: Literal["up", "down"]
    material: Material

    def __post_init__(self) -> None:
        assert self.length > 0.0, "End Fitting length must be positive."
        assert self.r2 > 0.0, "End Fitting r2 must be positive."
        assert self.direction in ("up", "down"), (
            "End Fitting direction must be either 'up' or 'down'."
        )

    def cone(self, outer_material: Material, name: str = "end_fitting_cone") -> OneSidedCone:
        """Create the unclipped cone geometry element for this end fitting."""
        return OneSidedCone(fill_material  = self.material,
                            outer_material = outer_material,
                            r              = sqrt(self.r2) * self.length,
                            h              = self.length,
                            name           = name)

    def as_stack(
        self,
        outer_material: Material,
        bottom_pos: float = 0.0,
        target_axial_thickness: Optional[float] = None,
        max_radius: Optional[float] = None,
        name: str = "end_fitting",
    ) -> CylindricalStack:
        """Create a stack representation of the clipped end fitting.

        When ``max_radius`` clips the cone base, the cylindrical portion is
        modeled exactly using ``max_radius``. The remaining taper is
        approximated with volume-preserving cone stack segments.
        """
        if target_axial_thickness is None:
            target_axial_thickness = self.length
        assert target_axial_thickness > 0.0, \
            f"target_axial_thickness = {target_axial_thickness}"

        stack_options = OneSidedCone.StackOptions(
            target_axial_length=target_axial_thickness)

        cone = self.cone(outer_material=outer_material, name=name)
        if (max_radius is None or max_radius >= cone.r or
            isclose(max_radius, cone.r, rel_tol=TOL)):

            return cone.as_stack(bottom_pos    = bottom_pos,
                                 stack_options = stack_options,
                                 direction     = self.direction)

        assert max_radius > 0.0, f"max_radius = {max_radius}"

        def equal_target_lengths(length: float, target_thickness: float) -> List[float]:
            num_div = equal_thickness_ndivs([length], target_thickness)[0]
            return [length / num_div for _ in range(num_div)]

        cylinder_length  = cone.h * (1.0 - max_radius / cone.r)
        cylinder_lengths = equal_target_lengths(cylinder_length, target_axial_thickness)
        cone_length      = cone.h - cylinder_length
        cone_lengths     = equal_target_lengths(cone_length, target_axial_thickness)

        def cylinder_segment(index: int, length: float) -> Stack.Segment:
            return Stack.Segment(
                length  = length,
                element = CylindricalPinCell(
                    radii     = [max_radius],
                    materials = [self.material, outer_material],
                    name      = f"{name}_cylinder_{index:02d}_pincell"))

        cylinder_segments = [cylinder_segment(i, length)
                             for i, length in enumerate(cylinder_lengths)]

        cone_segments = OneSidedCone(fill_material  = self.material,
                                     outer_material = outer_material,
                                     r              = max_radius,
                                     h              = cone_length,
                                     name           = f"{name}_cone").as_stack(
            stack_options = OneSidedCone.StackOptions(segment_lengths=cone_lengths),
            direction     = "up").segments

        segments = cylinder_segments + cone_segments
        if self.direction == "down":
            segments = list(reversed(segments))

        return CylindricalStack(segments=segments, name=name, bottom_pos=bottom_pos)

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (isinstance(other, EndFitting) and
                isclose(self.length, other.length, rel_tol=TOL) and
                isclose(self.r2, other.r2, rel_tol=TOL) and
                self.direction == other.direction and
                self.material == other.material)

    def __hash__(self) -> int:
        return hash((relative_round(self.length, TOL),
                     relative_round(self.r2, TOL),
                     self.direction,
                     self.material))

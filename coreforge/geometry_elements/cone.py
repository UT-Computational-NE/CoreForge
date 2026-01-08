from __future__ import annotations

from math import ceil, isclose, sqrt
from typing import Any, List, Optional

from mpactpy.utils import ROUNDING_RELATIVE_TOLERANCE as TOL
from mpactpy.utils import relative_round

from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Material
from coreforge.shapes import OneSidedCone as OneSidedConeShape


class OneSidedCone(GeometryElement):
	"""A geometry element representing a one-sided cone (flat base + single apex).

	Parameters
	----------
	fill_material : Material
		Material filling the cone interior.
	outer_material : Material
		Material filling the region outside the cone.
	r : Optional[float]
		Cone base radius (cm). Must be provided with ``h`` when ``cone`` is not
		provided.
	h : Optional[float]
		Cone height (cm). Must be provided with ``r`` when ``cone`` is not
		provided.
	cone : Optional[OneSidedConeShape]
		A pre-constructed one-sided cone shape. If provided, ``r`` and ``h`` must
		be omitted.
	name : str
		Name for the geometry element.

	Attributes
	----------
	shape : OneSidedConeShape
		The underlying one-sided cone shape.
	r : float
		Cone base radius (cm).
	h : float
		Cone height (cm).
	fill_material : Material
		Material filling the cone interior.
	outer_material : Material
		Material filling the region outside the cone.
	"""

	@property
	def shape(self) -> OneSidedConeShape:
		return self._shape

	@property
	def r(self) -> float:
		return self.shape.r

	@property
	def h(self) -> float:
		return self.shape.h

	@property
	def fill_material(self) -> Material:
		return self._fill_material

	@property
	def outer_material(self) -> Material:
		return self._outer_material

	def __init__(self,
		         fill_material:  Material,
		         outer_material: Material,
		         r:              Optional[float] = None,
		         h:              Optional[float] = None,
		         cone:           Optional[OneSidedConeShape] = None,
		         name:           str = "cone",
	):
		if cone is None:
			assert r is not None and h is not None, "Must provide either (r, h) or cone"
			cone = OneSidedConeShape(r=r, h=h)
		else:
			assert r is None and h is None, "Provide either (r, h) or cone, not both"
			assert isinstance(cone, OneSidedConeShape), f"cone must be OneSidedCone shape (got {type(cone)})"

		assert isinstance(fill_material, Material), f"fill_material must be Material (got {type(fill_material)})"
		assert isinstance(outer_material, Material), f"outer_material must be Material (got {type(outer_material)})"

		self._shape          = cone
		self._fill_material  = fill_material
		self._outer_material = outer_material
		super().__init__(name)

	def __eq__(self, other: Any) -> bool:
		if self is other:
			return True
		return (isinstance(other, OneSidedCone)
			    and self.shape          == other.shape
			    and self.fill_material  == other.fill_material
			    and self.outer_material == other.outer_material)

	def __hash__(self) -> int:
		return hash((self.shape,
			         self.fill_material,
			         self.outer_material))

	def as_stack(self,
		         bottom_pos:          float = 0.0,
		         n:                   Optional[int] = None,
		         target_axial_length: Optional[float] = None,
		         segment_lengths:     Optional[List[float]] = None,
		         direction:           str = "up",
	) -> Stack:
		"""Convert the cone into a volume-preserving stack of cylinders.

		The cone is approximated by Z-axis aligned cylinders, one per axial slice.
		The cylinder radius for each slice is chosen to preserve the cone volume
		within that slice.

		Exactly one of n, target_axial_length, or segment_lengths may be provided.
		If none are provided, a single segment is used.

		Parameters
		----------
		bottom_pos : float
			The axial position of the bottom of the stack (cm)
		n : Optional[int]
			Number of equal-height segments.
		target_axial_length : Optional[float]
			Maximum segment length; the smallest n is chosen such that each segment
			length is <= target_axial_length.
		segment_lengths : Optional[List[float]]
			Explicit segment lengths; must sum to cone height h.
		direction : str
			Segment ordering: "up" (base->apex) or "down" (apex->base).

		Returns
		-------
		Stack
			Stack approximating the cone.
		"""

		assert direction in ("up", "down"), f"direction must be 'up' or 'down' (got {direction})"

		lengths = self._determine_segment_lengths(n                   = n,
			                                      target_axial_length = target_axial_length,
			                                      segment_lengths     = segment_lengths)

		segments: List[Stack.Segment] = []
		z = 0.0
		for i, dz in enumerate(lengths):
			z0 = z
			z1 = z + dz
			r0 = self.r * (1.0 - z0 / self.h)
			r1 = self.r * (1.0 - z1 / self.h)
			r_eq = sqrt((r0 * r0 + r0 * r1 + r1 * r1) / 3.0)

			pincell = CylindricalPinCell(radii     = [r_eq],
				                         materials = [self.fill_material, self.outer_material],
				                         name      = f"{self.name}_{i:02d}_pincell")
			segments.append(Stack.Segment(element=pincell, length=dz))
			z = z1

		if direction == "down":
			segments = list(reversed(segments))

		return Stack(segments=segments, name=self.name, bottom_pos=bottom_pos)


	def _determine_segment_lengths(self,
		                           n:                   Optional[int],
		                           target_axial_length: Optional[float],
		                           segment_lengths:     Optional[List[float]],
	) -> List[float]:
		"""Determine the axial segment lengths for a cone-to-stack conversion.

		Exactly one of ``n``, ``target_axial_length``, or ``segment_lengths`` may be
		provided. If none are provided, a single segment spanning the full cone
		height is used.

		Parameters
		----------
		n : Optional[int]
			Number of equal-length axial segments.
		target_axial_length : Optional[float]
			Maximum segment length (cm). The smallest ``n`` is chosen such that each
			segment length is less than or equal to ``target_axial_length``.
		segment_lengths : Optional[List[float]]
			Explicit axial segment lengths (cm). All entries must be positive and the
			list must sum to the cone height.

		Returns
		-------
		List[float]
			A list of axial segment lengths (cm) that sum to the cone height.
		"""
		specified = [n is not None, target_axial_length is not None, segment_lengths is not None]
		assert sum(1 for x in specified if x) <= 1, "Specify at most one of n, target_axial_length, segment_lengths"

		if segment_lengths is not None:
			assert len(segment_lengths) > 0, "segment_lengths must be non-empty"
			assert all(length > 0.0 for length in segment_lengths), "All segment lengths must be > 0"
			total = sum(segment_lengths)
			assert isclose(total, self.h, rel_tol=TOL, abs_tol=TOL * max(1.0, self.h)), \
				f"segment_lengths must sum to cone height h={self.h} (got {total})"
			return list(segment_lengths)

		if target_axial_length is not None:
			assert target_axial_length > 0.0, f"target_axial_length = {target_axial_length}"
			# Smallest n such that h/n <= target_axial_length.
			n = max(1, int(ceil(self.h / target_axial_length)))

		if n is None:
			n = 1

		assert n >= 1, f"n = {n}"
		dz = self.h / n
		return [dz for _ in range(n)]



from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import mpactpy

from coreforge import geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl
from coreforge.mpact_builder.builder import AxisBounds, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs
from coreforge.mpact_builder.mpact_builder import build, register_builder
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.triga.core_element import CoreElement


@register_builder(geometry_elements_triga_netl.ModifiedThreeElementIrradiator)
class ModifiedThreeElementIrradiator(
    CoreElement[geometry_elements_triga_netl.ModifiedThreeElementIrradiator]
):
    """MPACT geometry builder for the NETL modified three-element irradiator."""

    @dataclass
    class Specs(BuilderSpecs):
        """Building specifications for the modified three-element irradiator.

        Each axial-feature field supplies a list of segment specifications in
        the same bottom-to-top order as ``element.pincell[name]``. A split
        feature requires two entries, one for each pin cell. Each pin cell's
        zone specifications are supplied independently using the existing
        ``CylindricalPinCell.Specs`` API. Omitted feature lists receive one
        default ``SegmentSpecs`` per pin cell at build time. When the geometry
        selects the simplified model, eliminated detailed features are ignored.

        Attributes
        ----------
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all irradiator segments.
        bottom_air : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the bottom air region.
        solid_spacer : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the solid lower spacer.
        hollow_spacer : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the hollow spacer section.
        hollow_spacer_upper_cap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the hollow spacer upper cap.
        cadmium_disk : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the cadmium disk.
        silver_disk : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the silver disk.
        b10_canister_lower_end_cap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the B-10 canister exterior-wall lower end cap.
        lower_b10_solid_section : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the solid lower B-10 section.
        b10_interior_wall_lower_cap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the B-10 canister interior-wall lower cap.
        pneumatic_sleeve_lower_cap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the pneumatic-sleeve lower cap.
        pneumatic_tube_lower_cap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the pneumatic-tube lower cap.
        lower_b10_region : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the lower annular B-10 region.
        upper_b10_region : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the upper annular B-10 region.
        b10_canister_top_cap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the B-10 canister top cap.
        inter_canister_gap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the gap between canisters.
        b4c_canister_bottom_cap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the B4C canister bottom cap.
        b4c_region : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the B4C region.
        b4c_canister_top_cap : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the B4C canister top cap.
        outer_casing_solid_upper_region : Optional[List[CoreElement.SegmentSpecs]]
            Specifications for the modeled solid upper region of the outer casing.
        """

        material_specs: Optional[MaterialSpecs] = None
        bottom_air: Optional[List[CoreElement.SegmentSpecs]] = None
        solid_spacer: Optional[List[CoreElement.SegmentSpecs]] = None
        hollow_spacer: Optional[List[CoreElement.SegmentSpecs]] = None
        hollow_spacer_upper_cap: Optional[List[CoreElement.SegmentSpecs]] = None
        cadmium_disk: Optional[List[CoreElement.SegmentSpecs]] = None
        silver_disk: Optional[List[CoreElement.SegmentSpecs]] = None
        b10_canister_lower_end_cap: Optional[List[CoreElement.SegmentSpecs]] = None
        lower_b10_solid_section: Optional[List[CoreElement.SegmentSpecs]] = None
        b10_interior_wall_lower_cap: Optional[List[CoreElement.SegmentSpecs]] = None
        pneumatic_sleeve_lower_cap: Optional[List[CoreElement.SegmentSpecs]] = None
        pneumatic_tube_lower_cap: Optional[List[CoreElement.SegmentSpecs]] = None
        lower_b10_region: Optional[List[CoreElement.SegmentSpecs]] = None
        upper_b10_region: Optional[List[CoreElement.SegmentSpecs]] = None
        b10_canister_top_cap: Optional[List[CoreElement.SegmentSpecs]] = None
        inter_canister_gap: Optional[List[CoreElement.SegmentSpecs]] = None
        b4c_canister_bottom_cap: Optional[List[CoreElement.SegmentSpecs]] = None
        b4c_region: Optional[List[CoreElement.SegmentSpecs]] = None
        b4c_canister_top_cap: Optional[List[CoreElement.SegmentSpecs]] = None
        outer_casing_solid_upper_region: Optional[List[CoreElement.SegmentSpecs]] = None

    def __init__(self, specs: Optional[Specs] = None):
        super().__init__(specs)

    def default_specs(self) -> Specs:
        return self.Specs()

    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs is not None else self.Specs()

    def build(
        self,
        element: geometry_elements_triga_netl.ModifiedThreeElementIrradiator,
        bounds: Optional[Bounds] = None,
    ) -> mpactpy.Core:
        """Build an MPACT representation of the modified irradiator."""

        if bounds is None:
            outer_radius = element.outer_casing.tube_2_outer_radius
            bounds = Bounds(
                X=AxisBounds(min=-outer_radius, max=outer_radius),
                Y=AxisBounds(min=-outer_radius, max=outer_radius),
            )

        stack, stack_specs = self.build_stack_and_specs(element)
        return build(stack, stack_specs, bounds)

    def _build_stack_and_specs(
        self,
        element: geometry_elements_triga_netl.ModifiedThreeElementIrradiator,
    ) -> Tuple[geometry_elements.PinCellStack, Stack.Specs]:
        """Return the irradiator stack and its segment specifications."""

        stack = element.as_stack(bottom_pos=0.0)
        specs_by_pincell = {}
        for name, region_pincells in element.pincell.items():
            region_specs = getattr(self.specs, name)
            if region_specs is None:
                region_specs = [CoreElement.SegmentSpecs() for _ in region_pincells]
            assert len(region_specs) == len(region_pincells), \
                f"'{name}' requires {len(region_pincells)} segment specifications; got {len(region_specs)}."
            specs_by_pincell.update({id(p): specs for p, specs in zip(region_pincells, region_specs)})
        segment_specs = {segment: specs_by_pincell[id(segment.element)] for segment in stack.segments}
        self._apply_material_specs(segment_specs, self.specs.material_specs)
        return stack, Stack.Specs(segment_specs)

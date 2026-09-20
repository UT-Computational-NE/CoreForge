from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

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

        Each axial-feature field supplies the segment specifications shared by
        every segment belonging to that feature. A feature may contain two
        segments when the lower end of Tube #2 splits it. When the geometry
        element selects the simplified model, fields for eliminated detailed
        features are ignored.

        Attributes
        ----------
        material_specs : Optional[MaterialSpecs]
            Default material specifications for all irradiator segments.
        bottom_air : CoreElement.SegmentSpecs
            Specifications for the bottom air region.
        solid_spacer : CoreElement.SegmentSpecs
            Specifications for the solid lower spacer.
        hollow_spacer : CoreElement.SegmentSpecs
            Specifications for the hollow spacer section.
        hollow_spacer_upper_cap : CoreElement.SegmentSpecs
            Specifications for the hollow spacer upper cap.
        cadmium_disk : CoreElement.SegmentSpecs
            Specifications for the cadmium disk.
        silver_disk : CoreElement.SegmentSpecs
            Specifications for the silver disk.
        b10_canister_lower_end_cap : CoreElement.SegmentSpecs
            Specifications for the B-10 canister exterior-wall lower end cap.
        lower_b10_solid_section : CoreElement.SegmentSpecs
            Specifications for the solid lower B-10 section.
        b10_interior_wall_lower_cap : CoreElement.SegmentSpecs
            Specifications for the B-10 canister interior-wall lower cap.
        pneumatic_sleeve_lower_cap : CoreElement.SegmentSpecs
            Specifications for the pneumatic-sleeve lower cap.
        pneumatic_tube_lower_cap : CoreElement.SegmentSpecs
            Specifications for the pneumatic-tube lower cap.
        lower_b10_region : CoreElement.SegmentSpecs
            Specifications for the lower annular B-10 region.
        upper_b10_region : CoreElement.SegmentSpecs
            Specifications for the upper annular B-10 region.
        b10_canister_top_cap : CoreElement.SegmentSpecs
            Specifications for the B-10 canister top cap.
        inter_canister_gap : CoreElement.SegmentSpecs
            Specifications for the gap between canisters.
        b4c_canister_bottom_cap : CoreElement.SegmentSpecs
            Specifications for the B4C canister bottom cap.
        b4c_region : CoreElement.SegmentSpecs
            Specifications for the B4C region.
        b4c_canister_top_cap : CoreElement.SegmentSpecs
            Specifications for the B4C canister top cap.
        outer_casing_solid_upper_end : CoreElement.SegmentSpecs
            Specifications for the solid upper end of the outer casing.
        """

        material_specs: Optional[MaterialSpecs] = None
        bottom_air: Optional[CoreElement.SegmentSpecs] = field(default_factory=CoreElement.SegmentSpecs)
        solid_spacer: Optional[CoreElement.SegmentSpecs] = field(default_factory=CoreElement.SegmentSpecs)
        hollow_spacer: Optional[CoreElement.SegmentSpecs] = field(default_factory=CoreElement.SegmentSpecs)
        hollow_spacer_upper_cap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        cadmium_disk: Optional[CoreElement.SegmentSpecs] = field(default_factory=CoreElement.SegmentSpecs)
        silver_disk: Optional[CoreElement.SegmentSpecs] = field(default_factory=CoreElement.SegmentSpecs)
        b10_canister_lower_end_cap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        lower_b10_solid_section: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        b10_interior_wall_lower_cap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        pneumatic_sleeve_lower_cap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        pneumatic_tube_lower_cap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        lower_b10_region: Optional[CoreElement.SegmentSpecs] = field(default_factory=CoreElement.SegmentSpecs)
        upper_b10_region: Optional[CoreElement.SegmentSpecs] = field(default_factory=CoreElement.SegmentSpecs)
        b10_canister_top_cap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        inter_canister_gap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        b4c_canister_bottom_cap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        b4c_region: Optional[CoreElement.SegmentSpecs] = field(default_factory=CoreElement.SegmentSpecs)
        b4c_canister_top_cap: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )
        outer_casing_solid_upper_end: Optional[CoreElement.SegmentSpecs] = field(
            default_factory=CoreElement.SegmentSpecs
        )

        def __post_init__(self) -> None:
            self.bottom_air = self.bottom_air or CoreElement.SegmentSpecs()
            self.solid_spacer = self.solid_spacer or CoreElement.SegmentSpecs()
            self.hollow_spacer = self.hollow_spacer or CoreElement.SegmentSpecs()
            self.hollow_spacer_upper_cap = self.hollow_spacer_upper_cap or CoreElement.SegmentSpecs()
            self.cadmium_disk = self.cadmium_disk or CoreElement.SegmentSpecs()
            self.silver_disk = self.silver_disk or CoreElement.SegmentSpecs()
            self.b10_canister_lower_end_cap = self.b10_canister_lower_end_cap or CoreElement.SegmentSpecs()
            self.lower_b10_solid_section = self.lower_b10_solid_section or CoreElement.SegmentSpecs()
            self.b10_interior_wall_lower_cap = self.b10_interior_wall_lower_cap or CoreElement.SegmentSpecs()
            self.pneumatic_sleeve_lower_cap = self.pneumatic_sleeve_lower_cap or CoreElement.SegmentSpecs()
            self.pneumatic_tube_lower_cap = self.pneumatic_tube_lower_cap or CoreElement.SegmentSpecs()
            self.lower_b10_region = self.lower_b10_region or CoreElement.SegmentSpecs()
            self.upper_b10_region = self.upper_b10_region or CoreElement.SegmentSpecs()
            self.b10_canister_top_cap = self.b10_canister_top_cap or CoreElement.SegmentSpecs()
            self.inter_canister_gap = self.inter_canister_gap or CoreElement.SegmentSpecs()
            self.b4c_canister_bottom_cap = self.b4c_canister_bottom_cap or CoreElement.SegmentSpecs()
            self.b4c_region = self.b4c_region or CoreElement.SegmentSpecs()
            self.b4c_canister_top_cap = self.b4c_canister_top_cap or CoreElement.SegmentSpecs()
            self.outer_casing_solid_upper_end = (
                self.outer_casing_solid_upper_end or CoreElement.SegmentSpecs()
            )

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
    ) -> Tuple[geometry_elements.CylindricalStack, Stack.Specs]:
        """Return the irradiator stack and its segment specifications."""

        stack = element.as_stack(bottom_pos=0.0)
        segment_specs = {}
        segment_index = 0
        for region_name, region_pincells in element.pincell.items():
            region_specs = getattr(self.specs, region_name)
            for _ in region_pincells:
                segment_specs[stack.segments[segment_index]] = region_specs
                segment_index += 1

        assert segment_index == len(stack.segments)
        self._apply_material_specs(segment_specs, self.specs.material_specs)
        return stack, Stack.Specs(segment_specs)

from dataclasses import dataclass
from typing import Optional
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.msre.block import Block
import coreforge.geometry_elements.msre as geometry_elements_msre

@register_builder(geometry_elements_msre.Stringer)
class Stringer:
    """ An MPACT geometry builder class for an MSRE Stringer

    Parameters
    ----------
    specs: Optional[Specs]
        Specifications for building the MPACT representation of this element

    Attributes
    ----------
    specs: Optional[Specs]
        Specifications for building the MPACT representation of this element

    """

    @dataclass
    class Specs(BuilderSpecs):
        """ Building specifications for Stringer

        Attributes
        ----------
        block_specs : Block.Specs
            The specifications to use for the stringer block
        target_axial_thicknesses : float
            The target thickness of the cells in terms of segment length (cm).
            Cells will be subdivided to limit cells to within this thickness.
        """

        block_specs:              Optional[Block.Specs] = None
        target_axial_thicknesses: Optional[float] = None

        def __post_init__(self):
            if not self.target_axial_thicknesses:
                self.target_axial_thicknesses = inf

            assert self.target_axial_thicknesses > 0.0, \
                f"target_axial_thicknesses = {self.target_axial_thicknesses}"

            if not self.block_specs:
                self.block_specs = Block.Specs()


    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else Stringer.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


    def build(self, element: geometry_elements_msre.Stringer, bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of an MSRE Stringer

        Parameters
        ----------
        element: geometry_elements_msre.Stringer
            The geometry element to be built
        bounds: Optional[Bounds]
            The spatial bounds for the geometry.

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        stack = element.as_stack()
        segment_specs = Stack.Segment.Specs(self.specs.target_axial_thicknesses,
                                            self.specs.block_specs)
        stack_specs = Stack.Specs({stack.segments[0]: segment_specs})

        return build(element.as_stack(), stack_specs, bounds)

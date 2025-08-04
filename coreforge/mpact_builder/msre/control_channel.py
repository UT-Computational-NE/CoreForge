from dataclasses import dataclass
from typing import Optional
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.stack import Stack
from coreforge.mpact_builder.cylindrical_pincell import CylindricalPinCell
import coreforge.geometry_elements.msre as geometry_elements_msre

@register_builder(geometry_elements_msre.ControlChannel)
class ControlChannel:
    """ An MPACT geometry builder class for an MSRE ControlChannel

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
        """ Building specifications for ControlChannel

        Attributes
        ----------
        pincell_specs : CylindricalPinCell.Specs
            The specifications to use for the control channel cylindrical pincells
        target_axial_thicknesses : float
            The target thickness of the cells in terms of segment length (cm).
            Cells will be subdivided to limit cells to within this thickness.
        """

        pincell_specs:            Optional[CylindricalPinCell.Specs] = None
        target_axial_thicknesses: Optional[float] = None

        def __post_init__(self):
            if not self.target_axial_thicknesses:
                self.target_axial_thicknesses = inf

            assert self.target_axial_thicknesses > 0.0, \
                f"target_axial_thicknesses = {self.target_axial_thicknesses}"

            if not self.pincell_specs:
                self.pincell_specs = CylindricalPinCell.Specs()


    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else ControlChannel.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


    def build(self, element: geometry_elements_msre.ControlChannel) -> mpactpy.Core:
        """ Method for building an MPACT geometry of an MSRE ControlChannel

        Parameters
        ----------
        element: geometry_elements_msre.ControlChannel
            The geometry element to be built

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        stack = element.as_stack()
        segment_specs = Stack.Segment.Specs(self.specs.target_axial_thicknesses,
                                            self.specs.pincell_specs)
        stack_specs = Stack.Specs({segment: segment_specs for segment in stack.segments})

        return build(element.as_stack(), stack_specs)

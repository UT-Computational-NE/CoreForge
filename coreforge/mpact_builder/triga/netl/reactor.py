from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build, get_builder
from coreforge.mpact_builder.builder import Bounds, Builder
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.stack import Stack
import coreforge.geometry_elements as geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


@register_builder(geometry_elements_triga_netl.Reactor)
class Reactor(Builder[geometry_elements_triga_netl.Reactor]):
    """ An MPACT geometry builder class for a TRIGA NETL Reactor

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
        """ Building specifications for Reactor

        Attributes
        ----------
        """



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


    def build(self,
              element: geometry_elements_triga_netl.Reactor,
              bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a TRIGA NETL Reactor

        Parameters
        ----------
        element: geometry_elements_triga_netl.Reactor
            The geometry element to be built
        bounds: Optional[Bounds]
            The spatial bounds for the geometry.

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """
        raise NotImplementedError("MPACT builder for Reactor is not implemented yet.")


def build_core_element(
    core_location: str,
    upper_grid_plate: geometry_elements_triga_netl.Reactor.GridPlate,
    lower_grid_plate: geometry_elements_triga_netl.Reactor.GridPlate,
    element: Optional[geometry_elements_triga_netl.Core.Element] = None,
    element_bottom_axial_position: Optional[float] = None,
    axial_bounds: Optional[tuple[float, float]] = None,
    outer_material: Optional[geometry_elements_triga_netl.Material] = None,
    element_specs: Optional[BuilderSpecs] = None,
    coolant_region_specs: Optional[Stack.Segment.Specs] = None,
) -> Optional[Tuple[geometry_elements.Stack, Stack.Specs]]:
    """Helper to build an MPACT core for a single element with grid plates.

    This function is intended only for core locations with grid plate penetrations.
    Non-element axial regions are represented as coolant pincells that use the
    upper/lower penetration radii as mesh boundaries.

    Parameters
    ----------
    core_location : str
        Core location identifier (e.g., ``"C-07"``) used to look up grid plate
        penetration radii.
    upper_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate
        Upper grid plate geometry and placement.
    lower_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate
        Lower grid plate geometry and placement.
    element : geometry_elements_triga_netl.Core.Element, optional
        Core element to place in the cell. When omitted, only the grid plates and outer
        material will be present in the returned universe.
    element_bottom_axial_position : float, optional
        Axial z-position (cm) of the element bottom relative to the core centerline.
    axial_bounds : Optional[tuple[float, float]],
        Lower and upper axial bounds (cm) for the constructed core.
        Defaults to top of upper grid plate or core element and bottom of lower grid plate or core element,
        whichever are more extreme.
    outer_material : Material, optional
        Material filling the region outside the element and grid plates. If omitted
        and ``element`` is provided, the element's ``outer_material`` is used. If
        ``element`` is ``None``, this must be provided.
    element_specs : Optional[BuilderSpecs]
        Builder specifications for the core element. If omitted, the element's
        builder defaults are used.
    coolant_region_specs : Optional[Stack.Segment.Specs]
        Specifications for coolant-only regions above/below the core element.
        Defaults to ``Stack.Segment.Specs()`` when omitted.

    Returns
    -------
    Optional[Tuple[geometry_elements.Stack, Stack.Specs]]
        Stack and corresponding specs for the core element with grid plates and non-core axial regions.
        Returns ``None`` if there is no element and no grid plate penetrations at the specified core location.
    """

    pass


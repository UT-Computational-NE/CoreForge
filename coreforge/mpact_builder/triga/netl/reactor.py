from __future__ import annotations
from typing import Optional
from dataclasses import dataclass

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


@register_builder(geometry_elements_triga_netl.Reactor)
class Reactor:
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


    @property
    def specs(self) -> Optional[Specs]:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else Reactor.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


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
    element: Optional[geometry_elements_triga_netl.Core.Element] = None,
    core_location: Optional[str] = None,
    element_bottom_axial_position: Optional[float] = None,
    outer_material: Optional[geometry_elements_triga_netl.Material] = None,
    upper_grid_plate: Optional[geometry_elements_triga_netl.Reactor.GridPlate] = None,
    lower_grid_plate: Optional[geometry_elements_triga_netl.Reactor.GridPlate] = None,
    bounds: Optional[Bounds] = None,
) -> mpactpy.Core:
    """Helper to build an MPACT core for a single element with optional grid plates.

    Parameters
    ----------
    element : geometry_elements_triga_netl.Core.Element, optional
        Core element to place in the cell.
    core_location : str, optional
        Core location identifier (e.g., ``"C-07"``) used to look up grid plate
        penetration radii.
    element_bottom_axial_position : float, optional
        Axial z-position (cm) of the element bottom relative to the core centerline.
    outer_material : Material, optional
        Material filling the region outside the element and grid plates.
    upper_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate, optional
        Upper grid plate geometry and placement.
    lower_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate, optional
        Lower grid plate geometry and placement.
    bounds : Optional[Bounds]
        The spatial bounds for the geometry.

    Returns
    -------
    mpactpy.Core
        Core containing the element (if provided) and any grid plate regions.
    """
    raise NotImplementedError("MPACT build_core_element is not implemented yet.")

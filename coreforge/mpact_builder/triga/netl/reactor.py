from __future__ import annotations
from typing import Optional, Protocol, Tuple
from dataclasses import dataclass, field
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build
from coreforge.mpact_builder.builder import Bounds, Builder
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.cylindrical_pincell import CylindricalPinCell
from coreforge.mpact_builder.stack import Stack
import coreforge.geometry_elements as geometry_elements
import coreforge.geometry_elements.triga.netl as geometry_elements_triga_netl


class CoreElementBuilder(Protocol):
    def build_stack_and_specs(
        self,
        element: geometry_elements.GeometryElement,
    ) -> Tuple[geometry_elements.Stack, Stack.Specs]:
        ...


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

    @dataclass
    class PincellRegionSpecs(BuilderSpecs):
        """ Building specifications for a core stack region.

        Attributes
        ----------
        target_axial_thickness : float
            Target axial thickness for segment subdivision (cm).
        pincell_specs : CylindricalPinCell.Specs
            Specifications for building the region pincell.
        """

        target_axial_thickness: Optional[float] = None
        pincell_specs:          Optional[CylindricalPinCell.Specs] = None

        def __post_init__(self):
            if not self.target_axial_thickness:
                self.target_axial_thickness = inf

            assert self.target_axial_thickness > 0.0, \
                f"target_axial_thickness = {self.target_axial_thickness}"

            if not self.pincell_specs:
                self.pincell_specs = CylindricalPinCell.Specs()

    @dataclass
    class CoreStackSpecs(BuilderSpecs):
        """ Building specifications for core stack regions outside the element.

        Attributes
        ----------
        grid_region_specs : PincellRegionSpecs
            Specs for grid plate regions.
        coolant_region_specs : PincellRegionSpecs
            Specs for coolant regions above/below the grid plates or when no element is present.
        """

        grid_region_specs: Optional[Reactor.PincellRegionSpecs] = field(
            default_factory=lambda: Reactor.PincellRegionSpecs()
        )
        coolant_region_specs: Optional[Reactor.PincellRegionSpecs] = field(
            default_factory=lambda: Reactor.PincellRegionSpecs()
        )

        def __post_init__(self):
            self.grid_region_specs = self.grid_region_specs or Reactor.PincellRegionSpecs()
            self.coolant_region_specs = self.coolant_region_specs or Reactor.PincellRegionSpecs()


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
    element_builder_specs: Optional[BuilderSpecs]= None,
    core_stack_specs: Optional[Reactor.CoreStackSpecs] = None,
    outer_material: Optional[geometry_elements_triga_netl.Material] = None,
    axial_bounds: Optional[tuple[float, float]] = None,
    unionize_radial_mesh: bool = False,
) -> Tuple[geometry_elements.Stack, Stack.Specs]:
    """Helper to build an MPACT core for a single element with grid plates.

    This function is intended only for core locations with grid plate penetrations.

    Parameters
    ----------
    element : geometry_elements_triga_netl.Core.Element, optional
        Core element to place in the cell. When omitted, only the grid plates and outer
        material will be present in the returned universe.
    element_builder_specs : Optional[BuilderSpecs]
        Builder specifications to use when constructing the core element.
        Defaults to the default builder specifications for the element type.
    core_stack_specs : Optional[Reactor.CoreStackSpecs]
        Specifications for grid plate and coolant-only regions when building the core element.
    core_location : str
        Core location identifier (e.g., ``"C-07"``) used to look up grid plate
        penetration radii.
    element_bottom_axial_position : float, optional
        Axial z-position (cm) of the element bottom relative to the core centerline.
    axial_bounds : Optional[tuple[float, float]],
        Lower and upper axial bounds (cm) for the constructed core.
        Defaults to top of upper grid plate or core element and bottom of lower grid plate or core element,
        whichever are more extreme.
    outer_material : openmc.Material, optional
        Material filling the region outside the element and grid plates. If omitted
        and ``element`` is provided, the element's ``outer_material`` is used. If
        ``element`` is ``None``, this must be provided.
    upper_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate
        Upper grid plate geometry and placement.
    lower_grid_plate : geometry_elements_triga_netl.Reactor.GridPlate
        Lower grid plate geometry and placement.
    unionize_radial_mesh : bool = False
        If True, unionize the radial mesh across any stacked/segmented regions.

    Returns
    -------
    Tuple[geometry_elements.Stack, Stack.Specs]
        Stack and corresponding specs for the core element with optional grid plates and non-core axial regions.
    """

    if element is not None:
        assert element_bottom_axial_position is not None, \
            "element_bottom_axial_position must be provided when element is provided."
        if outer_material is None:
            outer_material = element.outer_material
    else:
        assert outer_material is not None, \
            "outer_material must be provided when element is None."

    if core_stack_specs is None:
        core_stack_specs = Reactor.CoreStackSpecs()

    upper_radius = upper_grid_plate.geometry.penetration_map.get(core_location)
    assert upper_radius is not None, (
        f"Upper grid plate has no penetration at core location {core_location}."
    )
    lower_radius = lower_grid_plate.geometry.penetration_map.get(core_location)
    assert lower_radius is not None, (
        f"Lower grid plate has no penetration at core location {core_location}."
    )

    if axial_bounds is None:
        axial_bounds = (-(lower_grid_plate.top_to_core_centerline_distance +
                              lower_grid_plate.geometry.thickness),
                        upper_grid_plate.top_to_core_centerline_distance)

        if element is not None:
            axial_bounds = (min(axial_bounds[0], element_bottom_axial_position),
                            max(axial_bounds[1], element_bottom_axial_position + element.length))

    if core_stack_specs is None:
        core_stack_specs = Reactor.CoreStackSpecs()

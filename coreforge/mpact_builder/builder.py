from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

import mpactpy

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs, DEFAULT_MPACT_MATERIAL_SPECS

T = TypeVar("T", bound=GeometryElement)


@dataclass
class AxisBounds:
    """Bounds for a single axis.

    Attributes
    ----------
    min : float
        Minimum value for the axis.
    max : float
        Maximum value for the axis.
    """

    min: float
    max: float

    def __post_init__(self) -> None:
        if self.min >= self.max:
            raise ValueError(
                f"AxisBounds: min ({self.min}) must be less than max ({self.max})"
            )


@dataclass
class Bounds:
    """Bounds for X, Y, and Z axes.

    Attributes
    ----------
    X : Optional[AxisBounds]
        Bounds for the X axis.
    Y : Optional[AxisBounds]
        Bounds for the Y axis.
    Z : Optional[AxisBounds]
        Bounds for the Z axis.
    """

    X: Optional[AxisBounds] = None
    Y: Optional[AxisBounds] = None
    Z: Optional[AxisBounds] = None


class Builder(ABC, Generic[T]):
    """Abstract base class for MPACT geometry builders.

    Parameters
    ----------
    specs : Optional[BuilderSpecs]
        Specifications for building the MPACT representation of this element.
        If omitted, ``default_specs`` is used.

    Attributes
    ----------
    specs : BuilderSpecs
        Specifications for building the MPACT representation of this element.
    """

    def __init__(self, specs: Optional[BuilderSpecs] = None):
        if specs is None:
            specs = self.default_specs()
        self._specs = specs

    @property
    def specs(self) -> BuilderSpecs:
        return self._specs

    @abstractmethod
    def default_specs(self) -> BuilderSpecs:
        """Return the default builder specifications."""
        raise NotImplementedError

    @abstractmethod
    def build(self, element: T, bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """Build an MPACT core for the provided geometry element.

        Parameters
        ----------
        element : GeometryElement
            The geometry element to be built.
        bounds : Optional[Bounds]
            The spatial bounds for the geometry.

        Returns
        -------
        mpactpy.Core
            A new MPACT Core based on this GeometryElement.
        """
        raise NotImplementedError


def build_material(material: Material, specs: Optional[MaterialSpecs] = None) -> mpactpy.Material:
    """Function for building an MPACT Material from a given Material.

    This will first attempt to find specifications for how to build this material in specs.
    If no specifications are found in specs, then this will search the default specifications
    for the material type. If no default specifications for the material type are found, then
    the mpactpy.Material constructor default will be used.

    Parameters
    ----------
    material : Material
        The material to be built.
    specs : Optional[MaterialSpecs]
        The build specifications.

    Returns
    -------
    mpactpy.Material
        A new MPACT Material.
    """

    openmc_material = material.openmc_material

    if specs is not None and material in specs:
        mpact_specs = specs[material]
        return mpactpy.Material.from_openmc_material(openmc_material, mpact_specs)

    cls = type(material)
    while cls is not object:
        mpact_specs = DEFAULT_MPACT_MATERIAL_SPECS.get(cls)
        if mpact_specs:
            return mpactpy.Material.from_openmc_material(openmc_material, mpact_specs)
        cls = cls.__base__
    return mpactpy.Material.from_openmc_material(openmc_material)

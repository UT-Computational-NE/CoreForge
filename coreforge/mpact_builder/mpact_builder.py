from typing import Optional

import mpactpy

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.mpact_builder.builder import Bounds, Builder, build_material
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.voxel_builder import VoxelBuilder

_builder_registry = {}


def register_builder(geometry_cls):
    def decorator(builder_cls):
        _builder_registry[geometry_cls] = builder_cls
        return builder_cls
    return decorator

def get_builder(element: GeometryElement) -> Optional[Builder]:
    """ Return the registered builder class for a geometry element, if any.

    Parameters
    ----------
    element: GeometryElement
        The geometry element to find a builder for

    Returns
    -------
    Optional[Builder]
        The builder class for the geometry element, if any
    """
    cls = type(element)
    while cls is not object:
        builder_cls = _builder_registry.get(cls)
        if builder_cls:
            return builder_cls
        cls = cls.__base__
    return None

def build(element: GeometryElement, specs: Optional[BuilderSpecs] = None, bounds: Optional[Bounds] = None) -> mpactpy.Core:
    """ Function for building an MPACT Core from a GeometryElement

    Parameters
    ----------
    element: GeometryElement
        The geometry element to be built
    specs: Optional[BuilderSpecs]
        The build specifications
    bounds: Optional[Bounds]
        The spatial bounds for the geometry

    Returns
    -------
    mpactpy.Core
        A new MPACT Core based on this GeometryElement
    """

    if isinstance(specs, VoxelBuilder.Specs):
        return VoxelBuilder(specs).build(element, bounds)

    builder = get_builder(element)
    if isinstance(builder, type) and issubclass(builder, Builder):
        return builder(specs).build(element, bounds)

    raise NotImplementedError(f"No MPACT builder registered for {type(element).__name__} {element.name}")

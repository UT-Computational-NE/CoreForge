from typing import Optional

import openmc

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.openmc_builder.builder import Builder

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

def build(element: GeometryElement) -> openmc.Universe:
    """ Function for building an OpenMC Universe from a GeometryElement

    Parameters
    ----------
    element: GeometryElement
        The geometry element to be built

    Returns
    -------
    openmc.Universe
        A new OpenMC Universe based on this GeometryElement
    """
    builder = get_builder(element)
    if isinstance(builder, type) and issubclass(builder, Builder):
        return builder().build(element)
    raise NotImplementedError(f"No OpenMC builder registered for {type(element).__name__} {element.name}")

import openmc

from coreforge.geometry_elements.geometry_element import GeometryElement

_builder_registry = {}

def register_builder(geometry_cls):
    def decorator(builder_cls):
        _builder_registry[geometry_cls] = builder_cls
        return builder_cls
    return decorator

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
    cls = type(element)
    while cls is not object:
        builder_cls = _builder_registry.get(cls)
        if builder_cls:
            return builder_cls().build(element)
        cls = cls.__base__
    raise NotImplementedError(f"No MPACT builder registered for {type(element).__name__} {element.name}")

from typing import Optional

import mpactpy

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.material_specs import DEFAULT_MPACT_SPECS

_builder_registry = {}

def register_builder(geometry_cls):
    def decorator(builder_cls):
        _builder_registry[geometry_cls] = builder_cls
        return builder_cls
    return decorator

def build(element: GeometryElement, specs: Optional[BuilderSpecs] = None) -> mpactpy.Core:
    """ Function for building an MPACT Core from a GeometryElement

    Parameters
    ----------
    element: GeometryElement
        The geometry element to be built
    specs: Optional[BuilderSpecs]
        The build specifications

    Returns
    -------
    mpactpy.Core
        A new MPACT Core based on this GeometryElement
    """
    cls = type(element)
    while cls is not object:
        builder_cls = _builder_registry.get(cls)
        if builder_cls:
            return builder_cls(specs).build(element)
        cls = cls.__base__
    raise NotImplementedError(f"No MPACT builder registered for {type(element).__name__} {element.name}")

def build_material(material: Material, specs: Optional[BuilderSpecs] = None) -> mpactpy.Material:
    """ Function for building an MPACT Material from a given Material

    This will first attempt to find specifications for how to build this material in specs.
    If no specifications are found in specs, then this will search the default specifications
    for the material type.  If no default specifications for the material type are found, then
    the mpactpy.Material constructor default will be used.

    Parameters
    ----------
    material : Material
        The material to be built
    specs: Optional[BuilderSpecs]
        The build specifications

    Returns
    -------
    mpactpy.Material
        A new MPACT Material
    """

    openmc_material = material.openmc_material

    if specs and material in specs.material_specs:
        mpact_specs = specs.material_specs[material]
        return mpactpy.Material.from_openmc_material(openmc_material, mpact_specs)

    cls = type(material)
    while cls is not object:
        mpact_specs = DEFAULT_MPACT_SPECS.get(cls)
        if mpact_specs:
            return mpactpy.Material.from_openmc_material(openmc_material, mpact_specs)
        cls = cls.__base__
    return mpactpy.Material.from_openmc_material(openmc_material)

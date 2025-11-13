from typing import Optional, TypedDict
from dataclasses import dataclass

import mpactpy
import openmc

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material
from coreforge.mpact_builder.builder_specs import BuilderSpecs, VoxelBuildSpecs
from coreforge.mpact_builder.material_specs import MaterialSpecs, DEFAULT_MPACT_SPECS
from coreforge.openmc_builder import build as build_openmc_universe

_builder_registry = {}


class AxisBounds(TypedDict):
    """ Bounds for a single axis

    Attributes
    ----------
    min : float
        Minimum value for this axis
    max : float
        Maximum value for this axis
    """
    min: float
    max: float


@dataclass
class Bounds:
    """ Bounds for X, Y, and Z axes

    Attributes
    ----------
    X : Optional[AxisBounds]
        Bounds for the X axis
    Y : Optional[AxisBounds]
        Bounds for the Y axis
    Z : Optional[AxisBounds]
        Bounds for the Z axis
    """
    X: Optional[AxisBounds] = None
    Y: Optional[AxisBounds] = None
    Z: Optional[AxisBounds] = None

    def __post_init__(self):
        for axis_name in ['X', 'Y', 'Z']:
            axis_bounds = getattr(self, axis_name)
            if axis_bounds is not None:
                if axis_bounds['min'] >= axis_bounds['max']:
                    raise ValueError(
                        f"Bounds.{axis_name}: min ({axis_bounds['min']}) must be less than max ({axis_bounds['max']})"
                    )


def register_builder(geometry_cls):
    def decorator(builder_cls):
        _builder_registry[geometry_cls] = builder_cls
        return builder_cls
    return decorator

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
    if isinstance(specs, VoxelBuildSpecs):
        return build_voxelized(element, specs)

    cls = type(element)
    while cls is not object:
        builder_cls = _builder_registry.get(cls)
        if builder_cls:
            return builder_cls(specs).build(element, bounds)
        cls = cls.__base__
    return build_voxelized(element, specs)

def build_material(material: Material, specs: Optional[MaterialSpecs] = None) -> mpactpy.Material:
    """ Function for building an MPACT Material from a given Material

    This will first attempt to find specifications for how to build this material in specs.
    If no specifications are found in specs, then this will search the default specifications
    for the material type.  If no default specifications for the material type are found, then
    the mpactpy.Material constructor default will be used.

    Parameters
    ----------
    material : Material
        The material to be built
    specs: Optional[MaterialSpecs]
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



def build_voxelized(element:                GeometryElement,
                    specs:                  VoxelBuildSpecs,
                    default_material:       Optional[Material] = None,
                    default_material_specs: Optional[MaterialSpecs] = None) -> mpactpy.Core:
    """ Function for building an MPACT Core from a GeometryElement via geometry voxelation

    This function uses the openmc_builder to build an OpenMC Model of the geometry element which is
    then voxelized into an MPACTPy Core using the Core.overlay method.

    Parameters
    ----------
    element : GeometryElement
        The geometry element to be built
    specs : VoxelBuildSpecs
        The voxel build specifications
    default_material : Optional[Material]
        The material which will act as the "template" material to be replaced with
        the material read from the OpenMC overlay.  This is also the material for voxels
        where no OpenMC material is present to overlay it with.
    default_material_specs : Optional[MaterialSpecs]
        The material specifications for the default material

    Returns
    -------
    mpactpy.Core
        A new MPACT Core based on this GeometryElement
    """

    assert(specs), "User must provide a VoxelBuildSpecs when building via voxelation"

    if default_material is None:
        default_material = openmc.Material(temperature=300)
        default_material.add_nuclide('H1', 1.0)
        default_material = Material(default_material)

    openmc_geometry = openmc.Geometry(build_openmc_universe(element))

    template_material    = build_material(default_material, default_material_specs)
    num_material_regions = len(specs.x_thicknesses) * len(specs.y_thicknesses) * len(specs.z_thicknesses)
    thicknesses          = {"X": specs.x_thicknesses, "Y": specs.y_thicknesses, "Z": specs.z_thicknesses}
    materials            = [template_material] * num_material_regions

    template_pin      = mpactpy.build_rec_pin(thicknesses, materials)
    template_module   = mpactpy.Module(1, [[template_pin]])
    template_lattice  = mpactpy.Lattice([[template_module]])
    template_assembly = mpactpy.Assembly([template_lattice])
    template_core     = mpactpy.Core([[template_assembly]])

    pin_mask:      mpactpy.Pin.OverlayMask      = {template_material}
    module_mask:   mpactpy.Module.OverlayMask   = {template_pin:      pin_mask}
    lattice_mask:  mpactpy.Lattice.OverlayMask  = {template_module:   module_mask}
    assembly_mask: mpactpy.Assembly.OverlayMask = {template_lattice:  lattice_mask}
    include_only:  mpactpy.Core.OverlayMask     = {template_assembly: assembly_mask}

    return template_core.overlay(openmc_geometry, specs.offset, include_only, specs.overlay_policy)

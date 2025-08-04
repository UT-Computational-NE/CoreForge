from abc import ABC
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import mpactpy

from coreforge.mpact_builder.material_specs import MaterialSpecs


@dataclass
class BuilderSpecs(ABC):
    """ Abstract Class for Building specifications for Geometry Elements
    """

@dataclass
class VoxelBuildSpecs(BuilderSpecs):
    """ Building specifications for voxelizing the geometry

    This is a generic build specification for voxelizing an OpenMC Model into
    an MPACTPy Core.

    Attributes
    ----------
    xvals : Optional[List[float]]
        The x-coordinates marking material voxelization subdivisions (boundary values)
    yvals : Optional[List[float]]
        The y-coordinates marking material voxelization subdivisions (boundary values)
    zvals : Optional[List[float]]
        The z-coordinates marking material voxelization subdivisions (boundary values)
    x_thicknesses : Optional[List[float]]
        The x-direction thicknesses for each voxel
    y_thicknesses : Optional[List[float]]
        The y-direction thicknesses for each voxel
    z_thicknesses : Optional[List[float]]
        The z-direction thicknesses for each voxel
    material_specs : MaterialSpecs
        Specifications for how materials should be treated in MPACT
    overlay_policy : mpactpy.PinMesh.OverlayPolicy
        The specifications for how the overlay is to be performed.
        See mpactpy.PinMesh.OverlayPolicy documentation for details.
        Note that the mat_specs of the overlay_policy will be replaced
        with specifications based on material_specs.
    offset : Tuple[float, float, float]
        Offset of the OpenMC model's lower-left corner relative to the
        MPACT PinMesh lower-left. This may be required based on how the OpenMC
        Universe is built for a given GeometryElement. Default is (0.0, 0.0, 0.0)
    """

    xvals:          Optional[List[float]] = None
    yvals:          Optional[List[float]] = None
    zvals:          Optional[List[float]] = None
    x_thicknesses:  Optional[List[float]] = None
    y_thicknesses:  Optional[List[float]] = None
    z_thicknesses:  Optional[List[float]] = None
    material_specs: MaterialSpecs = field(default_factory=MaterialSpecs)
    overlay_policy: mpactpy.PinMesh.OverlayPolicy = field(default_factory=mpactpy.PinMesh.OverlayPolicy)
    offset:         Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self):
        # Validate that either boundary values or thicknesses are provided for each dimension
        for dim in ['x', 'y', 'z']:
            vals = getattr(self, f"{dim}vals")
            thicknesses = getattr(self, f"{dim}_thicknesses")

            if vals is None and thicknesses is None:
                raise ValueError(f"Either {dim}vals or {dim}_thicknesses must be provided")
            if vals is not None and thicknesses is not None:
                raise ValueError(f"Cannot specify both {dim}vals and {dim}_thicknesses")

        # Convert between boundary values and thicknesses
        for dim in ['x', 'y', 'z']:
            vals = getattr(self, f"{dim}vals")
            thicknesses = getattr(self, f"{dim}_thicknesses")

            if vals is not None:
                # Convert boundary values to thicknesses
                assert len(vals) > 0, f"len({dim}vals) = {len(vals)}"
                assert all(val > 0. for val in vals), f"{dim}vals = {vals}"
                assert all(vals[i-1] < vals[i] for i in range(1,len(vals))), f"{dim}vals = {vals}"

                # Calculate thicknesses from boundary values
                thicknesses = [vals[0]] + [vals[i] - vals[i-1] for i in range(1, len(vals))]
                setattr(self, f"{dim}_thicknesses", thicknesses)
            else:
                # Convert thicknesses to boundary values
                assert len(thicknesses) > 0, f"len({dim}_thicknesses) = {len(thicknesses)}"
                assert all(t > 0. for t in thicknesses), f"{dim}_thicknesses = {thicknesses}"

                # Calculate boundary values from thicknesses
                vals = [sum(thicknesses[:i+1]) for i in range(len(thicknesses))]
                setattr(self, f"{dim}vals", vals)

        material_specs = self.material_specs.material_specs
        self.overlay_policy.mat_specs = {mat.openmc_material: spec for mat, spec in material_specs.items()}

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, inf
from typing import Optional, Tuple, TypedDict

import mpactpy
import openmc

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material
from coreforge.mpact_builder.builder import Bounds, Builder, build_material
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs
from coreforge.openmc_builder import build as build_openmc_universe


class VoxelBuilder(Builder[GeometryElement]):
    """Builder for voxelizing geometry elements into MPACT cores."""

    @dataclass
    class Specs(BuilderSpecs):
        """Building specifications for voxelizing the geometry.

        Attributes
        ----------
        target_thicknesses : Optional[TargetThicknesses]
            Target per-axis thicknesses for voxel cells.
        num_div : Optional[NumDivisions]
            Fixed per-axis number of voxel divisions.
        material_specs : MaterialSpecs
            Specifications for how materials should be treated in MPACT.
        overlay_policy : mpactpy.PinMesh.OverlayPolicy
            The specifications for how the overlay is to be performed.
            See mpactpy.PinMesh.OverlayPolicy documentation for details.
            Note that the mat_specs of the overlay_policy will be replaced
            with specifications based on material_specs.
        offset : Tuple[float, float, float]
            Offset of the OpenMC model's lower-left corner relative to the
            MPACT PinMesh lower-left.
        """

        class TargetThicknesses(TypedDict, total=False):
            """Target per-axis thicknesses for voxel cells."""

            X: float
            Y: float
            Z: float

        class NumDivisions(TypedDict, total=False):
            """Per-axis number of voxel divisions."""

            X: int
            Y: int
            Z: int

        target_thicknesses: Optional[TargetThicknesses] = None
        num_div: Optional[NumDivisions] = None
        material_specs: MaterialSpecs = field(default_factory=dict)
        overlay_policy: mpactpy.PinMesh.OverlayPolicy = field(default_factory=mpactpy.PinMesh.OverlayPolicy)
        offset:         Tuple[float, float, float] = (0.0, 0.0, 0.0)

        def __post_init__(self) -> None:
            if self.target_thicknesses is None:
                self.target_thicknesses = {}
            if self.num_div is None:
                self.num_div = {}
            if self.material_specs is None:
                self.material_specs = {}

            valid_axes = {"X", "Y", "Z"}
            for axis in self.target_thicknesses:
                if axis not in valid_axes:
                    raise ValueError(f"Invalid axis '{axis}' in target_thicknesses.")
            for axis in self.num_div:
                if axis not in valid_axes:
                    raise ValueError(f"Invalid axis '{axis}' in num_div.")

            for axis in ["X", "Y", "Z"]:
                target = self.target_thicknesses.get(axis)
                num_div = self.num_div.get(axis)

                if target is not None and num_div is not None:
                    raise ValueError(f"Cannot specify both target_thicknesses and num_div for axis {axis}.")
                if target is None and num_div is None:
                    self.target_thicknesses[axis] = inf
                    target = inf

                if target is not None:
                    assert target > 0.0, f"target_thicknesses[{axis}] = {target}"
                if num_div is not None:
                    assert num_div > 0, f"num_div[{axis}] = {num_div}"

            self.overlay_policy.mat_specs = {mat.openmc_material: spec for mat, spec in self.material_specs.items()}

    def __init__(self,
                 specs:                  Specs,
                 default_material:       Optional[Material] = None,
                 default_material_specs: Optional[MaterialSpecs] = None) -> None:

        if specs is None:
            raise ValueError("VoxelBuilder requires VoxelBuilder.Specs.")
        super().__init__(specs)
        self._default_material = default_material
        self._default_material_specs = default_material_specs


    def default_specs(self) -> Specs:
        raise NotImplementedError("VoxelBuilder requires explicit VoxelBuilder.Specs.")


    @property
    def specs(self) -> Specs:
        return self._specs


    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        if specs is None:
            raise ValueError("VoxelBuilder requires VoxelBuilder.Specs.")
        self._specs = specs


    def build(self, element: GeometryElement, bounds: Optional[Bounds] = None) -> mpactpy.Core:
        if bounds is None or bounds.X is None or bounds.Y is None or bounds.Z is None:
            raise ValueError("VoxelBuilder requires Bounds for X, Y, and Z axes.")

        specs = self.specs
        default_material = self._default_material
        default_material_specs = self._default_material_specs

        if default_material is None:
            default_material = openmc.Material(temperature=300)
            default_material.add_nuclide("H1", 1.0)
            default_material = Material(default_material)

        openmc_geometry = openmc.Geometry(build_openmc_universe(element))

        axis_lengths = {"X": bounds.X.max - bounds.X.min,
                        "Y": bounds.Y.max - bounds.Y.min,
                        "Z": bounds.Z.max - bounds.Z.min}

        def axis_thicknesses(axis: str, length: float) -> list[float]:
            num_div = specs.num_div.get(axis)
            if num_div is None:
                target = specs.target_thicknesses.get(axis)
                if target is None:
                    raise ValueError(f"Missing target_thicknesses and num_div for axis {axis}.")
                num_div = max(1, int(ceil(length / target)))
            return [length / num_div] * num_div

        thicknesses = {axis: axis_thicknesses(axis, length) for axis, length in axis_lengths.items()}

        template_material = build_material(default_material, default_material_specs)
        num_material_regions = len(thicknesses["X"]) * len(thicknesses["Y"]) * len(thicknesses["Z"])
        materials = [template_material] * num_material_regions

        template_pin = mpactpy.build_rec_pin(thicknesses, materials)
        template_module = mpactpy.Module(1, [[template_pin]])
        template_lattice = mpactpy.Lattice([[template_module]])
        template_assembly = mpactpy.Assembly([template_lattice])
        template_core = mpactpy.Core([[template_assembly]])

        pin_mask: mpactpy.Pin.OverlayMask = {template_material}
        module_mask: mpactpy.Module.OverlayMask = {template_pin: pin_mask}
        lattice_mask: mpactpy.Lattice.OverlayMask = {template_module: module_mask}
        assembly_mask: mpactpy.Assembly.OverlayMask = {template_lattice: lattice_mask}
        include_only: mpactpy.Core.OverlayMask = {template_assembly: assembly_mask}

        return template_core.overlay(openmc_geometry, specs.offset, include_only, specs.overlay_policy)

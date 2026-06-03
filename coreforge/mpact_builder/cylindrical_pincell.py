from __future__ import annotations
from typing import Literal, Tuple, Optional, List
from dataclasses import dataclass
from math import hypot

import mpactpy

from coreforge.mpact_builder.builder import AxisBounds, Bounds, Builder, build_material
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs
from coreforge.mpact_builder.mpact_builder import register_builder
from coreforge.shapes.utils import equal_volume_ring_radii
from coreforge import geometry_elements

@register_builder(geometry_elements.CylindricalPinCell)
class CylindricalPinCell(Builder[geometry_elements.CylindricalPinCell]):
    """ An MPACT geometry builder class for CylindricalPinCell

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
    class ZoneSpecs:
        """Mesh specifications for a cylindrical pin-cell zone or outer region.

        ``ndivr_mat`` subdivides a zone into additional material regions by adding
        radial interfaces and copying the zone material into each new region.
        Each copied material region inherits the same ``ndivr_fsr`` and
        ``ndiva`` from this ``ZoneSpecs``.

        The outer-region spec applies to the material outside the outermost
        cylindrical zone. Its material subdivision radii are computed using an
        artificial circle centered on the pin-cell center and large enough to
        enclose the rectangular module boundary. That artificial final radius is
        used only for subdivision placement and is not written to the
        ``GeneralCylindricalPinMesh``.

        Attributes
        ----------
        ndivr_fsr : int
            Number of equal-volume radial FSR subdivisions to use for each
            material region created from this logical zone. This maps directly
            to ``GeneralCylindricalPinMesh.ndivr``.
        ndiva : int
            Number of equal-angle azimuthal FSR subdivisions to use for each
            radial FSR created from this logical zone. This maps directly to
            ``GeneralCylindricalPinMesh.ndiva``.
        ndivr_mat : int
            Number of radial material-region subdivisions to create from this
            logical zone. New material regions receive copies of the logical
            zone's material.
        ndivr_mat_type : Literal["equal_thickness", "equal_volume"]
            Method used to place radial material-region subdivision boundaries.
            ``"equal_thickness"`` spaces boundaries uniformly in radius.
            ``"equal_volume"`` spaces boundaries uniformly in annular area.
        """

        ndivr_fsr:      int = 1
        ndiva:          int = 1
        ndivr_mat:      int = 1
        ndivr_mat_type: Literal["equal_thickness", "equal_volume"] = "equal_thickness"

        def __post_init__(self) -> None:
            assert self.ndivr_fsr > 0, f"ndivr_fsr = {self.ndivr_fsr}"
            assert self.ndiva     > 0, f"ndiva = {self.ndiva}"
            assert self.ndivr_mat > 0, f"ndivr_mat = {self.ndivr_mat}"
            assert self.ndivr_mat_type in ("equal_thickness", "equal_volume"), \
                f"ndivr_mat_type = {self.ndivr_mat_type}"

    class Specs(BuilderSpecs):
        """Building specifications for CylindricalPinCells.

        Parameters
        ----------
        zone_specs : Optional[ZoneSpecs | List[ZoneSpecs]]
            Mesh specifications for the pin cell. A single ``ZoneSpecs``
            applies to all cylindrical zones and the outer region. A list
            specifies regions individually and must have one entry for each
            cylindrical zone plus one final entry for the outer region.
        divide_into_quadrants : bool
            An optional setting to divide the pincell into 4 separate MPACT
            Module quadrants. This will represent the pincell with 4 MPACT
            Modules rather than just one. Default value is False.
        material_specs : Optional[MaterialSpecs]
            Specifications for how materials should be treated in MPACT.

        Attributes
        ----------
        zone_specs : Optional[ZoneSpecs | List[ZoneSpecs]]
            Mesh specifications for the pin cell. A single ``ZoneSpecs``
            applies to all cylindrical zones and the outer region. A list
            specifies regions individually and must have one entry for each
            cylindrical zone plus one final entry for the outer region.
        divide_into_quadrants : bool
            An optional setting to divide the pincell into 4 separate MPACT Module quadrants.
            This will represent the pincell with 4 MPACT Modules rather than just one.
            Default value is False
        material_specs : MaterialSpecs
            Specifications for how materials should be treated in MPACT
        """

        zone_specs:            Optional[CylindricalPinCell.ZoneSpecs | List[CylindricalPinCell.ZoneSpecs]]
        divide_into_quadrants: bool
        material_specs:        MaterialSpecs

        def __init__(self,
                     zone_specs:            Optional[CylindricalPinCell.ZoneSpecs |
                                            List[CylindricalPinCell.ZoneSpecs]] = None,
                     divide_into_quadrants: bool = False,
                     material_specs:        Optional[MaterialSpecs] = None,
        ) -> None:
            zone_specs = zone_specs if zone_specs is not None else CylindricalPinCell.ZoneSpecs()

            self.zone_specs            = zone_specs
            self.divide_into_quadrants = divide_into_quadrants
            self.material_specs        = material_specs if material_specs is not None else {}


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


    def build(self, element: geometry_elements.CylindricalPinCell, bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a CylindricalPinCell

        Parameters
        ----------
        element: geometry_elements.CylindricalPinCell
            The geometry element to be built
        bounds: Optional[Bounds]
            The spatial bounds for the geometry.
            X and Y define the radial bounds, Z defines the height.
            Defaults to outer radius and height of 1.0 if not provided.

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        specs = self.specs

        outer_radius   = element.zones[-1].shape.outer_radius
        bounds   = bounds or Bounds()
        bounds.X = bounds.X or AxisBounds(min=-outer_radius, max=outer_radius)
        bounds.Y = bounds.Y or AxisBounds(min=-outer_radius, max=outer_radius)
        bounds.Z = bounds.Z or AxisBounds(min=0.0,           max=1.0)

        def build_module(module_bounds: Tuple[float, float, float, float]) -> mpactpy.Module:
            radii, ndivr, ndiva, materials = self._build_pin_parameters(element, module_bounds)
            z_thickness = bounds.Z.max - bounds.Z.min if bounds.Z else 1.0
            pinmesh = mpactpy.GeneralCylindricalPinMesh(radii,
                                                        module_bounds[0],
                                                        module_bounds[1],
                                                        module_bounds[2],
                                                        module_bounds[3],
                                                        [z_thickness],
                                                        ndivr,
                                                        ndiva,
                                                        [1])
            pin = mpactpy.Pin(pinmesh, materials)
            return mpactpy.Module(1, [[pin]])

        (xmin, xmax, ymin, ymax) = (bounds.X.min, bounds.X.max, bounds.Y.min, bounds.Y.max)
        hp   = {"X": (xmax-xmin)*0.5, "Y": (ymax-ymin)*0.5} # half pitch

        module_map = [[build_module((xmin, xmax, ymin, ymax))]] if not specs.divide_into_quadrants else \
                     [[build_module((        xmin, xmin+hp["X"], ymin+hp["Y"],         ymax)),
                       build_module((xmin+hp["X"],         xmax, ymin+hp["Y"],         ymax))],
                      [build_module((        xmin, xmin+hp["X"],         ymin, ymin+hp["Y"])),
                       build_module((xmin+hp["X"],         xmax,         ymin, ymin+hp["Y"]))],]

        lattice  = mpactpy.Lattice(module_map)
        assembly = mpactpy.Assembly([lattice])
        core     = mpactpy.Core([[assembly]])

        return core


    def _build_pin_parameters(self,
                              element:       geometry_elements.CylindricalPinCell,
                              module_bounds: Tuple[float, float, float, float],
    ) -> Tuple[List[float], List[int], List[int], List[mpactpy.Material]]:
        """Build radial mesh and material parameters for an MPACT pin.

        Parameters
        ----------
        element : geometry_elements.CylindricalPinCell
            Cylindrical pin-cell geometry to translate into MPACT pin inputs.
        module_bounds : Tuple[float, float, float, float]
            Radial module bounds in ``(x_min, x_max, y_min, y_max)`` order.

        Returns
        -------
        Tuple[List[float], List[int], List[int], List[mpactpy.Material]]
            ``radii``, ``ndivr``, ``ndiva``, and ``materials`` for constructing
            a ``GeneralCylindricalPinMesh`` and corresponding ``Pin``.
        """
        specs          = self.specs
        outer_radius   = element.zones[-1].shape.outer_radius
        zone_radii     = [0.0] + [zone.shape.outer_radius for zone in element.zones]
        zone_materials = [build_material(zone.material, specs.material_specs) for zone in element.zones]
        outer_material = build_material(element.outer_material, specs.material_specs)

        zone_specs = specs.zone_specs if specs.zone_specs is not None else CylindricalPinCell.ZoneSpecs()
        if isinstance(zone_specs, CylindricalPinCell.ZoneSpecs):
            zone_specs = [zone_specs] * (len(element.zones) + 1)

        assert len(zone_specs) == len(element.zones) + 1, \
            f"len(zone_specs) = {len(zone_specs)}, len(element.zones) + 1 = {len(element.zones) + 1}"

        def material_subdivision_radii(inner_radius: float, outer_radius: float,
                                       zone_spec: CylindricalPinCell.ZoneSpecs) -> list[float]:
            if zone_spec.ndivr_mat_type == "equal_thickness":
                thickness = outer_radius - inner_radius
                return [inner_radius + thickness * i / zone_spec.ndivr_mat
                        for i in range(1, zone_spec.ndivr_mat + 1)]
            return equal_volume_ring_radii(outer_radius, zone_spec.ndivr_mat, inner_radius)

        xmin, xmax, ymin, ymax         = module_bounds
        bounding_radius                = max(hypot(x, y) for x in (xmin, xmax) for y in (ymin, ymax))
        radii, ndivr, ndiva, materials = [], [], [], []

        def append_material_region(radius:   float,
                                   spec:     CylindricalPinCell.ZoneSpecs,
                                   material: mpactpy.Material) -> None:
            radii.append(radius)
            ndivr.append(spec.ndivr_fsr)
            ndiva.extend([spec.ndiva] * spec.ndivr_fsr)
            materials.append(material)

        for r1, r2, spec, material in zip(
            zone_radii[:-1], zone_radii[1:], zone_specs[:-1], zone_materials):

            subdivision_radii = material_subdivision_radii(r1, r2, spec)
            for radius in subdivision_radii:
                append_material_region(radius, spec, material)

        outer_spec = zone_specs[-1]
        if bounding_radius > outer_radius:
            subdivision_radii = material_subdivision_radii(zone_radii[-1], bounding_radius, outer_spec)
            for radius in subdivision_radii[:-1]:
                append_material_region(radius, outer_spec, outer_material)

        materials.append(outer_material)
        ndiva.append(outer_spec.ndiva)

        return radii, ndivr, ndiva, materials

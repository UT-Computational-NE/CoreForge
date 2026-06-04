from __future__ import annotations
from typing import Optional, List
from dataclasses import dataclass

import mpactpy
from mpactpy.utils import RadialDivisionType

from coreforge.mpact_builder.builder import AxisBounds, Bounds, Builder, build_material
from coreforge.mpact_builder.builder_specs import BuilderSpecs, MaterialSpecs
from coreforge.mpact_builder.mpact_builder import register_builder
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
        ndivr_mat_type: RadialDivisionType = "equal_thickness"

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

        def build_module(pin: mpactpy.Pin) -> mpactpy.Module:
            return mpactpy.Module(1, [[pin]])

        zone_specs = specs.zone_specs if specs.zone_specs is not None else CylindricalPinCell.ZoneSpecs()
        if isinstance(zone_specs, CylindricalPinCell.ZoneSpecs):
            zone_specs = [zone_specs] * (len(element.zones) + 1)

        assert len(zone_specs) == len(element.zones) + 1, \
            f"len(zone_specs) = {len(zone_specs)}, len(element.zones) + 1 = {len(element.zones) + 1}"

        radii = [zone.shape.outer_radius for zone in element.zones]
        materials = [build_material(zone.material, specs.material_specs) for zone in element.zones]
        materials.append(build_material(element.outer_material, specs.material_specs))

        ndivr = [zone_spec.ndivr_fsr for zone_spec in zone_specs[:-1]]
        ndiva = [zone_spec.ndiva for zone_spec in zone_specs[:-1] for _ in range(zone_spec.ndivr_fsr)]
        ndiva.append(zone_specs[-1].ndiva)

        z_thickness = bounds.Z.max - bounds.Z.min if bounds.Z else 1.0
        pinmesh = mpactpy.GeneralCylindricalPinMesh(radii,
                                                    bounds.X.min,
                                                    bounds.X.max,
                                                    bounds.Y.min,
                                                    bounds.Y.max,
                                                    [z_thickness],
                                                    ndivr,
                                                    ndiva,
                                                    [1])
        pin = mpactpy.Pin(pinmesh, materials)

        subdivisions = mpactpy.GeneralCylindricalPinMesh.Subdivisions(
            subd_r      = [zone_spec.ndivr_mat for zone_spec in zone_specs],
            div_type    = [zone_spec.ndivr_mat_type for zone_spec in zone_specs],
            outer_ndivr = zone_specs[-1].ndivr_fsr,
        )
        pin = pin.subdivide(subdivisions)

        module_map = [[build_module(pin)]] if not specs.divide_into_quadrants else \
                     [[build_module(quadrant_pin) for quadrant_pin in row]
                      for row in pin.divide_into_quadrants()]

        lattice  = mpactpy.Lattice(module_map)
        assembly = mpactpy.Assembly([lattice])
        core     = mpactpy.Core([[assembly]])

        return core

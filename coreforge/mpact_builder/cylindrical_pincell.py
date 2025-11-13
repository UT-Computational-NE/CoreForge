from typing import TypedDict, Tuple, Optional
from dataclasses import dataclass
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build_material, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.material_specs import MaterialSpecs
from coreforge import geometry_elements

@register_builder(geometry_elements.CylindricalPinCell)
class CylindricalPinCell:
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
    class Specs(BuilderSpecs):
        """ Building specifications for CylindricalPinCells

        Attributes
        ----------
        target_cell_thicknesses : Thicknesses
            The target thickness of the cells in terms of 'radial' thickness
            and 'azimuthal' arc length (cm).
            Cells will be subdivided to limit cells to within these specifications.
        divide_into_quadrants : bool
            An optional setting to divide the pincell into 4 separate MPACT Module quadrants.
            This will represent the pincell with 4 MPACT Modules rather than just one.
            Default value is False
        material_specs : MaterialSpecs
            Specifications for how materials should be treated in MPACT
        """

        class Thicknesses(TypedDict):
            """ Class specifying the keys for target cell thickness
            """
            radial:    float
            azimuthal: float

        target_cell_thicknesses: Optional[Thicknesses] = None
        divide_into_quadrants:   bool = False
        material_specs:          Optional[MaterialSpecs] = None

        def __post_init__(self):
            if not self.target_cell_thicknesses:
                self.target_cell_thicknesses = {}

                for dim in ["radial", "azimuthal"]:
                    self.target_cell_thicknesses.setdefault(dim, inf)

            if not self.material_specs:
                self.material_specs = MaterialSpecs()

            assert all(thickness > 0. for thickness in self.target_cell_thicknesses.values()), \
                f"target_cell_thicknesses = {self.target_cell_thicknesses}"


    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs if specs else CylindricalPinCell.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


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

        outer_radius = element.zones[-1].shape.outer_radius
        materials    = [zone.material for zone in element.zones] + [element.outer_material]
        materials    = [build_material(material) for material in materials]

        target_cell_thicknesses = {"R": specs.target_cell_thicknesses["radial"],
                                   "S": specs.target_cell_thicknesses["azimuthal"]}

        radii = [zone.shape.inner_radius for zone in element.zones]
        radial_thicknesses = [curr - prev for prev, curr in zip([0.0] + radii[:-1], radii)]


        bounds = bounds or Bounds(X = {"min": -outer_radius, "max": outer_radius},
                                  Y = {"min": -outer_radius, "max": outer_radius},
                                  Z = {"min": 0.0, "max": 1.0})

        def build_module(module_bounds: Tuple[float, float, float, float]) -> mpactpy.Module:
            z_thickness = bounds.Z['max'] - bounds.Z['min'] if bounds.Z else 1.0
            pin = mpactpy.build_gcyl_pin(bounds                  = module_bounds,
                                         materials               = materials,
                                         target_cell_thicknesses = target_cell_thicknesses,
                                         thicknesses             = {"R": radial_thicknesses,
                                                                    "Z": [z_thickness]})
            return mpactpy.Module(1, [[pin]])

        (xmin, xmax, ymin, ymax) = (bounds.X['min'], bounds.X['max'], bounds.Y['min'], bounds.Y['max'])
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

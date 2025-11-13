from typing import TypedDict, Optional, Dict
from dataclasses import dataclass
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build_material, Bounds
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.material_specs import MaterialSpecs
from coreforge import geometry_elements

@register_builder(geometry_elements.InfiniteMedium)
class InfiniteMedium:
    """ An MPACT geometry builder class for InfiniteMedium

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
        """ Building specifications for InfiniteMedium

        Attributes
        ----------
        target_cell_thicknesses : Thicknesses
            The target side length of the cells (cm).  Defaults to infinity for dimensions
            where no targets provided. (keys: "X", "Y", "Z")
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
            X: float
            Y: float
            Z: float

        target_cell_thicknesses: Optional[Thicknesses] = None
        divide_into_quadrants:   bool = False
        material_specs:          Optional[MaterialSpecs] = None

        def __post_init__(self):
            if self.target_cell_thicknesses is None:
                self.target_cell_thicknesses = {}

            for dim in ["X", "Y", "Z"]:
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
        self._specs = specs if specs else InfiniteMedium.Specs()


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


    def build(self, element: geometry_elements.InfiniteMedium, bounds: Optional[Bounds] = None) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a InfiniteMedium

        Parameters
        ----------
        element: geometry_elements.InfiniteMedium
            The geometry element to be built
        bounds: Optional[Bounds]
            The spatial bounds for the geometry (Bounds dataclass with X, Y, Z AxisBounds).
            Defaults to 1.0 thickness in each dimension if not provided.

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        specs = self.specs
        materials = [build_material(element.material)]

        thicknesses = {"X": 1.0, "Y": 1.0, "Z": 1.0}
        if bounds:
            thicknesses["X"] = bounds.X['max'] - bounds.X['min'] if bounds.X else thicknesses["X"]
            thicknesses["Y"] = bounds.Y['max'] - bounds.Y['min'] if bounds.Y else thicknesses["Y"]
            thicknesses["Z"] = bounds.Z['max'] - bounds.Z['min'] if bounds.Z else thicknesses["Z"]

        def build_module(module_thicknesses: Dict[str, float]) -> mpactpy.Module:
            pin = mpactpy.build_rec_pin(thicknesses             = {"X": [module_thicknesses["X"]],
                                                                   "Y": [module_thicknesses["Y"]],
                                                                   "Z": [module_thicknesses["Z"]]},
                                        materials               = materials,
                                        target_cell_thicknesses = specs.target_cell_thicknesses)
            return mpactpy.Module(1, [[pin]])

        # half radial thicknesses
        ht   = {"X": thicknesses["X"]*0.5,
                "Y": thicknesses["Y"]*0.5,
                "Z": thicknesses["Z"]}

        module_map = [[build_module(thicknesses)]] if not specs.divide_into_quadrants else \
                     [[build_module(ht),build_module(ht)],
                      [build_module(ht),build_module(ht)],]

        lattice  = mpactpy.Lattice(module_map)
        assembly = mpactpy.Assembly([lattice])
        core     = mpactpy.Core([[assembly]])

        return core

from typing import TypedDict, Optional
from dataclasses import dataclass
from math import inf

import mpactpy

from coreforge.mpact_builder.mpact_builder import register_builder, build_material
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
        thicknesses : Thicknesses
            The thicknesses of each material region division in each axis-direction
            (keys: "X", "Y", "Z")
        height : float
            The height to build the extruded PinCell in the axial direction (cm).
            Default value is 1.0
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

        thicknesses:             Thicknesses
        target_cell_thicknesses: Optional[Thicknesses] = None
        height:                  float = 1.0
        divide_into_quadrants:   bool = False
        material_specs:          Optional[MaterialSpecs] = None

        def __post_init__(self):
            if not self.target_cell_thicknesses:
                self.target_cell_thicknesses = {"X": inf, "Y": inf, "Z": inf}

            if not self.material_specs:
                self.material_specs = MaterialSpecs()

            assert all(thickness > 0. for thickness in self.target_cell_thicknesses.values()), \
                f"target_cell_thicknesses = {self.target_cell_thicknesses}"

            assert self.height > 0., f"height = {self.height}"

            assert all(thickness > 0. for thickness in self.thicknesses.values()), \
                f"target_cell_thicknesses = {self.thicknesses}"


    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Specs) -> None:
        self._specs = specs


    def __init__(self, specs: Specs):
        self.specs = specs


    def build(self, element: geometry_elements.InfiniteMedium) -> mpactpy.Core:
        """ Method for building an MPACT geometry of a InfiniteMedium

        Parameters
        ----------
        element: geometry_elements.InfiniteMedium
            The geometry element to be built

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        specs = self.specs

        materials = [build_material(element.material)]

        def build_module(thicknesses: InfiniteMedium.Specs.Thicknesses) -> mpactpy.Module:
            pin = mpactpy.build_rec_pin(thicknesses             = {"X": [thicknesses["X"]],
                                                                   "Y": [thicknesses["Y"]],
                                                                   "Z": [specs.height]},
                                        materials               = materials,
                                        target_cell_thicknesses = specs.target_cell_thicknesses)
            return mpactpy.Module(1, [[pin]])

        ht   = {"X": specs.thicknesses["X"]*0.5,
                "Y": specs.thicknesses["Y"]*0.5} # half thicknesses

        module_map = [[build_module(specs.thicknesses)]] if not specs.divide_into_quadrants else \
                     [[build_module(ht),build_module(ht)],
                      [build_module(ht),build_module(ht)],]

        lattice  = mpactpy.Lattice(module_map)
        assembly = mpactpy.Assembly([lattice])
        core     = mpactpy.Core([[assembly]])

        return core

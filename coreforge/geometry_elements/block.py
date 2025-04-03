from __future__ import annotations
from typing import List, Any, Optional
from math import isclose

import openmc
from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes import Shape_2D
from coreforge.materials import Material
from coreforge.geometry_elements.geometry_element import GeometryElement

class Block(GeometryElement):
    """ A class for the reactor blocks

    Reactor blocks are generally a prism with any number and arrangement
    of flow channels aligned along the prism's extrusion axis.

    Parameters
    ----------
    shape : Shape_2D
        The shape of the block
    prism_material : Material
        The material of the prismatic block
    name : str
        The name of the Block
    channels : List[Optional[Channel]]
        The fluid flow channels of this block
    outer_material : Material
        The material that radially surrounds the prism

    Attributes
    ----------
    shape : Shape_2D
        The shape of the block
    prism_material : Material
        The material of the prismatic block
    channels : List[Optional[Channel]]
        The fluid flow channels of this block
    outer_material : Material
        The material that radially surrounds the prism
    """

    class Channel():
        """ A class for a block channel

        Parameters
        ----------
        name : str
            The name for the channel
        shape : Shape_2D
            The shape of the channel
        shape_rotation : float
            The rotation of the channel about its own center (degrees)
        distance_from_block_center : float
            The distance between the block center and channel center.
            This translates the shape in negative-Y direction.
        rotation_about_block_center : float
            The rotation of the channel about the block center.
            The rotation is applied after the distance_from_block_center translation
        material : Material
            The material flowing through the channel

        Attributes
        ----------
        name : str
            The name for the channel
        shape : Shape_2D
            The shape of the channel
        shape_rotation : float
            The rotation of the channel about its own center (degrees)
        distance_from_block_center : float
            The distance between the block center and channel center.
        rotation_about_block_center : float
            The rotation of the channel about the block center.
        material : Material
            The material flowing through the channel
        """

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        def name(self, name: str) -> str:
            self._name = name

        @property
        def shape(self) -> Shape_2D:
            return self._shape

        @shape.setter
        def shape(self, shape: Shape_2D) -> None:
            self._shape = shape

        @property
        def shape_rotation(self) -> float:
            return self._shape_rotation

        @shape_rotation.setter
        def shape_rotation(self, shape_rotation: float) -> None:
            self._shape_rotation = shape_rotation

        @property
        def distance_from_block_center(self) -> float:
            return self._distance_from_block_center

        @distance_from_block_center.setter
        def distance_from_block_center(self, distance_from_block_center: float) -> None:
            assert distance_from_block_center >= 0., \
                f"distance_from_block_center = {distance_from_block_center}"
            self._distance_from_block_center = distance_from_block_center

        @property
        def rotation_about_block_center(self) -> float:
            return self._rotation_about_block_center

        @rotation_about_block_center.setter
        def rotation_about_block_center(self, rotation_about_block_center: float) -> None:
            self._rotation_about_block_center = rotation_about_block_center

        @property
        def material(self) -> Material:
            return self._material

        @material.setter
        def material(self, material: Material) -> None:
            self._material = material

        def __init__(self,
                     shape:                       Shape_2D,
                     material:                    Material,
                     name:                        str = 'channel',
                     shape_rotation:              float = 0.,
                     distance_from_block_center:  float = 0.,
                     rotation_about_block_center: float = 0.):
            self.name                        = name
            self.shape                       = shape
            self.material                    = material
            self.shape_rotation              = shape_rotation
            self.distance_from_block_center  = distance_from_block_center
            self.rotation_about_block_center = rotation_about_block_center

        def __eq__(self, other: Any) -> bool:
            if self is other:
                return True
            return (isinstance(other, Block.Channel)                                                        and
                    self.shape == other.shape                                                               and
                    self.material == other.material                                                         and
                    isclose(self.shape_rotation, other.shape_rotation, rel_tol=TOL)                         and
                    isclose(self.distance_from_block_center, other.distance_from_block_center, rel_tol=TOL) and
                    isclose(self.rotation_about_block_center, other.rotation_about_block_center, rel_tol=TOL)
                   )

        def __hash__(self) -> int:
            return hash((self.shape,
                         self.material,
                         relative_round(self.shape_rotation, TOL),
                         relative_round(self.distance_from_block_center, TOL),
                         relative_round(self.rotation_about_block_center, TOL)))

        def make_cell(self) -> openmc.Cell:
            """ A method for creating a new cell based on the channel

            Returns
            -------
            openmc.Cell
                A new cell based on this channel
            """

            region = self.shape.make_region()
            region = region.rotate((0., 0., self.shape_rotation))
            region = region.translate([0., -self.distance_from_block_center, 0.])
            region = region.rotate((0., 0., self.rotation_about_block_center))
            cell = openmc.Cell(name=self.name, fill=self.material.openmc_material, region=region)
            return cell

    @property
    def shape(self) -> Shape_2D:
        return self._shape

    @shape.setter
    def shape(self, shape: Shape_2D) -> None:
        self._shape = shape

    @property
    def prism_material(self) -> Material:
        return self._prism_material

    @prism_material.setter
    def prism_material(self, prism_material: Material) -> None:
        self._prism_material = prism_material

    @property
    def channels(self) -> List[Optional[Channel]]:
        return self._channels

    @channels.setter
    def channels(self, channels: List[Optional[Channel]]) -> None:
        self._channels = channels

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @outer_material.setter
    def outer_material(self, outer_material: Material) -> None:
        self._outer_material = outer_material


    def __init__(self,
                 shape:          Shape_2D,
                 prism_material: Material,
                 name:           str = 'block',
                 channels:       List[Optional[Channel]] = None,
                 outer_material: Material = None):

        self.shape            = shape
        self.prism_material   = prism_material
        self.channels         = channels if channels else []
        self.outer_material   = outer_material if not(outer_material is None) else prism_material
        super().__init__(name)

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Block)                    and
                self.shape == other.shape                   and
                self.prism_material == other.prism_material and
                self.outer_material == other.outer_material and
                len(self.channels) == len(other.channels)   and
                all(self.channels[i] == other.channels[i] for i in range(len(self.channels)))
               )

    def __hash__(self) -> int:
        return hash((self.shape,
                     self.prism_material,
                     self.outer_material,
                     tuple(self.channels)))

    def make_openmc_universe(self) -> openmc.Universe:

        channel_cells = []
        for channel in self.channels:
            if channel is None:
                continue
            channel_cells.append(channel.make_cell())

        prism_region = self.shape.make_region()
        outer_region = ~prism_region
        for channel in channel_cells:
            prism_region &= ~channel.region
            outer_region &= ~channel.region

        block_cell = openmc.Cell(fill=self.prism_material.openmc_material, region=prism_region)
        outer_cell = openmc.Cell(fill=self.outer_material.openmc_material, region=outer_region)

        universe = openmc.Universe(name=self.name)
        universe.add_cells([block_cell, outer_cell])
        for channel in channel_cells:
            universe.add_cell(channel)

        return universe

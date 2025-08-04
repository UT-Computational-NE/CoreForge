from __future__ import annotations
from typing import List, Optional, Dict
from copy import deepcopy

from coreforge.shapes import Shape_2D, Circle, Rectangle, Square, Stadium
from coreforge.materials import Material
from coreforge.geometry_elements.block import Block as BaseBlock



class Block(BaseBlock):
    """ A class for MSRE-like blocks

    MSRE-like blocks are square blocks with channels that are either centered on
    the middle of the block's N-S-E-W edges or the center of adjacent N-S-E-W block cell.

    When specifying the block channels, users must provide a list of channels with the list
    being 4 entries long corresponding to each face of the block.  For those faces with
    channels, the channel must be either a FuelChannel or ControlChannel.  Those faces
    with no flow channels should be specified as None.  The ordering of the channel list by
    face is N-S-E-W.

    Parameters
    ----------
    pitch : float
        Pitch of the block (cm)
    prism_material : Material
        The material of the prismatic block
    name : str
        The name of the MSRE Block
    channels : Dict[Optional[Block.Channel]]
        The channels of this MSRE Block (keys: "N", "S", "E", "W")
    outer_material : Optional[Material]
        The material that radially surrounds the prism
        Default: prism_material

    Attributes
    ----------
    pitch : float
        Pitch of the block (cm)
    fuel_channels : List[Block.FuelChannel]
        The fuel channels of this block
    has_fuel_channels : bool
        Whether or not the block has any fuel channels
    fuel_channels_have_equal_shapes : bool
        Whether or not the present fuel channels have the same shape (NOTE: false if no fuel channels are present)
    control_channels : List[Block.ControlChannel]
        The control channels of this block
    has_control_channels : bool
        Whether or not the block has any control channels
    control_channels_have_equal_shapes : bool
        Whether or not the present control channels have the same shape(NOTE: false if no control channels are present)
    """

    class Channel(BaseBlock.Channel):
        """ An abstract class for MSRE Block Channels
        """

        # Not sure why, by Pylint keeps thinking this __init__ isn't being used
        # even though it is.
        # pylint: disable=super-init-not-called
        def __init__(self, name: str, shape: Shape_2D, material: Material):
            self.name                         = name
            self.shape                        = shape
            self.material                     = material
            self._shape_rotation              = 0.
            self._distance_from_block_center  = None
            self._rotation_about_block_center = None


    class FuelChannel(Channel):
        """  A class for MSRE-like Block Fuel Flow Channels

        These channels are centered on the middle of the block's N-S-E-W edges.
        Currently, only stadium, circular, and rectangular fuel channels are supported.
        Rectangular fuel channels must also have a width greater than or equal to their height

        Parameters
        ----------
        shape : Optional[Shape_2D]
            The shape of the channel.  This must be either a Stadium, Circle, or Rectangle.
        material : Optional[Material]
            The material that fills the channel
        """

        @property
        def shape(self) -> Shape_2D:
            return self._shape

        @shape.setter
        def shape(self, shape: Shape_2D) -> None:
            assert isinstance(shape, (Stadium, Circle, Rectangle)), \
                    f"{type(self).__name__} is an Invalid Fuel Channel Shape! " +\
                        "Fuel Channel must be a Stadium, Circle, or Rectangle."
            if isinstance(shape, Rectangle):
                assert shape.w >= shape.h, f"width = {shape.w}, height = {shape.h}"
            self._shape = shape

        def __init__(self,
                     shape:             Shape_2D,
                     material:          Material,
                     name:              str = "fuel_channel",):

            super().__init__(name, shape, material)


    class ControlChannel(Channel):
        """ A class for MSRE-like Block Control Channels

        These channels are centered on the centers of the neighboring adjacent block cells.
        Currently, only cricular control channels are supported.

        Parameters
        ----------
        shape : Shape_2D
            The shape of the channel.  This must be a Circle.
        material : Material
            The material that fills the channel
        """

        @property
        def shape(self) -> Shape_2D:
            return self._shape

        @shape.setter
        def shape(self, shape: Shape_2D) -> None:
            assert isinstance(shape, Circle), \
                f"{type(self).__name__} is and Invalid Control Channel Shape! " +\
                        "Control Channel shape must be a Circle."
            self._shape = shape

        def __init__(self,
                     shape:             Shape_2D,
                     material:          Material,
                     name:              str = "control_channel",):
            super().__init__(name, shape, material)


    @property
    def pitch(self) -> float:
        return self._pitch

    @pitch.setter
    def pitch(self, pitch: float) -> None:
        assert pitch > 0., f"pitch = {pitch}"
        self._pitch = pitch

    @property
    def fuel_channels(self) -> List[Block.FuelChannel]:
        return [channel for channel in self.channels if isinstance(channel, Block.FuelChannel)]

    @property
    def has_fuel_channels(self) -> bool:
        return len(self.fuel_channels) > 0

    @property
    def fuel_channels_have_equal_shapes(self) -> bool:
        return self.has_fuel_channels and \
               all(channel.shape == self.fuel_channels[0].shape for channel in self.fuel_channels)

    @property
    def control_channels(self) -> List[Block.ControlChannel]:
        return [channel for channel in self.channels if isinstance(channel, Block.ControlChannel)]

    @property
    def has_control_channels(self) -> bool:
        return len(self.control_channels) > 0

    @property
    def control_channels_have_equal_shapes(self) -> bool:
        if not self.has_control_channels:
            return False
        return all(channel.shape == self.control_channels[0].shape for channel in self.control_channels)


    @property
    def channels(self) -> List[Optional[Block.Channel]]:
        return self._channels

    @channels.setter
    def channels(self, channels: List[Optional[Block.Channel]]) -> None:
        assert len(channels) == 4, f"len(channels) = {len(channels)}"
        rotation = [180., 0., 90., 270.]
        self._channels = [None, None, None, None]
        for i, channel in enumerate(channels):
            if channel:
                self.channels[i] = deepcopy(channel)
                self.channels[i].rotation_about_block_center = rotation[i]
                if isinstance(channel, Block.FuelChannel):
                    self.channels[i].distance_from_block_center = self.pitch*0.5
                else:
                    assert self.channels[i].shape.outer_radius > self.pitch*0.5, \
                        "Control channel falls outside the block. Channel Radius = " + \
                        f"{self.channels[i].shape.outer_radius}, Block Half Pitch = " + \
                        f"{self.pitch*0.5}"
                    self.channels[i].distance_from_block_center = self.pitch


    def __init__(self,
                 channels:          Dict[Optional[Block.Channel]],
                 pitch:             float,
                 prism_material:    Material,
                 name:              str = "msre_block",
                 outer_material:    Optional[Material] = None):

        self.pitch = pitch
        channels = [channels[face] if face in channels else None for face in ['N', 'S', 'E', 'W']]

        super().__init__(Square(length=pitch), prism_material, name, channels, outer_material)

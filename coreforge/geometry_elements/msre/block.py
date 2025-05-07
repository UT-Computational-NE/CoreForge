from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from typing import List, TypedDict, Optional, Dict, Literal
from math import inf, sqrt
from copy import deepcopy

import mpactpy
from mpactpy.pin import build_rec_pin, build_gcyl_pin

from coreforge.shapes import Shape_2D, Circle, Rectangle, Square, Stadium
from coreforge.materials import Material
from coreforge.geometry_elements.block import Block as BaseBlock
from coreforge.utils import remove_none_2D

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
    channels : List[Optional[Block.Channel]]
        The channels of this MSRE Block (keys: "N", "S", "E", "W")
    outer_material : Material
        The material that radially surrounds the prism
    mpact_build_specs : Optional[MPACTBuildSpecs]
        Specifications for building the MPACT Core representation of this element

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
    mpact_build_specs : MPACTBuildSpecs
        Specifications for building the MPACT Core representation of this element

    References
    ----------
    1. Robertson, R. C., “MSRE Design and Operations Report Part I: Description of Reactor Design”,
       ORNL-TM-0728, Oak Ridge National Laboratory, Oak Ridge, Tennessee (1965).
    """

    @dataclass
    class MPACTBuildSpecs():
        """ A dataclass for holding MPACT Core building specifications

        Attributes
        ----------
        target_cell_thicknesses : ThicknessSpec
            The target thickness of the cells in terms of lateral 'cartesian' length,
            'radial' thickness, and 'azimuthal' arc length (cm).
            Cells will be subdivided to limit cells to within these specifications.
        height : float
            The height to build the extruded PinCell in the axial direction (cm).
            Default value is 1.0
        divide_into_quadrants : bool
            An optional setting to divide the pincell into 4 separate MPACT Module quadrants.
            This will represent the pincell with 4 MPACT Modules rather than just one.
            Default value is False
        """

        class ThicknessSpec(TypedDict):
            """ Class specifying the keys for target cell thickness
            """
            cartesian: float
            radial:    float
            azimuthal: float

        target_cell_thicknesses: Optional[ThicknessSpec] = None
        height:                  float = 1.0
        divide_into_quadrants:   bool = False

        def __post_init__(self):
            if not self.target_cell_thicknesses:
                self.target_cell_thicknesses = {'cartesian': inf, 'radial': inf, 'azimuthal': inf}

            assert all(thickness > 0. for thickness in self.target_cell_thicknesses.values()), \
                f"target_cell_thicknesses = {self.target_cell_thicknesses}"

            assert self.height > 0., f"height = {self.height}"


    class Channel(BaseBlock.Channel):
        """ An abstract class for MSRE Block Channels

        Attributes
        ----------
        mpact_build_specs : Optional[MPACTBuildSpecs]
            Specifications for building the MPACT Pin for this channel
        """

        Orientation = Literal["horizontal", "vertical"]
        PinType     = Literal["cap", "flat"]
        Quadrant    = Literal["NW", "NE", "SW", "SE"]

        @dataclass
        class MPACTBuildSpecs():
            """ A dataclass for holding MPACT Pin building specifications

            When constructing MPACT Pins for channels, geometric specifications are
            expressed in terms of Stadium features such as 'flats' and 'caps' given that
            Stadium channels are the primary application. Circular and Rectangular fuel
            channels are treated as varients of Stadium channels, wherein Rectangle channels
            are simply Stadiums with square caps, and Circle channels are Stadiums with no flats.

            The 'flats' and 'caps' terminology is also used with Control Channels given that
            the limitations of the MPACT geometry construction requires Control Channels to
            adhere to certain geometric constraints based on the 'flats' and 'caps' of the fuel channels.

            Attributes
            ----------
            target_cell_thicknesses : Block.ThicknessSpec
                The target thickness of the cells in terms of lateral 'cartesian' length,
                'radial' thickness, and 'azimuthal' arc length (cm).
                Cells will be subdivided to limit cells to within these specifications.
            height : float
                The height to build the extruded Pin in the axial direction (cm).
                Default value is 1.0
            block_pitch : float
                The block pitch (cm) to use for MPACT Pin construction
            cap_cell_length : float
                The cap cell length (cm) to use for MPACT Pin construction
            flat_length : float
                The flat length (cm) to use for MPACT Pin construction
            prism_material : mpactpy.Material
                The MPACT material of the prismatic block
            """

            block_pitch:             float
            cap_cell_length:         float
            flat_length:        float
            prism_material:          mpactpy.Material
            target_cell_thicknesses: Optional[Block.ThicknessSpec] = None
            height:                  float = 1.0


            def __post_init__(self):
                if not self.target_cell_thicknesses:
                    self.target_cell_thicknesses = {'cartesian': inf, 'radial': inf, 'azimuthal': inf}

                assert all(thickness > 0. for thickness in self.target_cell_thicknesses.values()), \
                    f"target_cell_thicknesses = {self.target_cell_thicknesses}"

                assert self.height > 0.,          f"height = {self.height}"
                assert self.block_pitch > 0.,     f"block_pitch = {self.block_pitch}"
                assert self.cap_cell_length > 0., f"cap_cell_length = {self.cap_cell_length}"
                assert self.flat_length >= 0.,    f"flat_length = {self.flat_length}"

        @property
        def mpact_build_specs(self) -> Block.Channel.MPACTBuildSpecs:
            return self._mpact_build_specs

        @mpact_build_specs.setter
        def mpact_build_specs(self, specs: Block.Channel.MPACTBuildSpecs) -> None:
            self._mpact_build_specs = specs
            self._channel_material  = self.material.mpact_material
            self._prism_material    = specs.prism_material
            self._has_flats         = specs.flat_length > 0.0

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
            self._mpact_build_specs           = None


        @abstractmethod
        def build_mpact_pin(self, orientation: Orientation, pin_type: PinType, quadrant: Quadrant) -> mpactpy.Pin:
            """ Helper method for building MPACT Pins for the Channel

            Parameters
            ----------
            orientation : Orientation
                The channel orientation to use when building the pin
            pin_type : PinType
                The part of the channel to be constructed (i.e. 'cap' or 'flat')
            quadrant : Quadrant
                Which quadrant of the channel to consider when constructing the pin

            Returns
            -------
            mpactpy.Pin
                The constructed channel pin
            """


    class FuelChannel(Channel):
        """  A class for MSRE-like Block Fuel Flow Channels

        These channels are centered on the middle of the block's N-S-E-W edges.
        Currently, only stadium, circular, and rectangular fuel channels are supported.
        Rectangular fuel channels must also have a width greater than or equal to their height

        Parameters
        ----------
        shape : Shape_2D
            The shape of the channel.  This must be either a Stadium, Circle, or Rectangle.
        mpact_build_specs : Block.Channel.MPACTBuildSpecs
            The specifications required to build an MPACT Pin.  Cap cell length must be greater
            than or equal to the channel thickness.

        Attributes
        ----------
        shape : Shape_2D
            The shape of the channel
        mpact_build_specs : Block.Channel.MPACTBuildSpecs
            The specifications required to build an MPACT Pin
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

        @property
        def mpact_build_specs(self) -> Block.Channel.MPACTBuildSpecs:
            return self._mpact_build_specs

        @mpact_build_specs.setter
        def mpact_build_specs(self, specs: Block.Channel.MPACTBuildSpecs) -> None:
            Block.Channel.mpact_build_specs.__set__(self, specs)

            self._channel_thickness = self.shape.inner_radius
            self._prism_thickness   = specs.cap_cell_length - self._channel_thickness

            assert self._channel_thickness <= specs.cap_cell_length, \
                f"fuel_channel_thickness = {self._channel_thickness}, " + \
                f"cap_cell_length = {specs.cap_cell_length}"

            ccl = specs.cap_cell_length
            hfl = specs.flat_length * 0.5
            pm  = self._prism_material
            cm  = self._channel_material
            pt  = self._prism_thickness
            ct  = self._channel_thickness

            if isinstance(self.shape, Rectangle):
                self._cap_specs = {"NE": {"x_thicknesses": [ct, pt], "y_thicknesses": [ct, pt], "materials": [pm, pm, cm, pm]},
                                   "SE": {"x_thicknesses": [ct, pt], "y_thicknesses": [pt, ct], "materials": [cm, pm, pm, pm]},
                                   "SW": {"x_thicknesses": [pt, ct], "y_thicknesses": [pt, ct], "materials": [pm, cm, pm, pm]},
                                   "NW": {"x_thicknesses": [pt, ct], "y_thicknesses": [ct, pt], "materials": [pm, pm, pm, cm]}}
            else:
                self._cap_specs = {"NE": {"bounds": (  0., ccl,   0., ccl), "materials": [cm, pm, pm]},
                                   "SE": {"bounds": (  0., ccl, -ccl,  0.), "materials": [cm, pm, pm]},
                                   "SW": {"bounds": (-ccl,  0., -ccl,  0.), "materials": [cm, pm, pm]},
                                   "NW": {"bounds": (-ccl,  0.,   0., ccl), "materials": [cm, pm, pm]}}

            self._flat_specs = {"vertical":
                                    {"NE" : {"x_thicknesses": [ct, pt], "y_thicknesses": [hfl   ], "materials": [cm, pm]},
                                     "SE" : {"x_thicknesses": [ct, pt], "y_thicknesses": [hfl   ], "materials": [cm, pm]},
                                     "SW" : {"x_thicknesses": [pt, ct], "y_thicknesses": [hfl   ], "materials": [pm, cm]},
                                     "NW" : {"x_thicknesses": [pt, ct], "y_thicknesses": [hfl   ], "materials": [pm, cm]}},

                                "horizontal":
                                    {"NE" : {"x_thicknesses": [hfl   ], "y_thicknesses": [ct, pt], "materials": [pm, cm]},
                                     "SE" : {"x_thicknesses": [hfl   ], "y_thicknesses": [pt, ct], "materials": [cm, pm]},
                                     "SW" : {"x_thicknesses": [hfl   ], "y_thicknesses": [pt, ct], "materials": [cm, pm]},
                                     "NW" : {"x_thicknesses": [hfl   ], "y_thicknesses": [ct, pt], "materials": [pm, cm]}}}

        def __init__(self,
                     shape:             Shape_2D,
                     material:          Material,
                     name:              str = "fuel_channel",):
            super().__init__(name, shape, material)


        def build_mpact_pin(self,
                            orientation: Block.Channel.Orientation,
                            pin_type:    Block.Channel.PinType,
                            quadrant:    Block.Channel.Quadrant) -> mpactpy.Pin:
            assert self._mpact_build_specs, "MPACT Build Specifications not set"
            height                  = self.mpact_build_specs.height
            target_cell_thicknesses = self.mpact_build_specs.target_cell_thicknesses

            pin = None
            if pin_type == "cap":
                specs     = self._cap_specs[quadrant]
                materials = specs["materials"]
                if isinstance(self.shape, Rectangle):
                    pin = build_rec_pin(thicknesses             = {"X": specs["x_thicknesses"],
                                                                   "Y": specs["y_thicknesses"],
                                                                   "Z": [height]},
                                        materials               = materials,
                                        target_cell_thicknesses = {"X": target_cell_thicknesses["cartesian"],
                                                                   "Y": target_cell_thicknesses["cartesian"]})
                else:
                    pin = build_gcyl_pin(bounds                  = specs["bounds"],
                                         thicknesses             = {"R": [self._channel_thickness, self._prism_thickness],
                                                                    "Z": [height]},
                                         materials               = materials,
                                         target_cell_thicknesses = {"R": target_cell_thicknesses["radial"],
                                                                    "S": target_cell_thicknesses["azimuthal"]})
            else:
                specs     = self._flat_specs[orientation][quadrant]
                materials = specs["materials"]
                if self._has_flats:
                    pin = build_rec_pin(thicknesses             = {"X": specs['x_thicknesses'],
                                                                   "Y": specs['y_thicknesses'],
                                                                   "Z": [height]},
                                        materials               = materials,
                                        target_cell_thicknesses = {"X": target_cell_thicknesses["cartesian"],
                                                                   "Y": target_cell_thicknesses["cartesian"]})
            return pin


    class ControlChannel(Channel):
        """ A class for MSRE-like Block Control Channels

        These channels are centered on the centers of the neighboring adjacent block cells.
        Currently, only cricular control channels are supported.

        Parameters
        ----------
        shape : Shape_2D
            The shape of the channel.  This must be a Circle.
        mpact_build_specs : Block.Channel.MPACTBuildSpecs
            The specifications required to build an MPACT Pin.  The block pitch must be less than
            twice the channel radius; otherwise, the Control Channel will fall entirely outside
            the block. Additionally, because of how Control Channel pins are constructed, both the
            cap cell length and the flat length must be large enough to ensure that the Control
            Channel cut-out fits within the rectangular footprint defined by their product
            (cap cell length x flat length).

        Attributes
        ----------
        shape : Shape_2D
            The shape of the channel
        mpact_build_specs : Block.Channel.MPACTBuildSpecs
            The specifications required to build an MPACT Pin
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

        @property
        def mpact_build_specs(self) -> Block.Channel.MPACTBuildSpecs:
            return self._mpact_build_specs

        @mpact_build_specs.setter
        def mpact_build_specs(self, specs: Block.Channel.MPACTBuildSpecs) -> None:
            Block.Channel.mpact_build_specs.__set__(self, specs)

            half_block_pitch = specs.block_pitch * 0.5
            self._prism_thickness = specs.cap_cell_length - (self.shape.inner_radius - half_block_pitch)

            assert self.shape.outer_radius > half_block_pitch, \
                "Control rod channel is completely outside the block.  " + \
                f"control_rod_radius = {self.shape.outer_radius}, block_pitch = {specs.block_pitch}"

            channel_normal_clipping_limit  = half_block_pitch + specs.cap_cell_length
            assert self.shape.outer_radius <= channel_normal_clipping_limit, \
                "Control channel cut-out exceeds cut-out normal limit! " + \
                f"control_channel_radius = {self.shape.outer_radius}, " + \
                f"channel_normal_clipping_limit = {self.shape.channel_normal_clipping_limit}"

            channel_lateral_clipping_limit  = sqrt((half_block_pitch)**2 +
                                                   (specs.flat_length*0.5 + specs.cap_cell_length)**2)
            assert self.shape.outer_radius <= channel_lateral_clipping_limit, \
                "Control channel cut-out exceeds cut-out lateral limit! " + \
                f"control_channel_radius = {self.shape.outer_radius}, " + \
                f"channel_lateral_clipping_limit = {self.shape.channel_lateral_clipping_limit}"

            hbp = half_block_pitch
            hfl = specs.flat_length * 0.5
            ccl = specs.cap_cell_length

            self._cap_specs = {"horizontal" : {"NE": {"bounds": (     hfl,  hfl+ccl,      hbp, hbp+ccl)},
                                               "SE": {"bounds": (     hfl,  hfl+ccl, -hbp-ccl,    -hbp)},
                                               "SW": {"bounds": (-hfl-ccl,     -hfl, -hbp-ccl,    -hbp)},
                                               "NW": {"bounds": (-hfl-ccl,     -hfl,      hbp, hbp+ccl)}},

                               "vertical"   : {"NE": {"bounds": (     hbp, hbp+ccl,      hfl,  hfl+ccl)},
                                               "SE": {"bounds": (     hbp, hbp+ccl, -hfl-ccl,     -hfl)},
                                               "SW": {"bounds": (-hbp-ccl,    -hbp, -hfl-ccl,     -hfl)},
                                               "NW": {"bounds": (-hbp-ccl,    -hbp,      hfl,  hfl+ccl)}}}

            self._flat_specs = {"vertical":   {"NE" : {"bounds": (      hbp,  hbp+ccl,       0.,      hfl)},
                                               "SE" : {"bounds": (      hbp,  hbp+ccl,     -hfl,       0.)},
                                               "SW" : {"bounds": ( -hbp-ccl, -hbp,         -hfl,       0.)},
                                               "NW" : {"bounds": ( -hbp-ccl, -hbp,           0.,      hfl)}},

                                "horizontal": {"NE" : {"bounds": (       0.,  hfl,          hbp,  hbp+ccl)},
                                               "SE" : {"bounds": (       0.,  hfl,     -hbp-ccl,     -hbp)},
                                               "SW" : {"bounds": (     -hfl,   0.,     -hbp-ccl,     -hbp)},
                                               "NW" : {"bounds": (     -hfl,   0.,          hbp,  hbp+ccl)}}}

        def __init__(self,
                     shape:             Shape_2D,
                     material:          Material,
                     name:              str = "control_channel"):
            super().__init__(name, shape, material)

        def build_mpact_pin(self,
                            orientation: Block.Channel.Orientation,
                            pin_type:    Block.Channel.PinType,
                            quadrant:    Block.Channel.Quadrant) -> mpactpy.Pin:
            assert self._mpact_build_specs, "MPACT Build Specifications not set"
            bounds = self._cap_specs[orientation][quadrant]["bounds"] if pin_type == "cap" else \
                     self._flat_specs[orientation][quadrant]["bounds"]

            regions = [(self.shape.inner_radius, self._channel_material),
                       (self._prism_thickness,   self._prism_material  )]

            thicknesses = {"R": [thickness for thickness, _ in regions if thickness > 0.0],
                           "Z": [self.mpact_build_specs.height]}

            materials = [material for thickness, material in regions if thickness > 0.0] + [self._prism_material]

            target_cell_thicknesses = {"R": self.mpact_build_specs.target_cell_thicknesses["radial"],
                                       "S": self.mpact_build_specs.target_cell_thicknesses["azimuthal"]}

            pin = None if pin_type == "flat" and not(self._has_flats) else \
                  build_gcyl_pin(bounds, thicknesses, materials, target_cell_thicknesses)

            return pin


    @property
    def pitch(self) -> float:
        return self._pitch

    @pitch.setter
    def pitch(self, pitch: float) -> None:
        assert pitch > 0., f"pitch = {pitch}"
        self._pitch = pitch

    @property
    def mpact_build_specs(self) -> MPACTBuildSpecs:
        return self._mpact_build_specs

    @mpact_build_specs.setter
    def mpact_build_specs(self, specs: Optional[MPACTBuildSpecs]) -> None:
        self._mpact_build_specs = specs if specs else Block.MPACTBuildSpecs()

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
                    self.channels[i].distance_from_block_center = self.pitch


    def __init__(self,
                 pitch:             float,
                 prism_material:    Material,
                 name:              str = "msre_block",
                 channels:          Dict[List[Optional[Block.Channel]]] = {},
                 outer_material:    Material = None,
                 mpact_build_specs: Optional[MPACTBuildSpecs] = None):

        self.pitch = pitch
        self.mpact_build_specs = mpact_build_specs
        channels = [channels[face] if face in channels else None for face in ['N', 'S', 'E', 'W']]

        super().__init__(Square(length=pitch), prism_material, name, channels, outer_material)

    def make_mpact_core(self) -> mpactpy.Core:
        """ A method for creating an MPACTPy Core based on this geometry

        MPACT geometry construction currently only support fuel and control
        channels with equal shapes. This is due to how the pins and modules
        for MSRE blocks are currently built, which assumes all fuel / control channels
        have the same shape.
        """

        flat_length     = 0.
        cap_cell_length = self.pitch*0.25

        if self.has_fuel_channels:
            assert self.fuel_channels_have_equal_shapes
            shape = self.fuel_channels[0].shape
            flat_length     = shape.a if isinstance(shape, Stadium) else \
                              0.0     if isinstance(shape, Circle)  else \
                              shape.w - shape.h
            cap_cell_length = (self.pitch - flat_length) * 0.25

        if self.has_control_channels:
            assert self.control_channels_have_equal_shapes
            if not self.has_fuel_channels:
                cap_cell_length = self.control_channels[0].shape.outer_radius - self.pitch*0.5
                flat_length     = self.pitch - cap_cell_length*4.0

        prism_mpact_material = self.prism_material.mpact_material

        for channel in self.channels:
            if channel:
                channel.mpact_build_specs = Block.Channel.MPACTBuildSpecs(
                    target_cell_thicknesses = self.mpact_build_specs.target_cell_thicknesses,
                    height                  = self.mpact_build_specs.height,
                    block_pitch             = self.pitch,
                    cap_cell_length         = cap_cell_length,
                    flat_length             = flat_length,
                    prism_material          = prism_mpact_material
                )

        pins     = self._build_pins(cap_cell_length, flat_length, prism_mpact_material)
        lattice  = self._build_lattice(pins)
        assembly = mpactpy.Assembly([lattice])
        core     = mpactpy.Core([[assembly]])

        return core


    def _build_pins(self,
                    cap_cell_length: float,
                    flat_length:     float,
                    prism_material:  mpactpy.Material) -> Dict[str, mpactpy.Pin]:
        """ Helper method for building the MPACT Pins

        Parameters
        ----------
        cap_cell_length : float
            The cap cell length (cm) to use for MPACT Pin construction
        flat_length : float
            The flat length (cm) to use for MPACT Pin construction
        prism_material : mpactpy.Material
            The MPACT material of the prismatic block

        Returns
        -------
        Dict[str, mpactpy.Pin]
            The collection of built pins
        """

        has_flats = flat_length > 0.0

        ccl = cap_cell_length
        hfl = flat_length * 0.5
        pins = {'corner':     self._build_prism_pin(ccl, ccl, prism_material),
                'center':     self._build_prism_pin(hfl, hfl, prism_material) if has_flats else None,
                'H_spacer':   self._build_prism_pin(hfl, ccl, prism_material) if has_flats else None,
                'V_spacer':   self._build_prism_pin(ccl, hfl, prism_material) if has_flats else None}

        #                      orientation,  pin_type,   quadrant,      name
        channel_pin_specs = [[("horizontal",   "cap",      "SW",   "N_chan_W_cap" ),
                              ("horizontal",   "flat",     "SW",   "N_chan_W_flat"),
                              ("horizontal",   "flat",     "SE",   "N_chan_E_flat"),
                              ("horizontal",   "cap",      "SE",   "N_chan_E_cap" )],

                             [("horizontal",   "cap",      "NW",   "S_chan_W_cap" ),
                              ("horizontal",   "flat",     "NW",   "S_chan_W_flat"),
                              ("horizontal",   "flat",     "NE",   "S_chan_E_flat"),
                              ("horizontal",   "cap",      "NE",   "S_chan_E_cap" )],

                             [("vertical",     "cap",      "NW",   "E_chan_N_cap" ),
                              ("vertical",     "flat",     "NW",   "E_chan_N_flat"),
                              ("vertical",     "flat",     "SW",   "E_chan_S_flat"),
                              ("vertical",     "cap",      "SW",   "E_chan_S_cap" )],

                             [("vertical",     "cap",      "NE",   "W_chan_N_cap" ),
                              ("vertical",     "flat",     "NE",   "W_chan_N_flat"),
                              ("vertical",     "flat",     "SE",   "W_chan_S_flat"),
                              ("vertical",     "cap",      "SE",   "W_chan_S_cap" )]]

        for i, channel in enumerate(self.channels):
            specs = channel_pin_specs[i]
            for orientation, pin_type, quadrant, name in specs:
                if channel:
                    pins[name] = channel.build_mpact_pin(orientation, pin_type, quadrant)
                else:
                    pins[name] = pins["corner"]   if pin_type    == "cap" else \
                                 pins["H_spacer"] if orientation == "horizontal" else \
                                 pins["V_spacer"]
        return pins


    def _build_prism_pin(self, w: float, h: float, prism_material:  mpactpy.Material) -> mpactpy.Pin:
        """ Helper method for building the prism pins of the block

        Parameters
        ----------
        w : float
            Pin cell width (cm)
        h : float
            Pin cell height (cm)
        prism_material : mpactpy.Material
            The MPACT material of the prismatic block

        Returns
        -------
          The built pin
        """

        return build_rec_pin(thicknesses             = {"X": [w], "Y": [h], "Z": [self.mpact_build_specs.height]},
                             materials               = [prism_material],
                             target_cell_thicknesses = {"X": self.mpact_build_specs.target_cell_thicknesses["cartesian"],
                                                        "Y": self.mpact_build_specs.target_cell_thicknesses["cartesian"]})


    def _build_lattice(self, pins: Dict[str, mpactpy.Pin]) -> mpactpy.Lattice:
        """ Helper method for building the MPACT Lattice

        Parameters
        ----------
        pins : Dict[str, mpactpy.Pin]
            The collection of pins with which to build the lattice

        Returns
        -------
        mpactpy.Lattice
            The built MPACT Lattice
        """

        quadrants = {
            'NW': [('corner'       , 'N_chan_W_cap', 'N_chan_W_flat'),
                   ('W_chan_N_cap' , 'corner'      , 'H_spacer'     ),
                   ('W_chan_N_flat', 'V_spacer'    , 'center'       )],

            'SW': [('W_chan_S_flat', 'V_spacer'    , 'center'       ),
                   ('W_chan_S_cap' , 'corner'      , 'H_spacer'     ),
                   ('corner'       , 'S_chan_W_cap', 'S_chan_W_flat')],

            'NE': [('N_chan_E_flat', 'N_chan_E_cap', 'corner'       ),
                   ('H_spacer'     , 'corner'      , 'E_chan_N_cap' ),
                   ('center'       , 'V_spacer'    , 'E_chan_N_flat')],

            'SE': [('center'       , 'V_spacer'    , 'E_chan_S_flat'),
                   ('H_spacer'     , 'corner'      , 'E_chan_S_cap' ),
                   ('S_chan_E_flat', 'S_chan_E_cap', 'corner'       )],
        }

        quadrants = {name: remove_none_2D([[pins[p] for p in row] for row in layout])
                     for name, layout in quadrants.items()}

        if self.mpact_build_specs.divide_into_quadrants:
            modules = {name: mpactpy.Module(1, quadrant) for name, quadrant in quadrants.items()}
            return mpactpy.Lattice([[modules['NW'], modules['NE']],
                                    [modules['SW'], modules['SE']]])

        top    = [nw_row + ne_row for nw_row, ne_row in zip(quadrants['NW'], quadrants['NE'])]
        bottom = [sw_row + se_row for sw_row, se_row in zip(quadrants['SW'], quadrants['SE'])]
        full_map = top + bottom

        module = mpactpy.Module(1, full_map)
        return mpactpy.Lattice([[module]])

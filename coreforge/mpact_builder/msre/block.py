from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, TypedDict, Optional, Literal, List
from dataclasses import dataclass
from math import inf, sqrt

import mpactpy
from mpactpy.pin import build_rec_pin, build_gcyl_pin

from coreforge.shapes import Rectangle, Stadium, Circle
from coreforge.mpact_builder.mpact_builder import register_builder, build_material
from coreforge.mpact_builder.builder_specs import BuilderSpecs
from coreforge.mpact_builder.material_specs import MaterialSpecs
import coreforge.geometry_elements.msre as geometry_elements_msre
from coreforge.utils import remove_none_2D

@register_builder(geometry_elements_msre.Block)
class Block:
    """ An MPACT geometry builder class for Block

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
        """ Building specifications for Block

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
        material_specs : MaterialSpecs
            Specifications for how materials should be treated in MPACT
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
        material_specs:          Optional[MaterialSpecs] = None

        def __post_init__(self):
            if not self.target_cell_thicknesses:
                self.target_cell_thicknesses = {'cartesian': inf, 'radial': inf, 'azimuthal': inf}

            assert all(thickness > 0. for thickness in self.target_cell_thicknesses.values()), \
                f"target_cell_thicknesses = {self.target_cell_thicknesses}"

            assert self.height > 0., f"height = {self.height}"

            if not self.material_specs:
                self.material_specs = MaterialSpecs()


    class Channel(ABC):
        """ An MPACT geometry builder class for Channels

        Parameters
        ----------
        specs: Optional[Specs]
            Specifications for building the MPACT representation of the channel

        Attributes
        ----------
        specs: Optional[Specs]
            Specifications for building the MPACT representation of the channel
        """

        Orientation = Literal["horizontal", "vertical"]
        PinType     = Literal["cap", "flat"]
        Quadrant    = Literal["NW", "NE", "SW", "SE"]

        @dataclass
        class Specs(BuilderSpecs):
            """ A dataclass for holding MPACT Channel Pin building specifications

            When constructing MPACT Pins for channels, geometric specifications are
            expressed in terms of Stadium features such as 'flats' and 'caps' given that
            Stadium channels are the primary application. Circular and Rectangular fuel
            channels are treated as varients of Stadium channels, wherein Rectangle channels
            are simply Stadiums with square caps, and Circle channels are Stadiums with no flats.

            The 'flats' and 'caps' terminology is also used with Control Channels given that
            the limitations of the MPACT geometry construction requires Control Channels to
            adhere to certain geometric constraints based on the 'flats' and 'caps' of the fuel channels.

            When building Control Channels The block pitch must be less than twice the channel radius;
            otherwise, the Control Channel will fall entirely outside the block. Additionally, because
            of how Control Channel pins are constructed, both the cap cell length and the flat length
            must be large enough to ensure that the Control Channel cut-out fits within the rectangular
            footprint defined by their product (cap cell length x flat length).

            Attributes
            ----------
            target_cell_thicknesses : Block.ThicknessSpec
                The target thickness of the cells in terms of lateral 'cartesian' length,
                'radial' thickness, and 'azimuthal' arc length (cm).
                Cells will be subdivided to limit cells to within these specifications.
            height : float
                The height to build the extruded Pin in the axial direction (cm).
                Default value is 1.0
            channel : geometry_elements_msre.Block.Channel,
                The channel to build pins for
            block_pitch : float
                The block pitch (cm) to use for MPACT Pin construction
            cap_cell_length : float
                The cap cell length (cm) to use for MPACT Pin construction
            flat_length : float
                The flat length (cm) to use for MPACT Pin construction
            prism_material : mpactpy.Material
                The MPACT material of the prismatic block
            material_specs : MaterialSpecs
                Specifications for how materials should be treated in MPACT
            """

            channel:                 geometry_elements_msre.Block.Channel
            block_pitch:             float
            cap_cell_length:         float
            flat_length:             float
            prism_material:          mpactpy.Material
            material_specs:          MaterialSpecs
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
        def specs(self) -> Specs:
            return self._specs

        @specs.setter
        def specs(self, specs: Specs) -> None:
            self._specs = specs

        def __init__(self, specs: Specs):
            self.specs = specs

        @abstractmethod
        def build_mpact_pin(self,
                            orientation: Orientation,
                            pin_type:    PinType,
                            quadrant:    Quadrant) -> mpactpy.Pin:
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
        """ An MPACT geometry builder class for Fuel Channels
        """

        @property
        def specs(self) -> Block.Channel.Specs:
            return self._specs

        @specs.setter
        def specs(self, specs: Block.Channel.Specs) -> None:
            super(Block.FuelChannel, type(self)).specs.fset(self, specs)

            channel                 = specs.channel
            self._channel_thickness = channel.shape.inner_radius
            self._prism_thickness   = specs.cap_cell_length - self._channel_thickness
            self._has_flats         = specs.flat_length > 0.0

            assert self._channel_thickness <= specs.cap_cell_length, \
                f"fuel_channel_thickness = {self._channel_thickness}, " + \
                f"cap_cell_length = {specs.cap_cell_length}"

            ccl = specs.cap_cell_length
            hfl = specs.flat_length * 0.5
            pm  = specs.prism_material
            cm  = build_material(specs.channel.material, specs.material_specs)
            pt  = self._prism_thickness
            ct  = self._channel_thickness

            if isinstance(channel.shape, Rectangle):
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


        def __init__(self, specs: Optional[Block.Channel.Specs] = None):
            super().__init__(specs)

        def build_mpact_pin(self,
                            orientation: Block.Channel.Orientation,
                            pin_type:    Block.Channel.PinType,
                            quadrant:    Block.Channel.Quadrant) -> mpactpy.Pin:

            height                  = self.specs.height
            target_cell_thicknesses = self.specs.target_cell_thicknesses

            pin = None
            if pin_type == "cap":
                specs     = self._cap_specs[quadrant]
                materials = specs["materials"]
                if isinstance(self.specs.channel.shape, Rectangle):
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
        """ An MPACT geometry builder class for Control Channels
        """

        @property
        def specs(self) -> Block.Channel.Specs:
            return self._specs

        @specs.setter
        def specs(self, specs: Block.Channel.Specs) -> None:
            super(Block.ControlChannel, type(self)).specs.fset(self, specs)

            channel               = specs.channel
            half_block_pitch      = specs.block_pitch * 0.5
            self._prism_thickness = specs.cap_cell_length - (channel.shape.inner_radius - half_block_pitch)
            self._has_flats       = specs.flat_length > 0.0

            self._channel_material = build_material(channel.material, specs.material_specs)
            self._prism_material   = specs.prism_material

            assert channel.shape.outer_radius > half_block_pitch, \
                "Control rod channel is completely outside the block.  " + \
                f"control_rod_radius = {channel.shape.outer_radius}, block_pitch = {specs.block_pitch}"

            channel_normal_clipping_limit  = half_block_pitch + specs.cap_cell_length
            assert channel.shape.outer_radius <= channel_normal_clipping_limit, \
                "Control channel cut-out exceeds cut-out normal limit! " + \
                f"control_channel_radius = {channel.shape.outer_radius}, " + \
                f"channel_normal_clipping_limit = {channel_normal_clipping_limit}"

            channel_lateral_clipping_limit  = sqrt((half_block_pitch)**2 +
                                                   (specs.flat_length*0.5 + specs.cap_cell_length)**2)
            assert channel.shape.outer_radius <= channel_lateral_clipping_limit, \
                "Control channel cut-out exceeds cut-out lateral limit! " + \
                f"control_channel_radius = {channel.shape.outer_radius}, " + \
                f"channel_lateral_clipping_limit = {channel_lateral_clipping_limit}"

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



        def __init__(self, specs: Optional[Block.Channel.Specs] = None):
            super().__init__(specs)

        def build_mpact_pin(self,
                            orientation: Block.Channel.Orientation,
                            pin_type:    Block.Channel.PinType,
                            quadrant:    Block.Channel.Quadrant) -> mpactpy.Pin:

            channel = self.specs.channel

            bounds  = self._cap_specs[orientation][quadrant]["bounds"] if pin_type == "cap" else \
                      self._flat_specs[orientation][quadrant]["bounds"]

            regions = [(channel.shape.inner_radius, self._channel_material),
                       (self._prism_thickness,      self._prism_material  )]

            thicknesses = {"R": [thickness for thickness, _ in regions if thickness > 0.0],
                           "Z": [self.specs.height]}

            materials = [material for thickness, material in regions if thickness > 0.0] + [self._prism_material]

            target_cell_thicknesses = {"R": self.specs.target_cell_thicknesses["radial"],
                                       "S": self.specs.target_cell_thicknesses["azimuthal"]}

            pin = None if pin_type == "flat" and not(self._has_flats) else \
                  build_gcyl_pin(bounds, thicknesses, materials, target_cell_thicknesses)

            return pin


    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, specs: Optional[Specs]) -> None:
        self._specs = specs


    def __init__(self, specs: Optional[Specs] = None):
        self.specs = specs


    def build(self, element: geometry_elements_msre.Block) -> mpactpy.Core:
        """ Method for building an MPACT geometry of an MSRE Block

        MPACT geometry construction currently only support fuel and control
        channels with equal shapes. This is due to how the pins and modules
        for MSRE blocks are currently built, which assumes all fuel / control channels
        have the same shape.

        Parameters
        ----------
        element: geometry_elements_msre.Block
            The geometry element to be built

        Returns
        -------
        mpactpy.Core
            A new MPACT geometry based on this geometry element
        """

        specs = self.specs if self.specs else Block.Specs()

        flat_length     = 0.
        cap_cell_length = element.pitch*0.25

        if element.has_fuel_channels:
            assert element.fuel_channels_have_equal_shapes
            shape = element.fuel_channels[0].shape
            flat_length     = shape.a if isinstance(shape, Stadium) else \
                              0.0     if isinstance(shape, Circle)  else \
                              shape.w - shape.h
            cap_cell_length = (element.pitch - flat_length) * 0.25

        if element.has_control_channels:
            assert element.control_channels_have_equal_shapes
            if not element.has_fuel_channels:
                cap_cell_length = element.control_channels[0].shape.outer_radius - element.pitch*0.5
                flat_length     = element.pitch - cap_cell_length*4.0

        prism_mpact_material = build_material(element.prism_material, specs.material_specs)

        channel_builders: List[Optional[Block.Channel]] = []
        for channel in element.channels:
            channel_builder = None
            if channel:
                ChannelBuilder = Block.FuelChannel if isinstance(channel, geometry_elements_msre.Block.FuelChannel) else \
                                 Block.ControlChannel
                channel_specs = Block.Channel.Specs(channel                 = channel,
                                                    target_cell_thicknesses = specs.target_cell_thicknesses,
                                                    height                  = specs.height,
                                                    block_pitch             = element.pitch,
                                                    cap_cell_length         = cap_cell_length,
                                                    flat_length             = flat_length,
                                                    prism_material          = prism_mpact_material,
                                                    material_specs          = specs.material_specs)
                channel_builder = ChannelBuilder(channel_specs)
            channel_builders.append(channel_builder)

        pins     = self._build_pins(channel_builders, cap_cell_length, flat_length, prism_mpact_material)
        lattice  = self._build_lattice(pins)
        assembly = mpactpy.Assembly([lattice])
        core     = mpactpy.Core([[assembly]])

        return core


    def _build_pins(self,
                    channel_builders: List[Optional[Block.Channel]],
                    cap_cell_length: float,
                    flat_length:     float,
                    prism_material:  mpactpy.Material) -> Dict[str, mpactpy.Pin]:
        """ Helper method for building the MPACT Pins

        Parameters
        ----------
        channel_builders : List[Optional[Block.Channel]]
            The builders for building channel pins
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

        for i, channel_builder in enumerate(channel_builders):
            for orientation, pin_type, quadrant, name in channel_pin_specs[i]:
                if channel_builder:
                    pins[name] = channel_builder.build_mpact_pin(orientation, pin_type, quadrant)
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

        specs = self.specs if self.specs else Block.Specs()
        return build_rec_pin(thicknesses             = {"X": [w], "Y": [h], "Z": [specs.height]},
                             materials               = [prism_material],
                             target_cell_thicknesses = {"X": specs.target_cell_thicknesses["cartesian"],
                                                        "Y": specs.target_cell_thicknesses["cartesian"]})


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

        specs = self.specs if self.specs else Block.Specs()
        if specs.divide_into_quadrants:
            modules = {name: mpactpy.Module(1, quadrant) for name, quadrant in quadrants.items()}
            return mpactpy.Lattice([[modules['NW'], modules['NE']],
                                    [modules['SW'], modules['SE']]])

        top    = [nw_row + ne_row for nw_row, ne_row in zip(quadrants['NW'], quadrants['NE'])]
        bottom = [sw_row + se_row for sw_row, se_row in zip(quadrants['SW'], quadrants['SE'])]
        full_map = top + bottom

        module = mpactpy.Module(1, full_map)
        return mpactpy.Lattice([[module]])

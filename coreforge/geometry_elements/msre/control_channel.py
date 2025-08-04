from __future__ import annotations
from typing import List, Any
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.stack import Stack
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.materials import Material

class ControlChannel(GeometryElement):
    """ A class for MSRE-like Control Channels

    Parameters
    ----------
    length : float
        The length of the control channel
    fill_material : Material
        The fill material of the control channel
    thimble : Thimble
        The control rod thimble that occupies the control channel
    control_rod : ControlRod
        The control rod that occupies the control channel thimble

    Attributes
    ----------
    length : float
        The length of the control channel
    fill_material : Material
        The fill material of the control channel
    thimble : Thimble
        The control rod thimble that occupies the control channel
    control_rod : ControlRod
        The control rod that occupies the control channel thimble
    """

    class Thimble():
        """ A class for MSRE-like Control Channel Thimble

        Parameters
        ----------
        outer_radius : float
            The outer radius of the thimble (cm)
        thickness : float
            The thickness of the thimble wall tubing (cm)
        length : float
            The length of the thimbles extending from the top of the control channel
        wall_material : Material
            The wall material of the thimble
        fill_material : Material
            The fill material of the thimble


        Attributes
        ----------
        inner_radius : float
            The inner radius of the thimble (cm)
        outer_radius : float
            The outer radius of the thimble (cm)
        thickness : float
            The thickness of the thimble wall tubing (cm)
        length : float
            The length of the thimbles extending from the top of the control channel
        wall_material : Material
            The wall material of the thimble
        fill_material : Material
            The fill material of the thimble
        """

        @property
        def inner_radius(self) -> float:
            return self._inner_radius

        @property
        def outer_radius(self) -> float:
            return self._outer_radius

        @property
        def thickness(self) -> float:
            return self._thickness

        @property
        def length(self) -> float:
            return self._length

        @property
        def wall_material(self) -> Material:
            return self._wall_material

        @property
        def fill_material(self) -> Material:
            return self._fill_material


        def __init__(self,
                     outer_radius:  float,
                     thickness:     float,
                     length:        float,
                     wall_material: Material,
                     fill_material: Material):

            assert outer_radius > 0.0, f"outer_radius = {outer_radius}"
            assert thickness > 0.0, f"thickness = {thickness}"
            assert thickness < outer_radius, f"outer_radius = {outer_radius}, thickness = {thickness}"
            assert length > 0.0, f"length = {length}"

            self._inner_radius  = outer_radius - thickness
            self._outer_radius  = outer_radius
            self._thickness     = thickness
            self._length        = length
            self._wall_material = wall_material
            self._fill_material = fill_material


        def __eq__(self, other: Any) -> bool:
            if self is other:
                return True
            return (isinstance(other, ControlChannel.Thimble) and
                    isclose(self.outer_radius, other.outer_radius) and
                    isclose(self.thickness, other.thickness) and
                    isclose(self.length, other.length) and
                    self.wall_material == other.wall_material and
                    self.fill_material == other.fill_material
                   )

        def __hash__(self) -> int:
            return hash((relative_round(self.outer_radius, TOL),
                         relative_round(self.thickness, TOL),
                         relative_round(self.length, TOL),
                         self.wall_material,
                         self.fill_material))

    class ControlRod():
        """ A class for MSRE-like Control Channel Control Rod

        Parameters
        ----------
        radii : List[float]
            The radii of the control rod material regions (cm)
            Must be listed from inner most to outer most.
        materials : List[Material]
            The material regions of the control rod.
            Must be listed from inner most to outer most.
        insertion_fraction : float
            The amount the control rod is inserted into the thimble with respect to fractional
            length of the thimble
            Default: 0.0


        Attributes
        ----------
        radii : List[float]
            The radii of the control rod material regions (cm).  Listed from inner most to outer most.
        materials : List[Material]
            The material regions of the control rod. Listed from inner most to outer most.
        insertion_fraction : float
            The amount the control rod is inserted into the thimble with respect to fractional
            length of the thimble
        """

        @property
        def radii(self) -> List[float]:
            return self._radii

        @property
        def materials(self) -> List[Material]:
            return self._materials

        @property
        def insertion_fraction(self) -> float:
            return self._insertion_fraction

        @insertion_fraction.setter
        def insertion_fraction(self, insertion_fraction: float) -> None:
            assert 0.0 <= insertion_fraction <= 1.0, f"insertion_fraction = {insertion_fraction}"
            self._insertion_fraction = insertion_fraction

        def __init__(self,
                     radii:              List[float],
                     materials:          List[Material],
                     insertion_fraction: float = 0.0):

            assert len(radii) == len(materials), \
                f"len(radii) = {len(radii)}, len(materials) = {len(materials)}"
            assert all(r > 0.0 for r in radii), f"radii = {radii}"
            assert all(r_i < r_o for r_i, r_o in zip(radii, radii[1:])), f"radii = {radii}"


            self._radii             = radii
            self._materials         = materials
            self.insertion_fraction = insertion_fraction


        def __eq__(self, other: Any) -> bool:
            if self is other:
                return True
            return (isinstance(other, ControlChannel.ControlRod) and
                    len(self.radii) == len(other.radii)          and
                    isclose(self.insertion_fraction, other.insertion_fraction) and
                    all(isclose(self.radii[i], other.radii[i]) for i in range(len(self.radii))) and
                    all(self.materials[i] == other.materials[i] for i in range(len(self.materials)))
                   )

        def __hash__(self) -> int:
            return hash((tuple(self.radii),
                         tuple(self.materials),
                         relative_round(self.insertion_fraction, TOL)))

    @property
    def length(self) -> float:
        return self._length

    @property
    def fill_material(self) -> Material:
        return self._fill_material

    @property
    def thimble(self) -> Thimble:
        return self._thimble

    @property
    def control_rod(self) -> ControlRod:
        return self._control_rod

    def __init__(self,
                 thimble:       Thimble,
                 control_rod:   ControlRod,
                 length:        float,
                 fill_material: Material,
                 name:          str = 'control_channel'):

        assert length > 0., f"length = {length}"
        assert length >= thimble.length, \
            f"length = {length}, thimble.length = {thimble.length}"
        assert control_rod.radii[-1] < thimble.inner_radius, \
            f"control_rod.radii[-1] = {control_rod.radii[-1]}, " + \
            f"thimble.inner_radius = {thimble.inner_radius}"

        self._thimble       = thimble
        self._control_rod   = control_rod
        self._length        = length
        self._fill_material = fill_material
        super().__init__(name)

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, ControlChannel)     and
                self.thimble == other.thimble         and
                self.control_rod == other.control_rod and
                isclose(self.length, other.length)
               )

    def __hash__(self) -> int:
        return hash((self.thimble,
                     self.control_rod,
                     relative_round(self.length, TOL)))

    def as_stack(self, bottom_pos: float = 0.0) -> Stack:
        """ A method for getting a copy of the ControlChannel as a Stack

        Parameters
        ----------
        bottom_pos : float
            The axial position of the bottom of the stack (cm)

        Returns
        -------
        Stack
            The ControlChannel as a Stack
        """


        channel     = self
        thimble     = channel.thimble
        control_rod = channel.control_rod

        thimble_radii           = [thimble.inner_radius,  thimble.outer_radius]

        empty_channel_materials = [channel.fill_material,
                                   channel.fill_material,
                                   channel.fill_material]

        thimble_materials       = [thimble.fill_material,
                                   thimble.wall_material,
                                   channel.fill_material]

        empty_section       = CylindricalPinCell(radii     = thimble_radii,
                                                 materials = empty_channel_materials)
        thimble_section     = CylindricalPinCell(radii     = thimble_radii,
                                                 materials = thimble_materials)
        control_rod_section = CylindricalPinCell(radii     = control_rod.radii + thimble_radii,
                                                 materials = control_rod.materials + thimble_materials)

        thimble_tip_position = channel.length - thimble.length
        control_rod_length   = thimble.length * control_rod.insertion_fraction
        empty_thimble_length = thimble.length - control_rod_length

        segments = []
        if thimble_tip_position > 0.0:
            segments.append(Stack.Segment(empty_section, thimble_tip_position))
        if empty_thimble_length > 0.0:
            segments.append(Stack.Segment(thimble_section, empty_thimble_length))
        if control_rod_length > 0.0:
            segments.append(Stack.Segment(control_rod_section, control_rod_length))

        return Stack(segments   = segments,
                     name       = channel.name,
                     bottom_pos = bottom_pos)
